"""hwhkit.scheduler — APScheduler-backed scheduler implementing ``Scheduler`` contract.

Public surface::

    from hwhkit.scheduler import SchedulerProvider, SchedulerConfig, scheduled_task
"""

from hwhkit.scheduler.config import SchedulerConfig
from hwhkit.scheduler.decorators import register_scheduled_tasks, scheduled_task
from hwhkit.scheduler.provider import SchedulerProvider

__all__ = [
    "SchedulerConfig",
    "SchedulerProvider",
    "register_scheduled_tasks",
    "scheduled_task",
]
