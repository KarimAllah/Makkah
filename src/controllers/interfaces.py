from uuid import uuid1

# Defines an object that is capable of consuming interrupts from a 
class InterruptConsumerInterface(object):
    def __init__(self, name):
        self.name = name
    
    def trigger_interrupt(self, unique_id):
        raise NotImplementedError()
    
class InterruptProducerInterface(object):
    def set_interrupt_consumer(self, interrupt_consumer, irq_number):
        return str(uuid1())
        raise NotImplementedError()
    
    def remove_interrupt_consumer(self, interrupt_consumer, irq_number=None):
        raise NotImplementedError()