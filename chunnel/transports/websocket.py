import asyncio
import json
import logging
import websockets

from .base import BaseTransport
from ..messages import load_incoming_message, dump_outgoing_message

__all__ = ['WebsocketTransport']

logger = logging.getLogger(__name__)


class WebsocketTransport(BaseTransport):
    '''
    Implements the websocket transport for talking to phoenix servers.
    '''
    def __init__(self, url, incoming_queue, outgoing_queue):
        super().__init__(
            incoming_queue=incoming_queue, outgoing_queue=outgoing_queue
        )
        self.url = url
        self.ready = asyncio.Future()

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

    async def _recv_loop(self, websocket):
        while True:
            message_data = await websocket.recv()
            logger.info("received: %s", message_data)
            # TODO: This needs updates.
            message = load_incoming_message(json.loads(message_data))
            await self.incoming.put(message)
            logger.info("sent")

    async def _send_loop(self, websocket):
        while True:
            message = await self.outgoing.get()
            logger.info("sending: %s", message)
            try:
                # TODO: This needs updates.
                message_data = json.dumps(dump_outgoing_message(message))
                await websocket.send(message_data)
                message.sent.set_result(True)
            except Exception as e:
                message.sent.set_exception(e)
            logger.info("sent")
