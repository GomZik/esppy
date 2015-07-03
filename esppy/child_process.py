import os
import asyncio
import signal


class ChildProcess:
    def __init__(self, sock):
        self.sock = sock
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def start(self):
        self.loop.run_until_complete(self.connect())
        self.loop.add_signal_handler(signal.SIGINT, self.stop)
        self.loop.run_forever()

    @asyncio.coroutine
    def connect(self):
        reader, writer = yield from asyncio.open_connection(sock=self.sock)
        self.reader, self.writer = reader, writer
        asyncio.async(self.wait(reader))

    @asyncio.coroutine
    def wait(self, reader):
        pass

    def stop(self):
        self.loop.stop()
        os._exit(0)
