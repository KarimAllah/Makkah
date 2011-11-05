import logging
from controllers.interfaces import AbstractInterruptConsumer,\
    AbstractInterruptProducer

class SimpleInterruptController(AbstractInterruptConsumer, AbstractInterruptProducer):
    def __init__(self, name):
        AbstractInterruptConsumer.__init__(self, name)
        AbstractInterruptProducer.__init__(self, name)
        
        self.logger = logging.getLogger(name)
        
        # Anything that isn't in this list is implicitly assumed to be in irq_producers list.
        # list of irq_numbers
        self.fiq_producers = [] 
        
        self.mask_all = True
        self.masked_irqs = []
        
        self.current_priority = 9 # We've 10 levels from (0 =>> 9)    
    
    def enable_all(self):
        self.mask_all = False
    
    def mask_all(self):
        self.mask_all = True
        
    def mask_irq(self, irq_num):
        if irq_num in self.masked_irqs:
            self.logger.info("Interrupt number (%s) was already masked", irq_num)
            return
        
        self.logger.info("Masking interrupt number (%s)", irq_num)
        self.masked_irqs.append(irq_num)
        
    def unmask_irq(self, irq_num):
        if irq_num not in self.masked_irqs:
            self.logger.info("Interrupt number (%s) wasn't masked", irq_num)
            return
        
        self.logger.info("Enabling interrupt number (%s)", irq_num)
        self.masked_irqs.remove(irq_num)
        
    def set_priority(self, priority):
        self.current_priority = priority
    
    # Interrupt consumer routines.
    def interrupt_triggered(self, unique_id):
        try:
            irq_number = super(SimpleInterruptController, self).resolve_id(unique_id)
        except KeyError:
            self.logger.warn("No interrupt mapped to this interrupt line (%s)", unique_id)
            return
        
        if self.mask_all:
            self.logger.info("Interrupts are masked")
        elif irq_number in self.masked_irqs:
            self.logger.info("Interrupt number (%s) is masked", irq_number)
        elif (irq_number / 10) > self.current_priority:
            self.logger.info("Interrupt number (%s) is ignored, current priority level (%s)", irq_number, self.current_priority)
        else:
            if irq_number in self.fiq_producers:
                self.logger.info("Triggering a fast interrupt (FIQ)")
                super(SimpleInterruptController, self).trigger_interrupt(1)
            else:
                self.logger.info("Triggering a normal interrupt (IRQ)")
                super(SimpleInterruptController, self).trigger_interrupt(0)

    # Interrupt producer routines.
    def register_interrupt_consumer(self, interrupt_consumer, irq_number, returned_irq):
        # 0 => IRQ
        # 1 => FIQ
        if irq_number not in [0,1]:
            self.logger.warn("Only interrupt number 0 or 1 are available")
            return
        
        self._register_interrupt_consumer(interrupt_consumer, irq_number, returned_irq)
        
    def unregister_interrupt_consumer(self, interrupt_consumer, irq_number=None):
        self._unregister_interrupt_consumer(interrupt_consumer, irq_number)
        