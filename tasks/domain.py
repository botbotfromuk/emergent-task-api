"""
Task domain — the ONLY place where Task is defined.

Everything else (HTTP, CLI, validation, OpenAPI) is derived
automatically from these annotations.

Locality by construction:
  - MaxLen(200)  → Pydantic validator + OpenAPI constraint
  - Doc("...")   → OpenAPI description
  - Identity     → primary key across all targets
  - Min/Max      → validation enforced everywhere

Change a field here → all targets update. No other files to touch.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Annotated

from derivelib import derive, methods
from derivelib.patterns import http_crud
from derivelib.patterns._http import LIST, GET, CREATE, UPDATE, DELETE
from emergent.wire.axis.schema import Identity, Doc, MaxLen
from emergent.wire.axis.schema.validators import Min, Max

from tasks.provider import Tasks


@derive(
    http_crud(
        "/tasks",
        provider_node=Tasks,
        ops=(LIST, GET, CREATE, UPDATE, DELETE),
    ),
    methods,
)
@dataclass
class Task:
    """A task — fully self-describing across all compilation targets."""

    id: Annotated[int, Identity]

    title: Annotated[
        str,
        MaxLen(200),
        Doc("Task title — what needs to be done"),
    ]

    description: Annotated[
        str,
        MaxLen(2000),
        Doc("Detailed description of the task"),
    ] = ""

    done: Annotated[
        bool,
        Doc("Whether the task has been completed"),
    ] = False

    priority: Annotated[
        int,
        Min(1),
        Max(5),
        Doc("Priority level: 1 (lowest) to 5 (highest)"),
    ] = 3

    created_at: Annotated[
        str,
        Doc("ISO 8601 creation timestamp (auto-set)"),
    ] = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
