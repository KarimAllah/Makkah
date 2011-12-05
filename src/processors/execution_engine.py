import logging
import types
from processors.op_codes import simple_opcodes
import threading

INITIAL_IP = 0x0

class SimpleEngine(threading.Thread):
    def __init__(self, name, system_bus):
        # A word is 4-bytes long.
        self.logger = logging.getLogger(name)
        self.name = name
        self.system_bus = system_bus
        self.ip = INITIAL_IP
        self.word_size = 4
        self.op_handlers = {}
        
        local_storage = threading.local()
        # will be used to identify the current executing engine.
        local_storage.engine_id = self.name
        
    def load_opcodes(self, module):
        for attr in dir(module):
            attribute = getattr(module, attr)
            if attr.startswith('op_') and isinstance(attribute, types.FunctionType):
                self.op_handlers[attr[3:]] = attribute
                
    def fetch_next_op(self, ip):
        self.logger.info("Fetching next opcode from address (%s)", ip)
        op = self.system_bus.read(ip)
        return op
        
    def execute(self, op):
        try:
            self.op_handlers[str(op)]()
        except KeyError:
            return False
        
        return True


    def set_ip(self, address):
        self.ip = address
        
    def run(self):
        self.load_opcodes(simple_opcodes)
        while True:
            op = self.fetch_next_op(self.ip)
            if not self.execute(op):
                self.logger.error("Executing invalid opcode (%s). EXITING.", op)
                break
            self.ip = self.ip + self.word_size