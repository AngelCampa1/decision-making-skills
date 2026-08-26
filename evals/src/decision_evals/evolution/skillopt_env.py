"""The second engine, wired to the same scored environment as the first.

SkillOpt takes an environment rather than an adapter: a subclass of its
``EnvAdapter`` supplying ``build_train_env``, ``build_eval_env``, ``rollout`` and
``get_task_types``, and a YAML config naming the models. Its reflection step is
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

from collections.abc import Sequence
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


class SkillOptError(RuntimeError):
    """SkillOpt cannot be reached, or cannot be pointed at this venue."""


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
            """A slice of the validation pool, whatever ``split`` is called.

            SkillOpt names its splits and this environment has two pools. A
            ``split`` naming neither is an error rather than a default: silently
            evaluating on training items is how an acceptance gate stops being
            one.
            """
            if split not in {"val", "validation", "eval", "test"}:
                raise SkillOptError(
                    f"split {split!r} names no pool here. The pools are `train` and "
                    "`validation`; anything else would have to fall back to one of them, "
                    "and falling back to training is an acceptance gate that accepts."
                )
            return Batch(validation[:env_num] if env_num else validation, "validation")

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
            """
            traces = core.score(skill_content, env_manager.items)
            return [
                {
                    "id": trace.item_id,
                    "hard": int(trace.correct),
                    "soft": trace.score,
                    "task_type": TASK_TYPES[0],
                    "seed": trace.seed,
                    "prompt": trace.rendered,
                    "response": trace.response,
                    "expected": trace.expected,
                    "parsed": trace.parsed,
                    "zero_cause": trace.zero_cause,
                }
                for trace in traces
            ]

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


def _deployment(model: str) -> str:
    """The model name a server knows, with this repository's venue prefix off.

    ``ollama/qwen3:4b`` is how a record names it, because the prefix is what the
    arena registry and the concurrency register key on. The server was never
    told about the prefix.
    """
    label, _, rest = model.partition("/")
    return rest if rest and label in {"ollama", "nvbuild", "mockllm"} else model
