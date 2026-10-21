import asyncio
from typing import Any

BACKGROUND_TASKS: set[asyncio.Task[None]] = set()


def run_in_background(coro: Any) -> None:
    task = asyncio.create_task(coro)
    BACKGROUND_TASKS.add(task)
    task.add_done_callback(BACKGROUND_TASKS.discard)


async def cancel_background_tasks() -> None:
    tasks = list(BACKGROUND_TASKS)
    for task in tasks:
        task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
