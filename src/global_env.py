# Set this to the environment that you wish to see globally.
import threading

ENV = {}

# engine_id
THREAD_ENV = threading.local()

STEPPING = False

IMPORTANT_ops = []
IMPORTANT_IPs = []

def jump_to_ipdb(processor):
    import ipdb;ipdb.set_trace()

STEPPING_callacks = [jump_to_ipdb]
IMPORTANT_callbacks = [jump_to_ipdb]

class ComponentNotRegistered(Exception):
    def __init__(self, name):
        Exception.__init__(self)
        self.component_name = name

def get_component(self, name):
        try:
            return ENV[name]
        except KeyError:
            raise ComponentNotRegistered(name)