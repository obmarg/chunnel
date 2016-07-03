import asyncio

from chunnel.messages import IncomingMessage
from chunnel.transports.base import BaseTransport, TransportMessage


class TestTransport(BaseTransport):
    '''
    A transport implementation for testing.
    '''
    RESOLVE_READY = True

    def __init__(self, url, params, incoming, outgoing):
        self.url = url
        self.params = params
        super().__init__(incoming, outgoing)
        self._future = asyncio.Future()
        if self.RESOLVE_READY:
            self.ready.set_result(True)

    async def run(self):
        self.running = True
        await self._future
        self.running = False

    async def stop(self):
        self._future.set_result(True)


# TODO: Decide if this class is worth it.
# Currently just used in one place, and quite easy to do a gather w/
# set_reply instead...
class TestSender():
    '''
    Helper class for sending test messages and setting their responses.

    Example:

        sender = TestSender('test:topic', 'an_event', {})
        sender.set_reply({'whatever': 'you_want'})
        msg = await sender.send(socket)
        response = await msg.response()
        assert response == {'whatever': 'you_want'}
    '''
    def __init__(self, topic, event, payload):
        self._outgoing = {
            'topic': topic,
            'event': event,
            'payload': payload
        }

    def set_reply(self, payload):
        self._reply_payload = payload

    async def send(self, socket):
        if self._reply_payload:
            other_future = set_reply(
                socket, self._outgoing['topic'], self._reply_payload
            )
        else:
            other_future = _mark_sent(socket)

        _, sent_message = await asyncio.gather(
            other_future, socket._send_message(**self._outgoing)
        )
        return sent_message


async def _mark_sent(socket):
    '''
    Marks the next outgoing message as sent.
    '''
    msg = await socket.transport.outgoing.get()
    msg.sent.set_result(True)


async def set_reply(socket, topic, payload):
    '''
    Sets the reply to the next sent message.

    Also marks the message as sent if it is not already.
    '''
    msg = await socket.transport.outgoing.get()
    if not msg.sent.done():
        msg.sent.set_result(True)

    await socket.transport.incoming.put(
        TransportMessage('phx_reply', topic, payload, msg.message.ref)
    )
