import asyncio

from .messages import ChannelEvents


class ChannelJoinFailure(Exception):
    pass


class ChannelLeaveFailure(Exception):
    pass

# TODO: Random thought, but _might_ be nice to ditch the
# mutable-ness of these classes.
# Like a Channel can be joined or not.
# Maybe we should have a JoinedChannel class vs a Channel class.
# `.channel` always returns the Channel.
# `.join` returns the JoinedChannel (and if already joined does nothing extra).
# Not sure if it'd make a good API, but worth thinking about...


class Channel:
    '''
    A channel on a phoenix server.

    Should not be instantiated directly, but through a socket.
    '''
    def __init__(self, socket, topic, params):
        self.socket = socket
        self.topic = topic
        self.params = params
        self._incoming_messages = asyncio.Queue()
        # TODO: Consider something like channel_states in js lib?

    async def join(self):
        '''
        Joins the channel.
        '''
        join = await self.socket._send_message(
            self.topic, ChannelEvents.join.value, self.params
        )
        response = await join.response()
        if response['status'] != 'ok':
            # TODO: This exception needs more info...
            raise ChannelJoinFailure()

        return response['response']

    async def leave(self):
        '''
        Leaves the channel.
        '''
        leave = await self.socket._send_message(
            self.topic, ChannelEvents.leave.value, self.params
        )
        response = await leave.response()
        if response['status'] != 'ok':
            raise ChannelLeaveFailure()

    async def send(self, event, payload):
        '''
        Sends a message to a channel.

        :param event:    The event to send.
        :param payload:  The payload for the event.
        '''
        msg = await self.socket._send_message(self.topic, event, payload)
        return msg

    async def receive(self):
        msg = await self._incoming_messages.get()
        return msg

    async def __aenter__(self):
        resp = await self.join()
        return self, resp

    async def __aexit__(self, exc_type, exc_value, tb):
        await self.leave()
