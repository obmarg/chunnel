from unittest.mock import sentinel
import asyncio

import pytest

from chunnel.transports import TransportMessage

from .shared import TestTransport, TestSender


@pytest.mark.asyncio
async def test_connecting(socket, mocker):
    mocker.patch.object(TestTransport, 'RESOLVE_READY', new=False)

    connect_future = asyncio.ensure_future(socket.connect())
    await asyncio.sleep(0)
    assert socket.transport.params == sentinel.connect_params

    assert socket.transport
    assert socket.transport.url == 'ws://localhost'
    assert not connect_future.done()

    socket.transport.ready.set_result(True)
    await asyncio.sleep(0)
    assert connect_future.done()
    assert socket.connected
    await connect_future

    await socket.disconnect()


@pytest.mark.asyncio
async def test_connect_as_context_manager(socket):
    async with socket as socket:
        assert socket.connected

    assert not socket.connected


@pytest.mark.asyncio
async def test_creating_channel(socket):
    async with socket:
        channel = socket.channel("test:topic", sentinel.channel_params)
        assert channel.topic == 'test:topic'
        assert channel.params == sentinel.channel_params
        assert 'test:topic' in socket.channels
        assert socket.channels['test:topic'] == channel


@pytest.mark.asyncio
async def test_sending_message(socket):
    async with socket:
        send_future = asyncio.ensure_future(
            socket._send_message(
                sentinel.topic, sentinel.event, sentinel.payload
            )
        )
        await asyncio.sleep(0)
        assert socket.transport.outgoing.qsize() == 1
        message, sent_future = socket.transport.outgoing.get_nowait()
        assert message.event == sentinel.event
        assert message.topic == sentinel.topic
        assert message.payload == sentinel.payload
        assert message.ref

        sent_future.set_result(True)

        await asyncio.sleep(0)
        assert send_future.done()
        assert await send_future


@pytest.mark.asyncio
async def test_replies_routed_correctly(socket):
    async with socket:
        sender = TestSender(sentinel.topic, sentinel.event, sentinel.payload)
        sender.set_reply({'status': 'ok', 'response': sentinel.response})

        sent_message = await sender.send(socket)

        assert await sent_message.response() == sentinel.response


@pytest.mark.asyncio
async def test_channel_messages_routed_correctly(socket):
    async with socket:
        channel = socket.channel("test:topic", sentinel.channel_params)
        message = TransportMessage(
            sentinel.event, "test:topic", sentinel.payload, sentinel.ref
        )
        await socket.transport.incoming.put(message)
        message = await channel.receive()
        assert message.event == sentinel.event
        assert message.payload == sentinel.payload
