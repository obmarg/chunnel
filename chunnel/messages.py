from collections import namedtuple
from enum import Enum


class MessageStatus(Enum):
    ok = 'ok'
    error = 'error'


class IncomingMessage:
    def __init__(self, transport_message, socket):
        self._transport_message = transport_message
        self._socket = socket

    @property
    def event(self):
        return self._transport_message.event

    @property
    def payload(self):
        return self._transport_message.payload

    async def reply(self, status, response):
        await self._socket._send_message(
            self._transport_message.topic,
            ChannelEvents.reply.value,
            {'status': status, 'response': response},
            self._transport_message.ref
        )


# TODO: Think about where this belongs...
class ChannelEvents(Enum):
    close = "phx_close",
    error = "phx_error"
    join = "phx_join"
    reply = "phx_reply"
    leave = "phx_leave"


# TODO: PushedMessage?
class SentMessage:
    def __init__(self, response_future):
        self._response_future = response_future

    async def response(self):
        # TODO: Definitely need to think more about timeouts...
        # Currently the self._future is wrapped in a timeout, but is that what
        # I want?
        resp = await self._response_future
        return resp
