import asyncio
import signal


class ChildProcess:
    pass


class Worker:
    def __init__(self, loop):
        self.loop = loop


class Supervisor:
    def __init__(self, args):
        self.loop = asyncio.get_event_loop()
        self.args = args
        self.workers = []

    def run(self):
        for i in range(self.args.workers):
            self.workers.append(Worker(self.loop))

        signal.add_signal_handler(signal.SIGINT, lambda: self.loop.stop())
        self.loop.run_forever()
