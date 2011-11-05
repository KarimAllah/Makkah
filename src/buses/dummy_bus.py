import logging
from uuid import uuid1
from controllers.interfaces import InterruptConsumerInterface

class InterruptLine():
    def __init__(self, name, irq_number):
        self.logger = logging.getLogger(name)
        self.consumers_list = []
        self.irq_number = irq_number
        self.u_id = str(uuid1())
        
    def set_consumer(self, consumer):
        self.consumers_list.append(consumer)
        
    def trigger(self):
        for consumer in self.consumers_list:
            self.logger.info("Notifying consumer (%s)", consumer.name)
            consumer.trigger_interrupt(self.u_id)
            
    def get_id(self):
        return self.u_id
    
class SimpleBus(InterruptConsumerInterface):
    def __init__(self, name):
        self.name = name
        self.logger = logging.getLogger("SimpleBus")
        self.interrupts_map = {}  # irq_number <-to-> InterruptLine mapping. 
        
    def trigger_interrupt(self, irq_number):
        '''
            controller_name : name of the controller that triggers the interrupt
        '''
        if irq_number not in self.interrupts_map:
            self.logger.warn("No consumers registered for irq_number (%s)", irq_number)
            return
        
        self.logger.info("IRQ number (%s) is triggered", irq_number)
        self.interrupts_map[irq_number].trigger()
    
    def set_interrupt_consumer(self, interrupt_consumer, irq_number):
        try:
            interrupt_line = self.interrupts_map[irq_number]
        except KeyError:
            self.interrupts_map[irq_number] = interrupt_line = InterruptLine(self.name, irq_number)
        
        interrupt_line.set_consumer(interrupt_consumer)
        return interrupt_line.get_id()
    
    def remove_interrupt_consumer(self, interrupt_consumer, irq_number=None):
        raise NotImplementedError()