# Set this to the environment that you wish to see globally.
import threading
from threading import Event

ENV = {}

dbg_breakpoint_hit = False
dbg_event = Event()
dbg_event.set() # single-instruction stepping is OFF by default

# engine_id
THREAD_ENV = threading.local()

STEPPING = False
GDB_ops = []
GDB_IPs = []

class ComponentNotRegistered(Exception):
    def __init__(self, name):
        Exception.__init__(self)
        self.component_name = name

def get_component(self, name):
        try:
            return ENV[name]
        except KeyError:
            raise ComponentNotRegistered(name)

main_cpu = None

# Stoppable components
soc = None
dbg = None
char_devices = []

def stop_all():
    if soc:
        soc.stop()

    if dbg:
        dbg.stop()
        
    for char_device in char_devices:
        char_device.stop()

def get_info():
    info = soc.get_info()
    return info