Chunnel
---

A python client for [phoenix](http://www.phoenixframework.org/)
[channels](http://www.phoenixframework.org/docs/channels).

Usage
---

```python
from chunnel import Socket

socket = Socket('ws://example.com/socket', params={'token': 'blah'})
async with socket:
    channel = socket.channel('room:lobby, {})
    await channel.join()
    incoming = await channel.receive()
    await incoming.reply({'blah': 'whatever'})
    msg = await channel.push('something', {})
    response = await msg.response()
```

Status
---

Chunnel is very much in alpha status right now. It's API can (and probably will)
change, there's many edge cases that are not currently handled, and many TODOs
littered about the code.

Currently implemented:

- Joining channels
- Receving messages
- Sending messages

Not implemented:

- Documentation
- Incoming channel leave messages
- Connection errors/reconnecting.
- Much other error handling
- Presence
- Probably other things

Pull requests welcome.
