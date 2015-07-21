import os
from esppy.child_process import ChildProcess
import asyncio
import time
import signal

from esppy.protocols import WorkerProtocol, MsgType


class Worker:
    def __init__(self, loop):
        self.loop = loop
        self._started = False
        self.start()

    def start(self):
        assert not self._started
        self._started = True

        up_read, up_write = os.pipe()
        down_read, down_write = os.pipe()

        pid = os.fork()
        if pid:
            # parent
            self.pid = pid
            os.close(up_read)
            os.close(down_write)

            asyncio.async(self.connect(down_read, up_write))
        else:
            # child
            os.close(up_write)
            os.close(down_read)

            asyncio.set_event_loop(None)
            process = ChildProcess(up_read, down_write)
            process.start()

    @asyncio.coroutine
    def connect(self, read, write):
        loop = self.loop
        __, self.reader = yield from loop.connect_read_pipe(
            WorkerProtocol, os.fdopen(read, 'rb'))
        __, self.writer = yield from loop.connect_write_pipe(
            WorkerProtocol, os.fdopen(write, 'wb'))

        self.ping = time.monotonic()
        self.heartbeat_task = asyncio.Task(self.heartbeat())
        self.chat_task = asyncio.Task(self.chat())

    @asyncio.coroutine
    def heartbeat(self):
        while self._started:
            yield from asyncio.sleep(15)
            if (time.monotonic() - self.ping < 30):
                self.writer.ping()
            else:
                print('Unresponsive worker detected')
                yield from self.kill()
                self.start()
                return

    @asyncio.coroutine
    def chat(self):
        while self._started:
            try:
                msg = yield from self.reader.read()
            except:
                print('Unresponsive worker detected')
                yield from self.kill()
                self.start()
                return
            if msg == MsgType.PONG:
                self.ping = time.monotonic()

    @asyncio.coroutine
    def kill(self):
        self._started = False
        self.heartbeat_task.cancel()
        self.chat_task.cancel()
        yield from asyncio.wait([self.heartbeat_task, self.chat_task])
        os.kill(self.pid, signal.SIGTERM)
        self.reader.close()
        self.writer.close()
