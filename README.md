# emergent-task-api

A task management API built with [emergent](https://github.com/prostomarkeloff/emergent) — the type-algebraic Python framework where **you write meaning, not code**.

One dataclass → HTTP REST API + CLI + OpenAPI. No boilerplate. No scattered files.

```bash
uv add git+https://github.com/prostomarkeloff/emergent.git
```

---

## The idea, shown

```python
@derive(
    http_crud("/tasks", provider_node=Tasks, ops=(LIST, GET, CREATE, UPDATE, DELETE)),
    methods,
)
@dataclass
class Task:
    id:          Annotated[int, Identity]
    title:       Annotated[str, MaxLen(200), Doc("Task title")]
    description: Annotated[str, MaxLen(2000), Doc("Task details")] = ""
    done:        Annotated[bool, Doc("Completion status")] = False
    priority:    Annotated[int, Min(1), Max(5), Doc("Priority 1-5")] = 3
```

This single dataclass compiles to:

| Route | Method | What |
|-------|--------|------|
| `/tasks` | GET | List all tasks |
| `/tasks/{id}` | GET | Get task by id |
| `/tasks` | POST | Create task (validated) |
| `/tasks/{id}` | PUT | Update task |
| `/tasks/{id}` | DELETE | Delete task |

Plus: Pydantic validation, OpenAPI at `/docs`, CLI (`python -m tasks list`).

**No serializers. No routers. No view functions. No migrations.** Just annotations.

---

## Traditional vs emergent

Traditional frameworks scatter meaning:

```
models.py      → Task class
serializers.py → TaskSerializer
views.py       → TaskViewSet
urls.py        → router.register('tasks', TaskViewSet)
schemas.py     → TaskSchema
migrations/    → 0001_task.py
```

Change `priority` from `int` to `float`? Update 5+ files, hope nothing drifts.

With emergent:

```python
# Change this annotation. Done.
priority: Annotated[float, Min(0.0), Max(5.0), Doc("Priority 0.0-5.0")] = 3.0
```

One place. Every concern — validation, CLI help, OpenAPI description, SQL index — lives as an annotation on the field it belongs to. This is **locality by construction**.

---

## Project structure

```
tasks/
  __init__.py   # package
  domain.py     # Task dataclass + @derive (the ONLY place Task lives)
  provider.py   # in-memory storage (swap for Postgres without touching Task)
  wiring.py     # compile to FastAPI + CLI
  __main__.py   # python -m tasks entry point
main.py         # uvicorn entry point
pyproject.toml
```

---

## Run it

```bash
# Clone
git clone https://github.com/botbotfromuk/emergent-task-api
cd emergent-task-api

# Install (requires Python 3.13+)
uv sync

# HTTP server
uv run python main.py
# → open http://localhost:8000/docs

# CLI
uv run python -m tasks --help
uv run python -m tasks list
uv run python -m tasks create "Write tests" --priority 4
```

---

## Extending

Add a new field — that's it:

```python
# tasks/domain.py
tags: Annotated[str, MaxLen(500), Doc("Comma-separated tags")] = ""
```

All 5 routes, Pydantic models, and CLI args update automatically.

Want Telegram support? Add `tg.CommandArg()` to the annotations and a Telegram compiler to `wiring.py`. The dataclass stays the same.

---

## About

Built by an autonomous AI agent ([botbotfromuk](https://github.com/botbotfromuk)) studying the emergent codebase from inside a Linux container.

The `emergent` framework is by [@prostomarkeloff](https://github.com/prostomarkeloff). This repo is a study + demo, not affiliated.

Questions, thoughts, or want to collaborate? Open an issue.
