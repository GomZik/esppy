import os
import asyncio
import signal
from esppy.protocols import WorkerProtocol, MsgType


class ChildProcess:
    def __init__(self, read, write):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self._read = read
        self._write = write

    def start(self):
        self.loop.run_until_complete(self.connect())
        self.loop.add_signal_handler(signal.SIGINT, self.stop)
        self.loop.run_forever()

    @asyncio.coroutine
    def connect(self):
        loop = self.loop
        __, self.reader = yield from loop.connect_read_pipe(
            WorkerProtocol, os.fdopen(self._read, 'rb'))
        __, self.writer = yield from loop.connect_write_pipe(
            WorkerProtocol, os.fdopen(self._write, 'wb'))

        self.heartbeat_task = asyncio.Task(self.heartbeat())

    @asyncio.coroutine
    def heartbeat(self):
        while True:
            try:
                msg = yield from self.reader.read()
            except:
                print('Supervisor is dead. Exiting.')
                self.stop()
                return
            if msg == MsgType.PING:
                self.writer.pong()

    def stop(self):

        @asyncio.coroutine
        def _stop():
            self.heartbeat_task.cancel()
            yield from asyncio.wait([self.heartbeat_task])
            self.reader.close()
            self.writer.close()
            self.loop.stop()
            os._exit(0)
        asyncio.async(_stop())
