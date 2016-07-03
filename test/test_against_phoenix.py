from uuid import uuid4
import asyncio
import os

import pytest
import requests

from chunnel.socket import Socket

TEST_CARD_URL = os.getenv('TEST_CARD_URL')
SKIP_TESTS = TEST_CARD_URL is None


@pytest.fixture
def user_id():
    id_ = str(uuid4())
    response = requests.post(
        'http://{}/api/users'.format(TEST_CARD_URL),
        json={"user": {"id": id_, "rooms": ["lobby"]}}
    )
    assert response.status_code == 201
    return id_


def make_socket(user_id):
    return Socket(
        'ws://{}/socket/websocket'.format(TEST_CARD_URL),
        {'user_id': user_id}
    )


@pytest.fixture
def socket(event_loop, user_id):
    return make_socket(user_id)


@pytest.fixture
def socket2(event_loop, user_id):
    return make_socket(user_id)


@pytest.mark.skipif(SKIP_TESTS, reason="TEST_CARD_URL env var not set")
@pytest.mark.asyncio
async def test_join_and_ping(socket):
    async with socket:
        channel = socket.channel("room:lobby", {'join': 'params'})
        assert await channel.join() == {'join': 'params'}
        ping = await channel.push("ping", {"some": "data"})
        assert await ping.response() == {"some": "data"}


@pytest.mark.skipif(SKIP_TESTS, reason="TEST_CARD_URL env var not set")
@pytest.mark.asyncio
async def test_join_and_shout(socket, socket2):
    async with socket:
        async with socket2:
            socket1_channel = socket.channel("room:lobby", {})
            socket2_channel = socket2.channel("room:lobby", {})
            await asyncio.gather(
                socket1_channel.join(), socket2_channel.join()
            )
            shout_payload = {"hello": "is anybody there?"}
            await socket1_channel.push("shout", shout_payload)

            incoming = await socket1_channel.receive()
            assert incoming.payload == shout_payload

            incoming = await socket2_channel.receive()
            assert incoming.payload == shout_payload
