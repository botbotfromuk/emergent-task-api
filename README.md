# emergent-task-api

**Agentic task orchestration built on [emergent](https://github.com/prostomarkeloff/emergent).**

This repo is a working proof-of-concept showing how emergent's compositional primitives map naturally onto agentic pipelines. The core insight: **an agentic pipeline is a computation graph** — and emergent already knows how to resolve those.

---

## What this demonstrates

### 1. Graph Pipeline (auto-parallelized)

Each task unit is a typed graph node. Dependencies are declared via type annotations — the framework resolves execution order and runs independent nodes in parallel automatically.

```
UserIntent ──┬──► ResearchNode ──┐
             └──► ToolNode    ──►├──► SynthesisNode
```

No manual `asyncio.gather()` needed. You declare *what depends on what*, emergent figures out *when* to run it.

```python
@G.node
class ResearchNode:
    @classmethod
    async def __compose__(cls, intent: IntentNode) -> "ResearchNode":
        # fetch from RAG / vector DB / web search
        ...

@G.node
class SynthesisNode:
    @classmethod
    async def __compose__(cls, research: ResearchNode, tool: ToolNode) -> "SynthesisNode":
        # runs after BOTH research and tool complete — automatically
        ...

result = await G.compose(SynthesisNode, intent)
```

### 2. Observable Derivation (fold_stream prototype)

Streaming intermediate results as each node completes — rather than waiting for the whole pipeline. This is the prototype behind [Issue #7](https://github.com/prostomarkeloff/emergent/issues/7) on the emergent repo.

```python
async for event in run_observable_pipeline(intent):
    print(f"[{event.node}] {event.status}")
# → [pipeline] started
# → [IntentNode] completed
# → [ResearchNode] started
# → [ToolNode] started
# ✓ [ToolNode] completed        ← ToolNode finishes first (faster I/O)
# ✓ [ResearchNode] completed
# ✓ [SynthesisNode] completed
# ✓ [pipeline] completed
```

The event ordering reflects real async concurrency — whichever node finishes first, emits first. This enables progressive UI updates and early-exit optimization.

### 3. Saga Pipeline (stateful workflows with rollback)

For agentic steps that have side effects (acquiring locks, calling external APIs, writing state), emergent's saga pattern provides automatic rollback on failure.

```python
saga = S.step(
    action=acquire_tool_lock(tool_name),
    compensate=release_lock,         # ← runs if step 2 fails
).then(lambda lock_id:
    S.step(
        action=invoke_tool(lock_id),
        compensate=undo_invocation,
    )
)

result = await S.run_chain(saga)
# If invoke_tool() fails → release_lock() runs automatically
```

---

## Running

Requires [emergent](https://github.com/prostomarkeloff/emergent) installed from source.

```bash
git clone https://github.com/prostomarkeloff/emergent
cd emergent && pip install -e .
git clone https://github.com/botbotfromuk/emergent-task-api
cd emergent-task-api
python -m tasks.pipeline
```

Expected output:
```
1. Graph Pipeline (auto-parallelized DAG)
  [tool]      selecting tool for: '...'
  [research]  searching for: '...'     ← parallel with tool
  [synthesis] combining 3 facts + tool result
  ✓ Final response (confidence=0.87)

2. Observable Derivation (fold_stream prototype — Issue #7)
  → [pipeline] started
  ✓ [IntentNode] completed
  → [ResearchNode] started
  → [ToolNode] started
  ✓ [ToolNode] completed
  ✓ [ResearchNode] completed
  ✓ [SynthesisNode] completed
  ✓ [pipeline] completed

3. Saga Pipeline (stateful workflow with auto-rollback)
  ✓ Saga completed: tool_result:success
```

---

## Open questions / future directions

- **Multi-provider composition** ([Issue #6](https://github.com/prostomarkeloff/emergent/issues/6)): Can different nodes in the same graph use different storage backends? Scoped providers per subtree?
- **Native fold_stream()**: Hook into nodnod's internal event bus for first-class streaming. See [Issue #7](https://github.com/prostomarkeloff/emergent/issues/7).
- **TypeForm-aware dispatch** ([Issue #5](https://github.com/prostomarkeloff/emergent/issues/5)): Use PEP 747 TypeForm to select composition strategy at the type level.

---

## Why emergent for agentic systems?

Most agent frameworks hardcode execution strategies (sequential, concurrent, retry). emergent separates **what** from **how**: you write nodes that declare their typed dependencies, and the graph executor figures out the rest. This composability is exactly what agentic pipelines need — tasks that compose like functions, not like threads.

The saga pattern handles the messy reality of side effects. The cache layer makes repeated agent runs idempotent. Together, they give you a backend that can reason about failure, not just crash on it.
