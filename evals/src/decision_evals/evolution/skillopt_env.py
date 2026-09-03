"""The second engine, wired to the same scored environment as the first.

SkillOpt takes an environment rather than an adapter: a subclass of its
``EnvAdapter`` supplying ``build_train_env``, ``build_eval_env``, ``rollout`` and
``get_task_types``, and a flat config naming the models. Its own loader reads
that config from YAML; :func:`train_config` builds the same dictionary directly,
so there is no second file claiming to be the settings. Its reflection step is
inherited and runs against SkillOpt's own model layer, which is the difference
that matters — GEPA takes a ``reflection_lm`` callable and SkillOpt reads a
config.

**The class is built inside a function on purpose.** ``skillopt`` lives in the
``evolve`` dependency group, which ``de check`` never installs, so a module-level
``class DecisionEnv(EnvAdapter)`` would make the engine under study an
import-time dependency of the instrument measuring it. :func:`build_env` imports
it at call time and says something useful when it is missing.

**Both engines score through the same object.** :meth:`DecisionAdapter.score
<decision_evals.evolution.adapter.DecisionAdapter.score>` is what ``rollout``
calls, so the seed firewall, the budget, the resume key and the lineage are the
same code for both. A study comparing two engines under one protocol has to mean
one protocol; two integrations that each did their own bookkeeping would be
comparing the integrations.

**The venue reaches SkillOpt as configuration, not as a patch.** Its backend
router knows ``azure_openai``, ``codex`` and ``claude`` and nothing else, and the
first of those takes an ``auth_mode`` of ``openai_compatible`` that builds a
plain OpenAI client against any ``base_url``. So Ollama and NVIDIA Build are
reachable without touching the engine — which matters more than convenience,
because a patched engine is no longer the engine the result is about.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Final

from decision_evals.evolution.adapter import DecisionAdapter
from decision_evals.evolution.venues import Venue
from decision_evals.generators.generate import Item

#: What SkillOpt calls a task type. One, because every item in this corpus is
#: the same task under different strata, and inventing several would make its
#: per-type reporting look like a breakdown of something.
TASK_TYPES: Final[tuple[str, ...]] = ("decision",)

#: SkillOpt's auth mode for a plain OpenAI-compatible endpoint. Its own name for
#: it, in its own backend, so nothing here is a patch.
COMPAT_AUTH: Final = "openai_compatible"

#: The split names the trainer uses for its acceptance gate. ``valid_seen`` is
#: what it actually asks for; the rest are accepted because they mean the same
#: thing and a rename upstream should not be a crash.
SELECTION: Final[frozenset[str]] = frozenset(
    {"valid_seen", "val", "valid", "validation", "eval", "select"}
)

#: The split names meaning "held out", every one of which is refused. See
#: ``DecisionEnv.build_eval_env`` for why serving these would be worse than
#: failing.
HELD_OUT: Final[frozenset[str]] = frozenset({"valid_unseen", "test", "holdout", "unseen"})

#: The four settings ``EnvAdapter.reflect`` reads off ``self``. It is the
#: inherited reflection step -- no shipped environment overrides it -- and it
#: reads four attributes the abstract base never declares and never sets. Every
#: built-in adapter and the ``_template`` set them in ``__init__``, so the
#: contract is real and carried entirely by the example rather than by the
#: class. :meth:`DecisionEnv.setup` mirrors them off the config instead, because
#: the trainer hands ``setup`` the same dictionary it reads its own copies from
#: and two sources for one number is how they come to disagree.
REFLECT_SETTINGS: Final[tuple[str, ...]] = (
    "analyst_workers",
    "failure_only",
    "minibatch_size",
    "edit_budget",
)


class SkillOptError(RuntimeError):
    """SkillOpt cannot be reached, or cannot be pointed at this venue."""


def _why(trace: Any) -> str:
    """One line naming why an item was wrong, for the analyst's prompt header.

    The distinctions are the scorer's own, because they call for different
    edits: an answer in the wrong shape wants a format instruction and a
    confidently wrong answer wants better reasoning, and a reflector that cannot
    tell them apart will rewrite the wrong half of a skill.
    """
    if trace.zero_cause == "infrastructure":
        return "the call did not complete, so this item says nothing about the skill"
    if trace.zero_cause == "output_truncated":
        return (
            "the reply spent its whole output budget reasoning and never reached an "
            f"answer line; the format is not what failed, and {trace.expected!r} was correct"
        )
    if trace.parsed is None:
        return (
            f"no answer could be read from the reply ({trace.parse_status}); "
            f"expected {trace.expected!r}"
        )
    return f"answered {trace.parsed!r} where the correct option was {trace.expected!r}"


def _write_transcript(directory: Path, trace: Any) -> None:
    """Write one item's exchange where the reflection step looks for it.

    Three turns, which is what this corpus is: the rendered problem, the reply,
    and the scorer's verdict. The verdict goes in as ``role: system``, which is
    how the engine's own environments hand grading back to the analyst and how
    its formatter renders one.
    """
    directory.mkdir(parents=True, exist_ok=True)
    verdict = (
        "[EVALUATION RESULT]\n"
        f"Answer read from the reply: {trace.parsed!r}\n"
        f"Correct option: {trace.expected!r}\n"
        f"Parse status: {trace.parse_status}\n"
        f"Scored: {'correct' if trace.correct else 'incorrect'}"
    )
    conversation = [
        {"role": "user", "content": trace.rendered},
        {"role": "assistant", "content": trace.response},
        {"role": "system", "content": verdict},
    ]
    (directory / "conversation.json").write_text(
        json.dumps(conversation, ensure_ascii=False, indent=2), encoding="utf-8", newline=""
    )


class Batch:
    """What ``build_train_env`` hands to ``rollout``.

    SkillOpt calls this an environment manager and never looks inside one, so it
    is a list of items with a name on it. Named rather than anonymous because
    the name reaches the run directory and a rollout over the wrong split is the
    failure this study is built to prevent.
    """

    def __init__(self, items: Sequence[Item], split: str) -> None:
        self.items = list(items)
        self.split = split

    def __len__(self) -> int:
        return len(self.items)


def build_env(
    core: DecisionAdapter,
    *,
    train: Sequence[Item],
    validation: Sequence[Item],
) -> Any:
    """A SkillOpt ``EnvAdapter`` over this repository's corpus.

    Args:
        core: The scored environment. Its ``score`` method is what ``rollout``
            calls, so both engines share one set of books.
        train: What SkillOpt mutates against.
        validation: What its acceptance gate reads. Held separate here rather
            than sampled from one pool, because an acceptance gate reading the
            items a proposal was written against accepts everything.

    Raises:
        SkillOptError: SkillOpt is not installed.
    """
    try:
        from skillopt.envs.base import EnvAdapter
    except ImportError as exc:  # pragma: no cover - exercised by the import guard test
        raise SkillOptError(
            "skillopt is not installed. It is in the `evolve` dependency group, which "
            "the gate deliberately does not install: run "
            "`python -m uv sync --group evolve`."
        ) from exc

    class DecisionEnv(EnvAdapter):  # type: ignore[misc]
        """This corpus, in the shape SkillOpt's trainer expects."""

        def setup(self, cfg: dict[str, Any]) -> None:
            """Mirror the reflection settings off the config, before any step runs.

            The trainer calls this once with the flat config, then eleven
            hundred lines later the inherited ``reflect`` reads
            ``REFLECT_SETTINGS`` off ``self``. Nothing in the abstract base sets
            them, so an adapter that implements every abstract method and no
            more raises ``AttributeError`` at the first reflection -- after a
            baseline pass and a training rollout have already been spent. This
            run hit exactly that.

            Reading them from ``cfg`` rather than from constructor arguments is
            the point. The trainer reads its own copies out of the same
            dictionary, so there is no arrangement in which the env reflects on
            a budget the trainer is not using.

            Raises:
                SkillOptError: A config missing one of them, which
                    :func:`train_config` cannot produce.
            """
            super().setup(cfg)
            for name in REFLECT_SETTINGS:
                if name not in cfg:
                    raise SkillOptError(
                        f"the config has no {name!r}, and the inherited reflection step "
                        "reads it off the environment partway into the first step. "
                        "`train_config` supplies all of "
                        f"{list(REFLECT_SETTINGS)}; a config built some other way has to "
                        "as well."
                    )
                setattr(self, name, cfg[name])

        def build_train_env(self, batch_size: int, seed: int, **kwargs: Any) -> Batch:
            """A slice of the training pool.

            ``seed`` is SkillOpt's sampling seed and is deliberately *not* used
            to generate items. Corpus seeds are the split, and letting an engine
            choose one would put the firewall downstream of the thing it guards.
            Slicing is from the front rather than random, so a resumed run
            covers the items the first run covered.
            """
            return Batch(train[:batch_size] if batch_size else train, "train")

        def build_eval_env(self, env_num: int, split: str, seed: int, **kwargs: Any) -> Batch:
            """A slice of the validation pool, for the splits that mean one.

            SkillOpt's trainer asks for ALFWorld's split names, because that is
            the environment it was written against: ``valid_seen`` for the
            acceptance gate and ``valid_unseen`` for its final test. Those two
            names carry the whole distinction this study depends on, so they are
            mapped rather than accepted alike.

            ``SELECTION`` gets the validation pool. ``HELD_OUT`` gets a refusal:
            the holdout for this study is minted after the winners are frozen
            and no search may see it, so there is no pool here that could
            honestly answer. Serving validation items under a name meaning
            "test" would put a number in the trainer's own summary that reads
            like a held-out result and is not one.

            The refusal is a backstop rather than the control. ``eval_test`` is
            ``False`` in :func:`train_config`, so a run never asks; if one does,
            something changed and the run should stop rather than answer.
            """
            if split in SELECTION:
                return Batch(validation[:env_num] if env_num else validation, "validation")
            if split in HELD_OUT:
                raise SkillOptError(
                    f"split {split!r} is this trainer's held-out test split, and there is "
                    "nothing here to serve it. The study's holdout is minted after the "
                    "winners are frozen and no search may read it. Set `eval_test: false` "
                    "-- which `train_config` already does -- rather than pointing this at "
                    "the validation pool, because a validation number reported as a test "
                    "number is the failure the split exists to prevent."
                )
            raise SkillOptError(
                f"split {split!r} names no pool here. The pools are `train` and "
                f"`validation`; the selection splits are {sorted(SELECTION)}. Anything else "
                "would have to fall back to one of them, and falling back to training is an "
                "acceptance gate that accepts."
            )

        def rollout(
            self,
            env_manager: Batch,
            skill_content: str,
            out_dir: str,
            **kwargs: Any,
        ) -> list[dict[str, Any]]:
            """Score the current skill on this batch.

            ``hard`` is the correct/incorrect this corpus computes and ``soft``
            is the same number. They are not two measurements: the ground truth
            here is an option from a fixed menu, so there is no partial credit
            to report, and reporting a fabricated gradient between 0 and 1 would
            give SkillOpt's reflection a signal that is not in the data.

            **Writing the transcripts is not optional and the base class does
            not say so.** The reflection step reads each item's trajectory back
            off disk, from ``<out_dir>/predictions/<id>/conversation.json``, and
            when it finds nothing it returns ``None`` before calling the
            optimizer at all. That path is silent: the step prints an analyst
            line, reports zero edits, skips, and a whole search completes having
            proposed nothing while every log line looks ordinary. It did.
            """
            traces = core.score(skill_content, env_manager.items)
            predictions = Path(out_dir) / "predictions"
            results: list[dict[str, Any]] = []
            for trace in traces:
                _write_transcript(predictions / trace.item_id, trace)
                result: dict[str, Any] = {
                    "id": trace.item_id,
                    "hard": int(trace.correct),
                    "soft": trace.score,
                    "task_type": TASK_TYPES[0],
                    "task_description": trace.question,
                    "n_turns": 1,
                    "seed": trace.seed,
                    "prompt": trace.rendered,
                    "response": trace.response,
                    "expected": trace.expected,
                    "parsed": trace.parsed,
                    "zero_cause": trace.zero_cause,
                }
                if not trace.correct:
                    # Read straight into the analyst's prompt header. The cause
                    # matters more than the score: a reflector told only "0.0"
                    # rewrites reasoning guidance for a reply whose real problem
                    # was that it had no final line.
                    result["fail_reason"] = _why(trace)
                results.append(result)
            return results

        def get_task_types(self) -> list[str]:
            return list(TASK_TYPES)

    return DecisionEnv()


