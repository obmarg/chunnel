from unittest.mock import sentinel
import asyncio
import logging

import pytest

from chunnel.socket import Socket

from .shared import TestTransport


@pytest.fixture(autouse=True)
def setup_logging():
    logging.basicConfig(level=logging.DEBUG)


@pytest.yield_fixture
def event_loop():
    """
    Create an instance of the default event loop for each test case.

    This implementation is mostly a workaround for pytest-asyncio issues #29 &
    #30
    """
    policy = asyncio.get_event_loop_policy()
    res = policy.new_event_loop()
    asyncio.set_event_loop(res)
    res._close = res.close
    res.close = lambda: None

    yield res

    res._close()


@pytest.fixture
def socket(mocker, event_loop):
    mocker.patch.dict(Socket.TRANSPORTS, {'ws': TestTransport})
    return Socket('ws://localhost', sentinel.connect_params)
