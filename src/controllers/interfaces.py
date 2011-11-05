import logging

class AbstractInterruptProducer(object):
    def __init__(self, name):
        self.name = name
        self.logger = logging.getLogger(name)
        
        # {irq : [(id, consumer), ..., ...]}
        self.irq_consumers_map = {}
        
    def register_interrupt_consumer(self, interrupt_consumer, irq_number, returned_irq):
        if irq_number not in self.irq_consumers_map:
            self.irq_consumers_map[irq_number] = []
        else:
            consumers = [consumer for _, consumer in self.irq_consumers_map[irq_number]]
            
            if interrupt_consumer in consumers:
                for entry in self.irq_consumers_map[irq_number]:
                    if entry[0] == returned_irq and entry[1] == interrupt_consumer:
                        self.logger.warn("Interrupt Consumer (%s) is already registered for this interrupt number (%s) with the same returned IRQ (%s)", interrupt_consumer.name, irq_number, returned_irq)
                        return
            
        self.irq_consumers_map[irq_number].append([returned_irq, interrupt_consumer])
    
    def unregister_interrupt_consumer(self, interrupt_consumer, irq_number=None):
        if irq_number:
            irq_numbers = [irq_number]
        else:
            irq_numbers = self.irq_consumers_map.keys()
        
        removed = False
        for irq_number in irq_numbers:
            for entry in self.irq_consumers_map[irq_number]:
                if entry[1] == interrupt_consumer:
                    self.irq_consumers_map[irq_number].remove(entry)
                    removed = True

            if not self.irq_consumers_map[irq_number]:
                del self.irq_consumers_map[irq_number]
                
        if not removed:
            self.logger.warn("Couldn't find any registered consumer called (%s)", interrupt_consumer.name)
            
    def trigger_interrupt(self, irq_number):
        if irq_number not in self.irq_consumers_map:
            self.logger.warn("IRQ number (%s) has no consumers", irq_number)
            return
        
        for returned_irq, consumer in self.irq_consumers_map[irq_number]:
            consumer.interrupt_triggered(returned_irq)

class AbstractInterruptConsumer(object):
    def __init__(self, name):
        self.name = name
        self.logger = logging.getLogger(name)
    
    def attach_to(self, producer, irq_number, returned_irq):
        producer.register_interrupt_consumer(self, irq_number, returned_irq)
    
    def deattach_from(self, producer, irq_number=None):
        producer.unregister_interrupt_consumer(self, irq_number)
    
    #override
    def interrupt_triggered(self, returned_irq):
        self.logger.info("Interrupt number (%s) was triggered", returned_irq)