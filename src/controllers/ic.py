import logging
from controllers.interfaces import InterruptConsumerInterface,\
    InterruptProducerInterface
from uuid import uuid1


class SimpleInterruptController(InterruptConsumerInterface, InterruptProducerInterface):
    def __init__(self, name):
        InterruptConsumerInterface.__init__(self, name)
        self.logger = logging.getLogger(name)
        
        self.interrupts_map = {} # mapping unique_id <-to-> interrupt numbers.
        
        # Anything that isn't in this list is implicitly assumed to be in irq_producers list.
        # list of irq_numbers
        self.fiq_producers = [] 
        
        self.mask_all = True
        self.masked_irqs = []
        
        self.current_priority = 9 # We've 10 levels from (0 =>> 9)
        
        self.consumers_map = {0:[], 1:[]}
        
        self.interrupts_ids = {0: str(uuid1()), 1:str(uuid1())}
    
    def enable_all(self):
        self.mask_all = False
        self.masked_irqs = []
    
    def mask_all(self):
        self.mask_all = True
        
    def mask_irq(self, irq_num):
        if irq_num in self.masked_irqs:
            self.logger.info("Interrupt number (%s) was already masked", irq_num)
            return
        
        self.logger.info("Masking interrupt number (%s)", irq_num)
        self.masked_irqs.append(irq_num)
        
    def enable_irq(self, irq_num):
        if irq_num not in self.masked_irqs:
            self.logger.info("Interrupt number (%s) wasn't masked", irq_num)
            return
        
        self.logger.info("Enabling interrupt number (%s)", irq_num)
        self.masked_irqs.remove(irq_num)
        
    def set_priority(self, priority):
        self.current_priority = priority

    def trigger_interrupt(self, unique_id):
        if unique_id not in self.interrupts_map:
            self.logger.warn("No interrupt mapped to this interrupt line (%s)", unique_id)
            return
        
        if self.mask_all:
            self.logger.info("All interrupts are masked")
            return
        
        irq_number = self.interrupts_map[unique_id]
        
        if irq_number in self.masked_irqs:
            self.logger.info("Interrupt number (%s) is masked", irq_number)
            return
        
        if (irq_number / 10) > self.current_priority:
            self.logger.info("Interrupt number (%s) is ignored, current priority level (%s)", irq_number, self.current_priority)
        
        if irq_number in self.fiq_producers:
            self.logger.info("Triggering a fast interrupt (FIQ)")
            for consumer in self.consumers_map[1]:
                consumer.trigger_interrupt(self.interrupts_ids[1])
        else:
            self.logger.info("Triggering a normal interrupt (IRQ)")
            for consumer in self.consumers_map[0]:
                consumer.trigger_interrupt(self.interrupts_ids[0])

    def set_interrupt_consumer(self, interrupt_consumer, irq_number):
        # 0 => IRQ
        # 1 => FIQ
        if irq_number not in [0,1]:
            self.logger.warn("Only interrupt number 0 or 1 are available")
            return
        
        if interrupt_consumer in self.consumers_map[irq_number]:
            self.logger.warn("Interrupt Consumer (%s) is already registered for this interrupt number (%s)", interrupt_consumer.name, irq_number)
        
        self.consumers_map[irq_number].append(interrupt_consumer)
        
    def remove_interrupt_consumer(self, interrupt_consumer, irq_number=None):
        if irq_number not in [0,1]:
            self.logger.warn("Only interrupt number 0 or 1 are available")
            return
        
        if irq_number:
            irq_numbers = [irq_number]
        else:
            irq_numbers = [0,1]
        
        removed = False
        for irq_number in irq_numbers:
            if interrupt_consumer in self.consumers_map[irq_number]:
                removed = True
                self.consumers_map[irq_number].remove(interrupt_consumer)
                
        if not removed:
            self.logger.warn("Couldn't find any registered consumer called (%s)", interrupt_consumer.name)