import asyncio
from collections import namedtuple


TransportMessage = namedtuple(
    'TransportMessage', ['event', 'topic', 'payload', 'ref']
)

# TODO: Could maybe call this Push to mirror it's name in phoenix js imp.
OutgoingTransportMessage = namedtuple(
    'OutgoingTransportMessage', ['message', 'sent']
)


class BaseTransport:
    '''
    The base class for a transport.

    Transports are used to implement the sending & receiving of messages in
    chunnel. Each transport is constructed with 2 queues - a queue for incoming
    messages and a queue for outgoing messages.

    The incoming message queue should contain TransportMessage namedtuples.

    The outgoing message queue should contain OutgoingTransportMessage
    namedtuples.

    The transport should read messages from the outgoing queue and send them
    onto a phoenix server, and put any incoming messages onto the incoming
    queue.

    Transports are not responsible for interpreting the messages in any way,
    they just handle the communication.
    '''
    def __init__(self, incoming_queue, outgoing_queue):
        self.incoming = incoming_queue
        self.outgoing = outgoing_queue
        self.ready = asyncio.Future()

    async def run(self):
        '''
        Connects the transport and runs it's main loop.

        Will resolve `self.ready` when a connection has been made.
        '''
        raise NotImplementedError

    async def stop(self):
        '''
        Signals to the transport that it should stop.
        '''
        raise NotImplementedError
