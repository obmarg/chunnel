from urllib.parse import urlencode
import asyncio
import json
import logging

import websockets

from .base import BaseTransport, TransportMessage
from ..utils import get_unless_done, DONE

__all__ = ['WebsocketTransport']

logger = logging.getLogger(__name__)


class WebsocketTransport(BaseTransport):
    '''
    Implements the websocket transport for talking to phoenix servers.
    '''
    def __init__(self, url, params, incoming_queue, outgoing_queue):
        super().__init__(
            incoming_queue=incoming_queue, outgoing_queue=outgoing_queue
        )
        qs_params = {'vsn': '1.0.0', **params}
        self.url = url + '?' + urlencode(qs_params)
        print(self.url)
        self.ready = asyncio.Future()
        self._done = asyncio.Future()

    async def run(self):
        try:
            async with websockets.connect(self.url) as websocket:
                self.ready.set_result(True)
                # TODO: Think about error propagation at some point?
                # If one of these crashes, does it cancel the other?
                # It should, not sure if it does.
                await asyncio.gather(
                    self._recv_loop(websocket), self._send_loop(websocket)
                )
        except Exception as e:
            if not self.ready.done():
                self.ready.set_exception(e)

            raise

    async def stop(self):
        self._done.set_result(True)

    async def _recv_loop(self, websocket):
        while True:
            message_data = await get_unless_done(websocket.recv(), self._done)
            if message_data is DONE:
                return

            logger.info("received: %s", message_data)
            # TODO: This needs updates.
            message = _load_incoming_message(json.loads(message_data))
            await self.incoming.put(message)
            logger.info("sent")

    async def _send_loop(self, websocket):
        while True:
            message = await get_unless_done(self.outgoing.get(), self._done)
            if message is DONE:
                return

            logger.info("sending: %s", message)
            try:
                # TODO: This needs updates.
                message_data = json.dumps(
                    dump_outgoing_message(message.message)
                )
                await websocket.send(message_data)
                message.sent.set_result(True)
            except Exception as e:
                message.sent.set_exception(e)
            logger.info("sent")


def _load_incoming_message(message_data):
    return TransportMessage(
        message_data['event'],
        message_data['topic'],
        message_data['payload'],
        message_data.get('ref')
    )


def dump_outgoing_message(message):
    return {
        'event': message.event,
        'topic': message.topic,
        'ref': message.ref,
        'payload': message.payload
    }
