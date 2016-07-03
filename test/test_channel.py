from unittest.mock import sentinel
import asyncio

import pytest

from chunnel.channel import ChannelJoinFailure, ChannelLeaveFailure
from chunnel.messages import ChannelEvents
from chunnel.transports import TransportMessage

from .shared import set_reply


@pytest.yield_fixture
def socket(socket, event_loop):
    event_loop.run_until_complete(socket.connect())
    yield socket
    event_loop.run_until_complete(socket.disconnect())


@pytest.fixture
def channel(socket):
    return socket.channel("test:lobby", {})


@pytest.mark.asyncio
async def test_join(socket, channel):
    response, _ = await asyncio.gather(
        channel.join(),
        set_reply(
            socket,
            None,
            {'status': 'ok', 'response': sentinel.response}
        )
    )
    assert response == sentinel.response


@pytest.mark.asyncio
async def test_join_failure(socket, channel):
    with pytest.raises(ChannelJoinFailure):
        await asyncio.gather(
            channel.join(),
            set_reply(socket, None, {'status': 'error'})
        )


@pytest.mark.asyncio
async def test_leave(socket, channel):
    response, _ = await asyncio.gather(
        channel.join(),
        set_reply(socket, None, {'status': 'ok', 'response': {}})
    )
    await asyncio.gather(
        channel.leave(),
        set_reply(socket, None, {'status': 'ok'})
    )


@pytest.mark.asyncio
async def test_leave_failure(socket, channel):
    response, _ = await asyncio.gather(
        channel.join(),
        set_reply(socket, None, {'status': 'ok', 'response': {}})
    )
    with pytest.raises(ChannelLeaveFailure):
        await asyncio.gather(
            channel.leave(),
            set_reply(socket, None, {'status': 'error'})
        )


@pytest.mark.asyncio
async def test_context_manager_join(socket):
    asyncio.ensure_future(
        set_reply(
            socket, None, {'status': 'ok', 'response': sentinel.response}
        )
    )
    # TODO: Not sure about this api...
    async with socket.channel("test:lobby", {}) as (channel, response):
        assert response == sentinel.response
        assert channel == socket.channels['test:lobby']
        asyncio.ensure_future(
            set_reply(socket, None, {'status': 'ok'})
        )


@pytest.mark.asyncio
async def test_send_message(socket, channel):
    send_future = asyncio.ensure_future(
        channel.push(sentinel.event, sentinel.payload)
    )
    await asyncio.sleep(0)
    assert socket.transport.outgoing.qsize() == 1
    msg, sent_future = socket.transport.outgoing.get_nowait()
    assert msg.topic == channel.topic
    assert msg.event == sentinel.event
    assert msg.payload == sentinel.payload
    sent_future.set_result(True)

    assert await send_future


@pytest.mark.asyncio
async def test_message_replies(socket, channel):
    sent_message, _ = await asyncio.gather(
        channel.push(sentinel.event, sentinel.payload),
        set_reply(socket, None, {'status': 'ok', 'response': 'abcd'})
    )
    response = await sent_message.response()
    assert response == 'abcd'


@pytest.mark.asyncio
async def test_message_receive(socket, channel):
    message = TransportMessage(
        sentinel.event, channel.topic, sentinel.payload, sentinel.ref
    )
    await socket.transport.incoming.put(message)
    await socket.transport.incoming.put(message)
    message = await channel.receive()
    assert message.event == sentinel.event
    assert message.payload == sentinel.payload


@pytest.mark.asyncio
async def test_reply_to_received_message(socket, channel):
    await socket.transport.incoming.put(
        TransportMessage(
            sentinel.event, channel.topic, sentinel.payload, sentinel.ref
        )
    )
    incoming_message = await channel.receive()

    reply_future = asyncio.ensure_future(
        incoming_message.reply(sentinel.status, sentinel.response)
    )
    await asyncio.sleep(0)
    reply, sent_future = await socket.transport.outgoing.get()
    assert reply.topic == channel.topic
    assert reply.event == ChannelEvents.reply.value
    assert reply.payload == {
        'status': sentinel.status, 'response': sentinel.response
    }
    assert reply.ref == sentinel.ref

    sent_future.set_result(True)
    assert reply_future
