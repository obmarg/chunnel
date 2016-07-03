import asyncio

import pytest

from chunnel.utils import get_unless_done, DONE


@pytest.mark.asyncio
async def test_get_unless_done_getting():
    queue = asyncio.Queue()
    await queue.put(1)
    await queue.put(2)
    future = asyncio.Future()
    assert await get_unless_done(queue.get(), future) == 1
    assert await get_unless_done(queue.get(), future) == 2


@pytest.mark.asyncio
async def test_get_unless_done_when_done():
    queue = asyncio.Queue()
    future = asyncio.Future()
    future.set_result(True)
    assert await get_unless_done(queue.get(), future) is DONE


@pytest.mark.asyncio
async def test_get_unless_done_when_done_and_queue():
    queue = asyncio.Queue()
    future = asyncio.Future()
    future.set_result(True)
    await queue.put(1)
    assert await get_unless_done(queue.get(), future) is DONE
