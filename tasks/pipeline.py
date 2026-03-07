"""
Agentic Task Pipeline — built on emergent's graph + saga patterns.

This module demonstrates how emergent's compositional primitives map
to agentic task orchestration:

  graph nodes  → task units with typed dependencies (auto-parallelized)
  saga steps   → multi-step workflows with automatic rollback on failure
  cache tiers  → memoized task results (idempotent re-runs)

Key insight: an agentic pipeline IS a computation graph. Each node
is a capability; each edge is a data dependency. emergent resolves
the execution order automatically — you declare *what*, not *when*.

Example pipeline:
  UserIntent → [ResearchTask, ToolSelection] → Synthesis → Response
                     ↑ parallel ↑

Run:
  python -m tasks.pipeline
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from emergent import graph as G
from emergent import saga as S
from combinators import lift as L
from kungfu import Ok, Error


# ─────────────────────────────────────────────────────────────────────────────
# Domain: Agentic Task Types
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class UserIntent:
    """The raw user request — entry point for the pipeline."""
    query: str
    session_id: str


@dataclass(frozen=True)
class ResearchResult:
    """Output of the research sub-task."""
    facts: list[str]
    sources: list[str]


@dataclass(frozen=True)
class ToolCall:
    """A resolved tool invocation."""
    tool_name: str
    args: dict[str, str]
    result: str


@dataclass(frozen=True)
class SynthesisResult:
    """Final synthesized response."""
    response: str
    used_tools: list[str]
    confidence: float


@dataclass(frozen=True)
class TaskError(Exception):
    message: str
    recoverable: bool = True

    def __str__(self) -> str:
        return f"TaskError({'recoverable' if self.recoverable else 'fatal'}): {self.message}"


# ─────────────────────────────────────────────────────────────────────────────
# Graph Nodes — declarative dependency graph
#
# The framework resolves execution order from type dependencies.
# ResearchNode and ToolNode both depend on IntentNode → they run in PARALLEL.
# SynthesisNode depends on both → it runs after both complete.
#
# Topology:
#   IntentNode ──┬──► ResearchNode ──┐
#                └──► ToolNode    ──►├──► SynthesisNode
# ─────────────────────────────────────────────────────────────────────────────

@G.node
class IntentNode:
    """Entry node — holds the user intent, seeds the graph."""

    def __init__(self, intent: UserIntent) -> None:
        self.intent = intent

    @classmethod
    def __compose__(cls, intent: UserIntent) -> "IntentNode":
        # Synchronous — just wraps the input
        return cls(intent)


@G.node
class ResearchNode:
    """Simulate a research sub-task (web search, RAG, knowledge lookup)."""

    def __init__(self, result: ResearchResult) -> None:
        self.result = result

    @classmethod
    async def __compose__(cls, intent: IntentNode) -> "ResearchNode":
        # In production: call a real research API / vector DB
        print(f"  [research]  searching for: '{intent.intent.query}'")
        await asyncio.sleep(0.05)  # simulate async I/O
        return cls(ResearchResult(
            facts=[
                f"emergent uses nodnod for DAG-based dependency resolution",
                f"fold patterns enable streaming derivation of typed results",
                f"query context: {intent.intent.query}",
            ],
            sources=["emergent/graph/__init__.py", "nodnod docs"],
        ))


@G.node
class ToolNode:
    """Select and invoke the best tool for the task."""

    def __init__(self, call: ToolCall) -> None:
        self.call = call

    @classmethod
    async def __compose__(cls, intent: IntentNode) -> "ToolNode":
        # In production: tool registry lookup + actual tool execution
        print(f"  [tool]      selecting tool for: '{intent.intent.query}'")
        await asyncio.sleep(0.03)  # runs in parallel with ResearchNode
        return cls(ToolCall(
            tool_name="graph_composer",
            args={"query": intent.intent.query},
            result="composition graph resolved — 3 nodes, 2 parallel branches",
        ))


@G.node
class SynthesisNode:
    """Combine research + tool output into final response."""

    def __init__(self, result: SynthesisResult) -> None:
        self.result = result

    @classmethod
    async def __compose__(
        cls,
        research: ResearchNode,  # depends on ResearchNode
        tool: ToolNode,          # depends on ToolNode
                                 # → framework schedules both first, then this
    ) -> "SynthesisNode":
        print(f"  [synthesis] combining {len(research.result.facts)} facts + tool result")
        await asyncio.sleep(0.01)

        facts_summary = "; ".join(research.result.facts[:2])
        response = (
            f"Based on research ({facts_summary}) and tool output "
            f"({tool.call.result}), the answer follows emergent's "
            f"compositional model."
        )
        return cls(SynthesisResult(
            response=response,
            used_tools=[tool.call.tool_name],
            confidence=0.87,
        ))


# ─────────────────────────────────────────────────────────────────────────────
# Observable Derivation — streaming pipeline events (Issue #7 prototype)
#
# This is the fold_stream() idea made concrete: instead of awaiting
# a single final result, we yield intermediate derivation events
# as each node completes. Consumers get progressive updates.
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class DerivationEvent:
    """A single step in the observable derivation stream."""
    node: str
    status: str  # "started" | "completed" | "failed"
    payload: object = None


async def run_observable_pipeline(intent: UserIntent):
    """
    Run the task pipeline with observable intermediate results.

    Yields DerivationEvent for each node completion — the fold_stream()
    pattern from Issue #7, implemented over emergent's graph.

    Usage:
        async for event in run_observable_pipeline(intent):
            print(f"{event.node}: {event.status}")
    """
    # Run sub-tasks with per-node event emission
    # (Real fold_stream would hook into nodnod's internal event bus)

    yield DerivationEvent("pipeline", "started", intent)

    # Phase 1: Intent parsing
    intent_node = IntentNode(intent)
    yield DerivationEvent("IntentNode", "completed", intent_node)

    # Phase 2: Parallel research + tool (simulate concurrent emission)
    research_task = asyncio.create_task(ResearchNode.__compose__(intent_node))
    tool_task = asyncio.create_task(ToolNode.__compose__(intent_node))

    yield DerivationEvent("ResearchNode", "started")
    yield DerivationEvent("ToolNode", "started")

    # Yield events as each completes (order depends on which finishes first)
    done, _ = await asyncio.wait(
        [research_task, tool_task],
        return_when=asyncio.FIRST_COMPLETED
    )
    for task in done:
        node = task.result()
        yield DerivationEvent(type(node).__name__, "completed", node)

    # Wait for remaining
    remaining = [t for t in [research_task, tool_task] if not t.done()]
    for task in remaining:
        node = await task
        yield DerivationEvent(type(node).__name__, "completed", node)

    research_node = research_task.result()
    tool_node = tool_task.result()

    # Phase 3: Synthesis
    yield DerivationEvent("SynthesisNode", "started")
    synthesis_node = await SynthesisNode.__compose__(research_node, tool_node)
    yield DerivationEvent("SynthesisNode", "completed", synthesis_node)

    yield DerivationEvent("pipeline", "completed", synthesis_node.result)


# ─────────────────────────────────────────────────────────────────────────────
# Saga: Multi-step task with rollback
#
# Demonstrates saga pattern for stateful agentic workflows where
# partial failures must unwind prior side effects (e.g., external API calls).
# ─────────────────────────────────────────────────────────────────────────────

async def _acquire_tool_lock(tool: str) -> str:
    print(f"  [saga] acquiring lock on tool: {tool}")
    await asyncio.sleep(0.01)
    return f"lock:{tool}:abc123"


async def _release_tool_lock(lock_id: str) -> None:
    print(f"  [saga] releasing lock: {lock_id}")


async def _invoke_tool(lock_id: str) -> str:
    print(f"  [saga] invoking tool under lock: {lock_id}")
    await asyncio.sleep(0.02)
    return f"tool_result:success"


async def _undo_tool_invocation(result: str) -> None:
    print(f"  [saga] reverting tool invocation: {result}")


async def run_saga_pipeline(tool_name: str):
    """
    Run a saga-based task pipeline with automatic rollback.

    Models a two-phase agentic workflow:
      Step 1: acquire a resource lock (compensate: release lock)
      Step 2: invoke the tool    (compensate: undo invocation)

    If step 2 fails, step 1's compensation runs automatically.
    """
    saga = S.step(
        action=L.catching_async(
            lambda: _acquire_tool_lock(tool_name),
            on_error=lambda e: TaskError(str(e))
        ),
        compensate=_release_tool_lock,
    ).then(
        lambda lock_id: S.step(
            action=L.catching_async(
                lambda: _invoke_tool(lock_id),
                on_error=lambda e: TaskError(str(e))
            ),
            compensate=_undo_tool_invocation,
        )
    )

    return await S.run_chain(saga)


# ─────────────────────────────────────────────────────────────────────────────
# Demo
# ─────────────────────────────────────────────────────────────────────────────

async def main() -> None:
    sep = "─" * 55

    # ── 1. Graph pipeline (auto-parallelized) ────────────────────────────────
    print(f"\n{sep}")
    print("1. Graph Pipeline (auto-parallelized DAG)")
    print(sep)

    intent = UserIntent(
        query="How does emergent's graph module handle dependency resolution?",
        session_id="sess-001",
    )

    from emergent import graph as G
    result = await G.compose(SynthesisNode, intent)
    print(f"\n  ✓ Final response (confidence={result.result.confidence}):")
    print(f"    {result.result.response[:80]}...")

    # ── 2. Observable derivation (fold_stream prototype) ─────────────────────
    print(f"\n{sep}")
    print("2. Observable Derivation (fold_stream prototype — Issue #7)")
    print(sep)

    print("\n  Streaming pipeline events:")
    async for event in run_observable_pipeline(intent):
        status_icon = {"started": "→", "completed": "✓", "failed": "✗"}.get(event.status, "?")
        print(f"    {status_icon} [{event.node}] {event.status}")

    # ── 3. Saga pipeline (with rollback) ─────────────────────────────────────
    print(f"\n{sep}")
    print("3. Saga Pipeline (stateful workflow with auto-rollback)")
    print(sep)

    print("\n  Running saga...")
    result = await run_saga_pipeline("graph_composer")
    match result:
        case Ok(r):
            print(f"  ✓ Saga completed: {r.value}")
        case Error(e):
            print(f"  ✗ Saga failed + rolled back: {e}")

    print(f"\n{sep}\n")


if __name__ == "__main__":
    asyncio.run(main())
