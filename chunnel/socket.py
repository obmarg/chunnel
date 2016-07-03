from concurrent.futures import FIRST_COMPLETED
from urllib.parse import urlsplit
import asyncio
import logging

from .transports import (
    WebsocketTransport, TransportMessage, OutgoingTransportMessage
)
from .channel import Channel
from .messages import SentMessage, ChannelEvents, IncomingMessage
from .utils import get_unless_done, DONE

__all__ = ['Socket']

logger = logging.getLogger(__name__)


# TODO: Should this be called Socket? Dunno if it matches up with phoenix too
# well..
class Socket:
    '''
    A connection to a phoenix server.

    A transport will automatically be selected based on the URL provided.
    See the TRANSPORTS dict for more details.

    :param url:    The URL of the phoenix server to connect to.
    :param params: Optional parameters to use when connecting.
    '''

    # A mapping of url scheme -> transport.
    TRANSPORTS = {
        'ws': WebsocketTransport,
        'wss': WebsocketTransport
    }

    # TODO: Should these parameters be passed to connect?  Maybe not..
    def __init__(self, url, params):
        self.url = url
        self.params = params
        self.connected = False
        self.channels = {}
        self._incoming = asyncio.Queue()
        self._outgoing = asyncio.Queue()
        self._ref = 1
        self._response_futures = {}

    async def connect(self):
        if self.connected:
            raise Exception("Already connected!")

        transport_class = self.TRANSPORTS[urlsplit(self.url).scheme]
        self.transport = transport_class(
            self.url, self.params, self._incoming, self._outgoing
        )
        transport_task = asyncio.ensure_future(self.transport.run())

        await self.transport.ready

        self._transport_task = transport_task
        self._done_recv = asyncio.Future()
        self._recv_task = asyncio.ensure_future(self._recv_loop())
        # TODO: Ok, so this is cool - but how to tell if our transport_task has
        # failed.
        self.connected = True

    async def disconnect(self):
        if not self.connected:
            raise Exception("Not connected!")

        self._done_recv.set_result(True)
        await self.transport.stop()

        await asyncio.gather(self._recv_task, self._transport_task)

        self.connected = False

    def channel(self, topic, params):
        # TODO: What to do if we already have this channel?
        channel = Channel(self, topic, params)
        self.channels[topic] = channel
        return channel

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.disconnect()

    async def _check_transport(self):
        # TODO: More thought around this function...
        if not self.connected:
            raise Exception("Not connected!")
        if self._transport_task.done():
            # We've probably excepted.
            # TODO: Do something more thorough here...
            self._transport_task.result()

    # TODO: _push_message?
    async def _send_message(self, topic, event, payload, ref=None):
        '''
        Sends a message to the remote.

        :param topic:   The topic to send the message on.
        :param event:   The name of the event to send.
        :param payload: The payload of the event.
        :param ref:     Optional ref to use for sending.
        :returns:       The ref of the event, which can be used to receive
                        replies.
        '''
        if not ref:
            ref = self._ref
            self._ref += 1

        message = OutgoingTransportMessage(
            TransportMessage(event, topic, payload, ref),
            asyncio.Future()
        )
        # TODO: add a done callback to reply_future that deletes it from
        # self._response_futures after a certain time...
        resp_future = asyncio.Future()
        self._response_futures[ref] = resp_future
        await self._outgoing.put(message)
        await message.sent
        # TODO: Return something slightly different....
        return SentMessage(resp_future)

    async def _recv_loop(self):
        '''
        Runs the socket receive loop.

        This will read incoming messages off the queue and attempt to route
        them to an appropriate place.
        '''
        while True:
            message = await get_unless_done(
                self._incoming.get(), self._done_recv
            )
            if message is DONE:
                break
            # TODO: Definitely need to handle phx_close...
            if message.event == ChannelEvents.reply.value:
                if message.payload['status'] == 'ok':
                    self._response_futures[message.ref].set_result(
                        message.payload.get('response')
                    )
                else:
                    # TODO: we can do better than this...
                    self._response_futures[message.ref].set_exception(
                        Exception("Response not ok!")
                    )
            else:
                channel = self.channels.get(message.topic)
                if channel:
                    await channel._incoming_messages.put(
                        IncomingMessage(message, self)
                    )
