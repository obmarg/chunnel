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
        try:
            response = await join.response()
        except Exception as e:
            # TODO: this needs some work.
            raise ChannelJoinFailure() from e

        return response

    async def leave(self):
        '''
        Leaves the channel.
        '''
        leave = await self.socket._send_message(
            self.topic, ChannelEvents.leave.value, self.params
        )
        try:
            response = await leave.response()
        except Exception as e:
            # TODO: this needs some work.
            raise ChannelLeaveFailure() from e

    async def push(self, event, payload):
        '''
        Pushes a message to a channel.

        :param event:    The event to push.
        :param payload:  The payload for the event.
        '''
        msg = await self.socket._send_message(self.topic, event, payload)
        return msg

    # TODO: could be nice to just expose a "read only queue" under .incoming
    # With get, get_nowait & an async iterator interface?
    # TODO: Otherwise should maybe be called pull (to go with push)
    async def receive(self):
        msg = await self._incoming_messages.get()
        return msg

    async def __aenter__(self):
        resp = await self.join()
        return self, resp

    async def __aexit__(self, exc_type, exc_value, tb):
        await self.leave()
