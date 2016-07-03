from concurrent.futures import FIRST_COMPLETED
import asyncio

__all__ = ['DONE', 'get_unless_done']


class DONE():
    '''
    Singleton that indicates a DONE when returned from get_unless_done.
    '''
    pass


# TODO: Tests
async def get_unless_done(getter_future_or_coro, done_future):
    '''
    Wraps a get operation & a future that indicates when we should stop
    getting.

    If the done_future is resolved while waiting for the get, we cancel the get
    and return DONE.

    :params getter_task_or_coro:   A getter.
    :params done_future:           A future that indicates we are done.
    '''
    getter_future = asyncio.ensure_future(getter_future_or_coro)
    done, pending = await asyncio.wait(
        (getter_future, done_future),
        return_when=FIRST_COMPLETED
    )
    if done_future in done:
        if not getter_future.done():
            getter, = pending
            getter.cancel()

        return DONE

    return await getter_future
