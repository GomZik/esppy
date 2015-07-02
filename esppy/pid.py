import importlib


class Pid:
    def __init__(self, module_name, function_name, args, kwargs):
        module = importlib.import_module(module_name)
        func = getattr(module, function_name)
        func(*args, **kwargs)
