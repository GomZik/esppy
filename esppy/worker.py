import os
from esppy.child_process import ChildProcess
import asyncio
from socket import socketpair
import time

from esppy.protocols import WorkerProtocol, MsgType


class Worker:
    def __init__(self, loop):
        self.loop = loop
        self._started = False
        self.start()

    def start(self):
        assert not self._started
        self._started = True

        parent_socket, child_socket = socketpair()

        pid = os.fork()
        if pid:
            # parent
            os.close(child_socket.fileno())
            asyncio.async(self.connect(parent_socket))
        else:
            # child
            os.close(parent_socket.fileno())
            asyncio.set_event_loop(None)
            process = ChildProcess(child_socket)
            process.start()

    @asyncio.coroutine
    def connect(self, sock):
        loop = self.loop
        stream_reader, stream_writer = yield from asyncio.open_connection(
            sock=sock, loop=loop)
        self.channel = WorkerProtocol(stream_reader, stream_writer)
        self.ping = time.monotonic()
        self.heartbeat_task = asyncio.Task(self.heartbeat())
        self.chat_task = asyncio.Task(self.chat())

    @asyncio.coroutine
    def heartbeat(self):
        while True:
            yield from asyncio.sleep(15)
            if (time.monotonic() - self.ping < 30):
                self.channel.ping()
            else:
                print('Unresponsive worker detected')

    @asyncio.coroutine
    def chat(self):
        while True:
            try:
                msg = yield from self.channel.read()
            except:
                print('Unresponsive worker detected')
            if msg == MsgType.PONG:
                self.ping = time.monotonic()
