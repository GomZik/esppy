import importlib


class Pid:
    def __init__(self, module_name, function_name, args, kwargs):
        module = importlib.import_module(module_name)
        func = getattr(module, function_name)
        func(*args, **kwargs)

    def __mod__(self, data):
        print('Send to {} data {}'.format(str(self), str(data)))

    def __str__(self):
        return '<PID nodename.worker.id>'
