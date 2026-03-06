"""
In-memory storage provider for Task.

In production: swap MemoryRelationalProvider for SqliteProvider,
PostgresProvider, etc. The Task dataclass never changes.
"""

from __future__ import annotations

from nodnod import scalar_node
from emergent.wire.axis.query.providers.memory import MemoryRelationalProvider
from emergent.wire.axis.query._provider import SequenceNextId


@scalar_node
class Tasks:
    """Provider node — injected by the emergent DI system."""

    @classmethod
    def __compose__(cls):
        return MemoryRelationalProvider(
            key_fn=lambda task: task.id,
            next_id=SequenceNextId(),
        )
