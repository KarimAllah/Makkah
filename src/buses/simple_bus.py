from controllers.interfaces import AbstractInterruptProducer,\
    AbstractInterruptConsumer, AbstractAddressableObject

class SimpleBus(AbstractInterruptProducer, AbstractInterruptConsumer, AbstractAddressableObject):
    '''
        Simple Bus implementation, used as a base class for all other more complicated buses.
    '''
    def __init__(self, name):
        AbstractInterruptConsumer.__init__(self, name)
        AbstractInterruptProducer.__init__(self, name)
        AbstractAddressableObject.__init__(self)
    
    # Interrupt management.
    def interrupt_triggered(self, returned_irq):
        super(SimpleBus, self).trigger_interrupt(returned_irq)