def venue_config(target: Venue, optimizer: Venue) -> dict[str, Any]:
    """The ``model`` section of a SkillOpt config pointing at these venues.

    Returned as a dict rather than written to YAML, so a caller can merge it
    into whichever base config it is running and there is no second file
    claiming to be the configuration.

    The key is ``auth_mode: openai_compatible``, which is SkillOpt's own path to
    a plain OpenAI client against an arbitrary ``base_url``. The Azure names
    around it are its names, not a repurposing: the same section carries the
    endpoint for every mode that backend supports.

    Raises:
        SkillOptError: A venue with no reachable endpoint. The mock venue has an
            empty ``base_url`` by construction, and a config pointing at nothing
            fails on the first call with a message about a URL rather than about
            a venue.
    """
    for role, venue in (("target", target), ("optimizer", optimizer)):
        if not venue.endpoint.base_url:
            raise SkillOptError(
                f"the {role} venue {venue.model!r} has no base URL, so SkillOpt has "
                "nowhere to send a call. The in-process mock venue answers inside this "
                "process and cannot be reached over HTTP; run SkillOpt against `ollama/` "
                "or `nvbuild/`."
            )
    return {
        "model": {
            "backend": "azure_openai",
            "target": _deployment(target.model),
            "optimizer": _deployment(optimizer.model),
            "target_azure_openai_endpoint": target.endpoint.base_url,
            "target_azure_openai_api_key": target.endpoint.api_key or "dummy",
            "target_azure_openai_auth_mode": COMPAT_AUTH,
            "optimizer_azure_openai_endpoint": optimizer.endpoint.base_url,
            "optimizer_azure_openai_api_key": optimizer.endpoint.api_key or "dummy",
            "optimizer_azure_openai_auth_mode": COMPAT_AUTH,
        }
    }


