from controllers.interfaces import AbstractBankedAddressableObject,\
    AbstractInterruptConsumer, AbstractInterruptProducer
from controllers.memory import SimpleMemory

class ARMGenericInterruptController(AbstractBankedAddressableObject, AbstractInterruptConsumer, AbstractInterruptProducer):
    '''
        SPI : Shared peripheral Interrupts.
        PPI : Private peripheral Interrupts.
        SGI : Software Generated Interrupts.
    '''
    ICDISER = 0x0 # Interrupt set-enable Register
    ICDICER = 0x0 # Interrupt clear-enable Register
    
    ICDISPR = 0x0 # Interrupt set-pending Register
    ICDICPR = 0x0 # Interrupt clear-pending Register
    
    ICDISPR = 0x0 # Interrupt status-pending register
    ICDICPR = 0x0 # interrupt status-pending register
    
    ICDABR  = 0x0 # active bit register
    
    ICDSGIR = 0x0 # software generated interrupt register
    
    ICCIAR = 0x0 # 
    
    ICDIPR = 0x0 # interrupt priority registers
    
    ICCPMR = 0x0 # interrupt priority mask register
    
    ICCBPR = 0x0 # binary point register
    
    ICCRPR = 0x0 # running priority register


    INACTIVE    = 0x0
    PENDING     = 0x1
    ACTIVE      = 0X2
    APENDING    = 0x3
    
    trigger_transitions = {INACTIVE: PENDING, PENDING: PENDING, ACTIVE: APENDING, APENDING: APENDING}
    
    def __init__(self):
        AbstractBankedAddressableObject.__init__()
        self.regf_map = {} # register <-> function map.
        self.memory = SimpleMemory("arm_gic register memory", )
        
        
        self.irq_state_machine = {}
    
    def acknowldge(self, source_id, target_irq):
        pass

    def interrupt_triggered(self, returned_irq):
        state = self.irq_state_machine[returned_irq]
        self.irq_state_machine[returned_irq] = self.trigger_transitions[state]
        #FIXME:
        
    