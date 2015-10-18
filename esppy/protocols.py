import asyncio


EOL_MARKER = '\n'


class MsgType:
    PING = '/ping'
    PONG = '/pong'


class WorkerProtocol(asyncio.Protocol):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._buffer = []
        self._writer = self._feed_data()
        self._callbacks = []
        next(self._writer)

    def _feed_data(self):
        while True:
            chunk = yield
            if chunk:
                data = chunk.decode('utf-8').split(EOL_MARKER)
                data = list(filter(None, data))
                self._buffer += data

                while self._callbacks:
                    if self._buffer:
                        msg = self._buffer[0]
                        self._buffer = self._buffer[1:]
                        callback = self._callbacks[0]
                        self._callbacks = self._callbacks[1:]
                        callback(msg)
                    else:
                        break

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        self._writer.send(data)

    def write(self, data):
        data = (str(data) + EOL_MARKER).encode('utf-8')
        self.transport.write(data)

    def _make_callback(self, future):
        def _callback(data):
            future.set_result(data)

        return _callback

    def read(self):
        future = asyncio.Future()

        if self._buffer:
            msg = self._buffer[0]
            self._buffer = self._buffer[1:]
            future.set_result(msg)
        else:
            self._callbacks.append(self._make_callback(future))

        return future

    def ping(self):
        self.write(MsgType.PING)

    def pong(self):
        self.write(MsgType.PONG)

    def close(self):
        self.transport.close()
