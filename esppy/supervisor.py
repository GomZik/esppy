import asyncio
import signal
from esppy.worker import Worker
import socket
from . import web


class Supervisor:
    def __init__(self, args):
        self.loop = asyncio.get_event_loop()
        self.args = args
        self.workers = []
        self.nodes = []
        self.master = None
        self.broadcast_task = None

    def run(self):
        for i in range(self.args.workers):
            self.workers.append(Worker(self.loop))

        if not self.args.disable_nodes:
            if not self.args.slave:
                self.start_broadcast()
            else:
                self.wait_bradcast()

        def stop():
            @asyncio.coroutine
            def _stop():
                print('\nGraceful shutdown')
                tasks = []
                for worker in self.workers:
                    tasks.append(asyncio.Task(worker.kill()))
                if self.broadcast_task is not None:
                    self.broadcast_task.cancel()
                    yield from asyncio.wait([self.broadcast_task])
                yield from asyncio.wait(tasks)
                self.loop.stop()

            asyncio.async(_stop())
            
        if not self.args.no_web:
            self.attach_web_monitoring()

        self.loop.add_signal_handler(signal.SIGINT, stop)
        self.loop.run_forever()

    def wait_bradcast(self):
        print('Waiting for master broadcast')
        broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        broadcast_socket.bind(('', self.args.port))
        self.loop.add_reader(
            broadcast_socket, self.broadcast_received, broadcast_socket)

    def start_broadcast(self):
        broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        broadcast_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        broadcast_socket.bind(('', 0))

        self.broadcast_task = asyncio.Task(self.broadcast(broadcast_socket))

        self.loop.run_until_complete(
            asyncio.start_server(
                self.node_connected, port=self.args.port, loop=self.loop)
        )

    @asyncio.coroutine
    def broadcast(self, sock):
        def _send():
            future = asyncio.Future()

            def _inner():
                try:
                    self.loop.remove_writer(sock)
                    future.set_result(sock.sendto(
                        self.args.cookie.encode('utf-8'),
                        ('<broadcast>', self.args.port)))
                except Exception as e:
                    future.set_exception(e)

            self.loop.add_writer(sock, _inner)
            return future

        while True:
            print('Send broadcast')
            yield from _send()
            yield from asyncio.sleep(15)

    def broadcast_received(self, sock):
        data, addr = sock.recvfrom(1024)
        if data.decode('utf-8') == self.args.cookie:
            ip = addr[0]
            print('Broadcast received', data, addr)
            self.loop.remove_reader(sock)
            asyncio.async(self.connect_to_master(ip))

    @asyncio.coroutine
    def connect_to_master(self, ip):
        reader, writer = yield from asyncio.open_connection(
            host=ip, port=self.args.port, loop=self.loop)
        print('Connected to master node')
        self.nodes.append((reader, writer))
        self.master = (reader, writer)
        asyncio.async(self.handle_node(reader, writer))

    @asyncio.coroutine
    def node_connected(self, reader, writer):
        print('Node connected')
        self.nodes.append((reader, writer))
        asyncio.async(self.handle_node(reader, writer))

    @asyncio.coroutine
    def handle_node(self, reader, writer):
        pass
        
    def attach_web_monitoring(self):
        self.web_monitoring = self.loop.run_until_complete(web.make_server())
