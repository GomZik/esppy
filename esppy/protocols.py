import enum
import asyncio


EOL_MARKER = '\n'


class MsgType(enum.Enum):
    PING = '/ping'
    PONG = '/pong'


class WorkerProtocol:
    def __init__(self, read, write):
        self._read_transport = read
        self._write_transport = write

    @asyncio.coroutine
    def write(self, data):
        data = (str(data) + EOL_MARKER).encode('utf-8')
        self._write_transport.write(data)
        yield from self._write_transport.drain()

    @asyncio.coroutine
    def read(self):
        data = yield from self._read_transport.readline()
        data = data.decode('utf-8').replace(EOL_MARKER)
        return data

    @asyncio.coroutine
    def ping(self):
        yield from self.write(MsgType.PING)

    @asyncio.coroutine
    def pong(self):
        self.write(MsgType.PONG)