def train_config(
    *,
    target: Venue,
    optimizer: Venue,
    out_root: Path,
    skill_init: Path,
    batch_size: int,
    sel_env_num: int,
    train_size: int,
    num_epochs: int = 1,
    accumulation: int = 1,
    merge_batch_size: int = 1,
    edit_budget: int = 4,
    analyst_workers: int = 1,
    minibatch_size: int = 8,
    failure_only: bool = False,
    seed: int = 0,
) -> dict[str, Any]:
    """The flat config ``ReflACTTrainer`` reads, with every required key supplied.

    ``ReflACTTrainer`` takes a flat dictionary and reads fourteen keys with no
    default at all -- ``cfg["batch_size"]`` rather than ``cfg.get(...)`` -- so a
    missing one is a ``KeyError`` partway into a run that has already spent
    calls. They are all supplied here, and everything else is left to the
    engine's own defaults, which is the difference between configuring a run and
    inventing one.

    The arguments without defaults are the ones no default could be right for.
    The rest carry the smallest value that still exercises the mechanism, because
    the binding constraint on this study is wall-clock on a single local GPU and
    every one of them multiplies the call count.

    Three settings are not tuning and should not be changed to make a run finish:

    ``eval_test`` is ``False``. It is what stops the trainer asking for its
    held-out split, which this environment refuses to serve.

    ``analyst_workers`` is 1. The reflection analyst is the one place the trainer
    fans out, and on 2026-08-19 this repository measured a batching server
    changing **every** answer under concurrency -- 0 of 40 agreement, McNemar
    p < 0.0001 -- which is why ``runner.CONCURRENCY_UNSAFE`` registers the
    ``ollama`` prefix. That finding is about the venue rather than about the
    caller, so it applies to an optimizer served from the same place.

    ``target_model`` and ``target_backend`` are set because the trainer requires
    them, and they are **unused for scoring**: every scored call in this study
    goes through ``rollout`` and this repository's own runner, so the record, the
    budget and the resume key are the harness's. They matter only if some path
    inside the engine calls the target itself, and a config that named nothing
    would fail there rather than surfacing it.

    Raises:
        SkillOptError: A venue with no reachable endpoint, or a non-positive
            count where the engine would divide by it.
    """
    for name, value in (
        ("batch_size", batch_size),
        ("sel_env_num", sel_env_num),
        ("train_size", train_size),
        ("num_epochs", num_epochs),
        ("accumulation", accumulation),
        ("merge_batch_size", merge_batch_size),
        ("analyst_workers", analyst_workers),
    ):
        if value < 1:
            raise SkillOptError(
                f"{name} is {value}, and a search cannot run a non-positive number of "
                "anything. The engine divides by several of these."
            )
    if not skill_init.is_file():
        raise SkillOptError(
            f"{skill_init} is not a file, so the trainer has no skill to start from. It "
            "reads the seed body off disk rather than taking it as a string."
        )

    flat = _flatten(venue_config(target, optimizer))
    flat.update(
        {
            "out_root": str(out_root),
            "skill_init": str(skill_init),
            "env": TASK_TYPES[0],
            "batch_size": batch_size,
            "num_epochs": num_epochs,
            "accumulation": accumulation,
            "merge_batch_size": merge_batch_size,
            "edit_budget": edit_budget,
            "analyst_workers": analyst_workers,
            # Read by the inherited reflection step off the environment rather
            # than off the config. `DecisionEnv.setup` mirrors them across, and
            # they are named here so the config stays the one place a setting
            # is written down. `minibatch_size` and `failure_only` are the
            # engine's own defaults; the other two are not, and `train_config`'s
            # docstring says why.
            "minibatch_size": minibatch_size,
            "failure_only": failure_only,
            "seed": seed,
            "sel_env_num": sel_env_num,
            # Read as `cfg.get("train_size", 0)` and then, when that is zero,
            # inferred from a dataloader. This adapter has none by design -- the
            # corpus is generated, not loaded -- so the inference returns None
            # and the trainer raises. A `.get` with a fallback is still a
            # required key when the fallback cannot succeed.
            "train_size": train_size,
            # Read only inside `if cfg["eval_test"]:`, so this is never used.
            # Present because a KeyError from a branch nobody meant to take is a
            # worse failure than an unused zero.
            "test_env_num": 0,
            "eval_test": False,
        }
    )
    return flat


def _flatten(structured: dict[str, Any]) -> dict[str, Any]:
    """Flatten through SkillOpt's own mapping.

    Its ``_FLATTEN_MAP`` is 80-odd entries and it is the engine's business which
    structured key becomes which flat one. Re-typing that mapping here would
    make a version bump silently produce a config the trainer reads differently
    from the way it is written.

    Raises:
        SkillOptError: SkillOpt is not installed.
    """
    try:
        from skillopt.config import flatten_config
    except ImportError as exc:  # pragma: no cover - exercised by the import guard test
        raise SkillOptError(
            "skillopt is not installed. It is in the `evolve` dependency group, which "
            "the gate deliberately does not install: run "
            "`python -m uv sync --group evolve`."
        ) from exc
    return dict(flatten_config(structured))


def _deployment(model: str) -> str:
    """The model name a server knows, with this repository's venue prefix off.

    ``ollama/qwen3:4b`` is how a record names it, because the prefix is what the
    arena registry and the concurrency register key on. The server was never
    told about the prefix.
    """
    label, _, rest = model.partition("/")
    return rest if rest and label in {"ollama", "nvbuild", "mockllm"} else model
