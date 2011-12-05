import logging
import threading
import global_env
from ctypes import c_uint32, c_uint64, c_int32
from controllers.interfaces import AbstractInterruptConsumer

INITIAL_IP = c_uint32(0x0)
CPSR_RESET = c_uint32(0x0)

class InvalidInstructionOpCode(Exception):
    pass

class NotImplementedOpCode(Exception):
    pass

class WrongExecutionFlow(Exception):
    pass

class Unpredictable(Exception):
    pass

class AccessViolation(Exception):
    pass

class ARMCortexA9(threading.Thread, AbstractInterruptConsumer):
    # Masks
    
    # CPSR
    PROCESSOR_MODE          = 0x0000001F
    PROCESSOR_THUMB         = 0x00000020
    PROCESSOR_ASYNC_DISABLE = 0x00000100
    PROCESSOR_IRQ_DISABLE   = 0x00000080
    PROCESSOR_FIQ_DISABLE   = 0x00000040
    PROCESSOR_ENDIANESS     = 0x00000200
    PROCESSOR_IT_0_1        = 0x06000000
    PROCESSOR_IT_2_7        = 0x0000FC00
    PROCESSOR_IT            = 0x0600FC00
    PROCESSOR_GE            = 0x00F00000  # Greater or equal
    PROCESSOR_J             = 0x01000000 # Jazelle
    PROCESSOR_Q             = 0x08000000
    PROCESSOR_V             = 0x10000000 # Overflow
    PROCESSOR_C             = 0x20000000 # Carry
    PROCESSOR_Z             = 0x40000000 # Zero
    PROCESSOR_N             = 0x80000000 # Negative
    
    # CONDITION
    CONDITION_MASK          = 0xF0000000
    CONDITION_MASK_SHIFT    = 28
    

    # LDR
    LDR_IMMEDIATE_OP_MASK   = 0x0E500000
    LDR_IMMEDIATE_OP        = 0x04100000
    LDR_IMMEDIATE_IMM       = 0x00000FFF
    LDR_IMMEDIATE_RT        = 0x0000F000
    LDR_IMMEDIATE_RT_SHIFT  = 12
    LDR_IMMEDIATE_RN        = 0x000F0000
    LDR_IMMEDIATE_RN_SHIFT  = 16
    LDR_IMMEDIATE_P         = 0x01000000
    LDR_IMMEDIATE_W         = 0x00800000
    LDR_IMMEDIATE_U         = 0x00200000
    
    LDR_LITERAL_OP_MASK     = 0x0F7F0000
    LDR_LITERAL_OP          = 0x051F0000
    LDR_LITERAL_IMM         = 0x00000FFF
    LDR_LITERAL_RT          = 0x0000F000
    LDR_LITERAL_RT_SHIT     = 12
    LDR_LITERAL_U           = 0x00800000
    
    # STR
    STR_REGISTER_OP_MASK    = 0x06500010
    STR_REGISTER_OP         = 0x06000000
    STR_REGISTER_P          = 0x01000000
    STR_REGISTER_U          = 0x00800000
    STR_REGISTER_W          = 0x00200000
    STR_REGISTER_TYPE       = 0x00000060
    STR_REGISTER_TYPE_SHIFT = 5
    STR_REGISTER_RM         = 0x0000000F
    STR_REGISTER_IMM        = 0x00000F80
    STR_REGISTER_IMM_SHIFT  = 7
    STR_REGISTER_RT         = 0x0000F000
    STR_REGISTER_RT_SHIFT   = 12
    STR_REGISTER_RN         = 0x000F0000
    STR_REGISTER_RN_SHIFT   = 16
    
    STR_IMMEDIATE_OP_MASK   = 0x0E500000
    STR_IMMEDIATE_OP        = 0x04000000
    STR_IMMEDIATE_P         = 0x01000000
    STR_IMMEDIATE_U         = 0x00800000
    STR_IMMEDIATE_W         = 0x00200000
    STR_IMMEDIATE_RN        = 0x000F0000
    STR_IMMEDIATE_RN_SHIFT  = 16
    STR_IMMEDIATE_RT        = 0x0000F000
    STR_IMMEDIATE_RT_SHIFT  = 12
    STR_IMMEDIATE_IMM       = 0x00000FFF
    
    # Branch
    B_OP_MASK               = 0x0F000000
    B_OP                    = 0x0A000000
    B_IMM                   = 0x00FFFFFF
    
    BL_OP_MASK              = 0x0F000000
    BL_OP                   = 0x0B000000
    BL_IMM                  = 0x00FFFFFF
    
    # ADD
    ADD_IMMEDIATE_OP_MASK   = 0x0FE00000
    ADD_IMMEDIATE_OP        = 0x02800000
    ADD_IMMEDIATE_IMM       = 0x00000FFF
    ADD_IMMEDIATE_RD        = 0x0000F000
    ADD_IMMEDIATE_RD_SHIFT  = 12
    ADD_IMMEDIATE_RN        = 0x000F0000
    ADD_IMMEDIATE_RN_SHIFT  = 16
    ADD_IMMEDIATE_S         = 0x00100000
    
    ADD_REGISTER_OP_MASK    = 0x0FE00010
    ADD_REGISTER_OP         = 0x00800000
    ADD_REGISTER_S          = 0x00100000
    ADD_REGISTER_RN         = 0x000F0000
    ADD_REGISTER_RN_SHIFT   = 16
    ADD_REGISTER_RD         = 0x0000F000
    ADD_REGISTER_RD_SHIFT   = 12
    ADD_REGISTER_IMM        = 0x00000F80
    ADD_REGISTER_IMM_SHIFT  = 7
    ADD_REGISTER_TYPE       = 0x00000060
    ADD_REGISTER_TYPE_SHIFT = 5
    ADD_REGISTER_RM         = 0x0000000F
    
    # SUB
    SUB_REGISTER_OP_MASK    = 0x0FE00010
    SUB_REGISTER_OP         = 0x00400000
    SUB_REGISTER_IMM        = 0x00000F80
    SUB_REGISTER_IMM_SHIFT  = 7
    SUB_REGISTER_RN         = 0x000F0000
    SUB_REGISTER_RN_SHIFT   = 16
    SUB_REGISTER_RD         = 0x0000F000
    SUB_REGISTER_RD_SHIFT   = 12
    SUB_REGISTER_TYPE       = 0x00000060
    SUB_REGISTER_TYPE_SHIFT = 5
    SUB_REGISTER_RM         = 0x0000000F
    SUB_REGISTER_S          = 0x00100000
    
    # Bit
    BFC_OP_MASK             = 0x0FE0007F
    BFC_OP                  = 0x07C0001F
    BFC_MSB                 = 0x001F0000
    BFC_MSB_SHIFT           = 16
    BFC_LSB                 = 0x00000F80
    BFC_LSB_SHIFT           = 7
    BFC_RD                  = 0x0000F000
    BFC_RD_SHIFT            = 12
    
    # CMP
    CMP_REGISTER_OP_MASK    = 0x0FF0FF10
    CMP_REGISTER_OP         = 0x01500000
    CMP_REGISTER_RN         = 0x000F0000
    CMP_REGISTER_RN_SHIFT   = 16
    CMP_REGISTER_IMM        = 0x00000F80
    CMP_REGISTER_IMM_SHIFT  = 7
    CMP_REGISTER_TYPE       = 0x00000060
    CMP_REGISTER_TYPE_SHIFT = 5
    CMP_REGISTER_RM         = 0x0000000F
    
    # MOV
    MOV_IMMEDIATE_OP1_MASK  = 0x0FEF0000
    MOV_IMMEDIATE_OP1       = 0x03A00000
    MOV_IMMEDIATE_OP1_S     = 0x00100000
    MOV_IMMEDIATE_OP1_RD    = 0x0000F000
    MOV_IMMEDIATE_OP1_RD_SHIFT   = 12
    MOV_IMMEDIATE_OP1_IMM   = 0x00000FFF
    
    MOV_IMMEDIATE_OP2_MASK  = 0x0FF00000
    MOV_IMMEDIATE_OP2       = 0x03000000
    MOV_IMMEDIATE_OP2_IMM   = 0x000F0000
    MOV_IMMEDIATE_OP2_IMM_SHIFT = 16
    
    MOV_REGISTER_OP_MASK    = 0x0FEF0FF0
    MOV_REGISTER_OP         = 0x01A00000
    MOV_REGISTER_RM         = 0x0000000F
    MOV_REGISTER_RD         = 0x0000F000
    MOV_REGISTER_RD_SHIFT   = 12
    MOV_REGISTER_S          = 0x00100000
    
    # Logical Shift
    LSL_IMMEDIATE_OP_MASK   = 0x0FEF0070
    LSL_IMMEDIATE_OP        = 0x01A00000
    LSL_IMMEDIATE_RD        = 0x0000F000
    LSL_IMMEDIATE_RD_SHIFT  = 12
    LSL_IMMEDIATE_IMM       = 0x00000F80
    LSL_IMMEDIATE_IMM_SHIFT = 7
    LSL_IMMEDIATE_RM        = 0x0000000F
    LSL_IMMEDIATE_S         = 0x00100000
    
    LSR_IMMEDIATE_OP_MASK   = 0x0FEF0070
    LSR_IMMEDIATE_OP        = 0x01A00020
    LSR_IMMEDIATE_RD        = 0x0000F000
    LSR_IMMEDIATE_RD_SHIFT  = 12
    LSR_IMMEDIATE_IMM       = 0x00000F80
    LSR_IMMEDIATE_IMM_SHIFT = 7
    LSR_IMMEDIATE_RM        = 0x0000000F
    LSR_IMMEDIATE_S         = 0x00100000
    
    # ORR
    ORR_IMMEDIATE_OP_MASK   = 0x0FE00000
    ORR_IMMEDIATE_OP        = 0x03800000
    ORR_IMMEDIATE_IMM       = 0x00000FFF
    ORR_IMMEDIATE_RD        = 0x0000F000
    ORR_IMMEDIATE_RD_SHIFT  = 12
    ORR_IMMEDIATE_RN        = 0x000F0000
    ORR_IMMEDIATE_RN_SHIFT  = 16
    ORR_IMMEDIATE_S         = 0x00100000
    
    ORR_REGISTER_OP_MASK    = 0x0FE00010
    ORR_REGISTER_OP         = 0x01800000
    ORR_REGISTER_IMM        = 0x00000F80
    ORR_REGISTER_IMM_SHIFT  = 7
    ORR_REGISTER_RM         = 0x0000000F
    ORR_REGISTER_RN         = 0x000F0000
    ORR_REGISTER_RN_SHIFT   = 16
    ORR_REGISTER_RD         = 0x0000F000
    ORR_REGISTER_RD_SHIFT   = 12
    ORR_REGISTER_TYPE       = 0x00000060
    ORR_REGISTER_TYPE_SHIFT = 5
    ORR_REGISTER_S          = 0x00100000
    
    SVC_OP_MASK             = 0x0F000000
    SVC_OP                  = 0x0F000000
    SVC_IMM                 = 0x00FFFFFF
    
    MCR_OP_MASK             = 0x0E100010
    MCR_OP                  = 0x0E000010
    MCR_OPC1                = 0x00E00000
    MCR_OPC1_SHIFT          = 21
    MCR_CRN                 = 0x000F0000
    MCR_CRN_SHIFT           = 16
    MCR_RT                  = 0x0000F000
    MCR_RT_SHIFT            = 12
    MCR_COPROC              = 0x00000F00
    MCR_COPROC_SHIFT        = 8
    MCR_OPC2                = 0x000000E0
    MCR_OPC2_SHIFT          = 5
    MCR_CRM                 = 0x0000000F
    
    
    def __init__(self, name, system_bus, security_extensions=True):
        threading.Thread.__init__(self)
        # A word is 4-bytes long.
        self.logger = logging.getLogger(name)
        self.name = name
        self.system_bus = system_bus
        self.word_size = 4
        self.op_handlers = {}
        self.received_interrupts = {}
        global_env.THREAD_ENV.engine_id = name
        self.HaveSecurityExt = security_extensions
        
        self.init_registers()
        self.init_interrupts()
                
    def fetch_next_op(self):
        self.logger.info("Fetching next opcode from address (%s)", self.ip.value)
        op = self.system_bus.read(self.ip.value)
        return op.value
    
    def init_registers(self):
        self.cpsr   = CPSR_RESET
        self.ip     = INITIAL_IP
        
        self.registers = {}
        
        self.processor_modes = processor_modes = {
                                                   "user"       : 0x10,
                                                   "fiq"        : 0x11,
                                                   "irq"        : 0x12,
                                                   "supervisor" : 0x13,
                                                   "monitor"    : 0x16,
                                                   "abort"      : 0x17,
                                                   "undefined"  : 0x1b,
                                                   "sys"        : 0x1f
                                                 }
        
        user_mode = processor_modes['user']
        # User mode registers.
        self.registers[user_mode] = []
        for _ in range(15):
            self.registers[user_mode].append(c_uint32())
        
        # System mode registers.
        self.registers[processor_modes['sys']] = []
        for index in range(15):
            self.registers[processor_modes['sys']].append(self.registers[user_mode][index])
        
        modes = ['supervisor', 'monitor', 'abort', 'undefined', 'irq']
        for mode in modes:
            mode = processor_modes[mode]
            self.registers[mode] = []
            for index in range(13):
                self.registers[mode].append(self.registers[user_mode][index])
                
            self.registers[mode].append(c_uint32()) # sp = r13
            self.registers[mode].append(c_uint32()) # lr = r14

        # FIQ registers.
        mode = processor_modes['fiq']
        self.registers[mode] = []
        for index in range(8):
            self.registers[mode].append(self.registers[user_mode][index])
            
        self.registers[mode].append(c_uint32()) # r8
        self.registers[mode].append(c_uint32()) # r9
        self.registers[mode].append(c_uint32()) # r10
        self.registers[mode].append(c_uint32()) # r11
        self.registers[mode].append(c_uint32()) # r12
        self.registers[mode].append(c_uint32()) # r13
        self.registers[mode].append(c_uint32()) # r14
        
        self.cpsr.value |= processor_modes['supervisor']
        
        # Adding spsr
        modes = ['supervisor', 'monitor', 'abort', 'undefined', 'irq', 'fiq']
        self.spsr_registers = {}
        for mode in modes:
            mode = processor_modes[mode]
            self.spsr_registers[mode] = c_uint32()
            
        # CP15 Registers
        self.cp15_registers = {}
        def init_cp15_register(crn, opc1, crm, opc2, secure, value):
            bank = 0 if secure else 1
            try:
                self.cp15_registers[crn][opc1][crm][opc2][bank] = value
            except:
                try:
                    self.cp15_registers[crn][opc1][crm][opc2] = {bank: value}
                except:
                    try:
                        self.cp15_registers[crn][opc1][crm] = {opc2 : {bank: value}}
                    except:
                        try:
                            self.cp15_registers[crn][opc1] = {crm: {opc2: {bank: value}}}
                        except:
                            self.cp15_registers[crn] = {opc1: {crm: {opc2: {bank: value}}}}

        # crn, opc1, crm, opc2, bank(0 => secure, 1 => non-secure)
        

        #self.cp15_registers[12] = {0: {0: {0: {0 : c_uint32()}}}} # VBAR ( secure )
        #self.cp15_registers[12][0][0][0][1] = c_uint32() # VBAR ( non-secure )
        #self.cp15_registers[12][0][0][1][0] = c_uint32() # MVBAR ( secure )
        #self.cp15_registers[12][0][1][0][0] = c_uint32() # ISR ( secure )
        #self.cp15_registers[12][0][1][0][1] = c_uint32() # ISR ( non-secure )
        #self.cp15_registers[1][0][0][0][0] = c_uint32() # SCTLR ( secure )
        #self.cp15_registers[1][0][1][0][0] = c_uint32() # SCR ( secure )
        #self.cp15_registers[1][0][0][0][1] = c_uint32() # SCTLR ( non-secure )
        
        
        init_cp15_register(12, 0, 0, 0, True, c_uint32()) # VBAR ( secure )
        init_cp15_register(12, 0, 0, 0, False, c_uint32()) # VBAR ( non-secure )
        init_cp15_register(12, 0, 0, 1, True, c_uint32()) # MVBAR ( secure )
        init_cp15_register(12, 0, 1, 0, True, c_uint32()) # ISR ( secure )
        init_cp15_register(12, 0, 1, 0, False, c_uint32()) # ISR ( non-secure )
        init_cp15_register(1, 0, 0, 0, True, c_uint32()) # SCTLR ( secure )
        init_cp15_register(1, 0, 0, 0, False, c_uint32()) # SCR ( secure )
        init_cp15_register(1, 0, 1, 0, True, c_uint32()) # SCTLR ( non-secure )
        
        
    
    def init_interrupts(self):
        # undefined instruction    0x0
        # secure monitor call      0x1
        # supervisor call          0x2
        # prefetch abort           0x3
        # data abort               0x4
        # irq                      0x5
        # fiq                      0x6
        self.exception_offsets = {
                    0x0: (4, 2),
                    0x1: (4, 4),
                    0x2: (4, 2),
                    0x3: (4, 4),
                    0x4: (8, 8),
                    0x5: (4, 4),
                    0x6: (4, 4)
                }
        
        self.interrupt_offset_map = {
                    0x0: 0x04,
                    0x1: 0x08,
                    0x2: 0x08,
                    0x3: 0x0C,
                    0x4: 0x10,
                    0x5: 0x18,
                    0x6: 0x1C
                }
        
    def register_read(self, register_index):
        return self.registers[self.cpsr.value & self.PROCESSOR_MODE][register_index] 

    def register_write(self, register_index, reg):
        register = self.registers[self.cpsr.value & self.PROCESSOR_MODE][register_index]
        register.value = reg.value

    IRQ_UNDEFINED   = 0x0
    IRQ_SMC         = 0x1
    IRQ_SVC         = 0x2
    IRQ_PREFETCH_ABORT = 0x3
    IRQ_DATA_ABORT  = 0x4
    IRQ_IRQ         = 0x5
    IRQ_FIQ         = 0x6
    def interrupt_triggered(self, returned_irq):
        self.received_interrupts[returned_irq] = True 
    
    def _TakeException(self):
        interrupt_found = False
        for interrupt, value in self.received_interrupts.items():
            if value:
                # Should we clear the interrupt ?
                #self.received_interrupts[interrupt] = False
                interrupt_found = True
                break
        
        if not interrupt_found:
            return
        
        # 1- save return value to lr
        thumb = self.cpsr.value & self.PROCESSOR_THUMB
        offset = self.exception_offsets[interrupt][1 if thumb else 0]
        lr = self.ip.value + offset

        # 2- update cpsr:
        new_cpsr = self.cpsr.value
        A, F, I = 0, 0, 0 # This means it's unchanged
        MODE = self.cpsr.value & self.PROCESSOR_MODE # Any dummy initial value
        
        scr = self._SCR().value
        secure = ((scr & self.SCR_NS) == 0)
        ea = scr & self.SCR_EA
        irq = scr & self.SCR_IRQ
        fiq = scr & self.SCR_FIQ
        aw = scr & self.SCR_AW
        fw = scr & self.SCR_FW
        
        if interrupt == 0x1:
            # SMC
            A, F, MODE = 1, 1, self.processor_modes['monitor']
        elif interrupt == 0x2:
            MODE = self.processor_modes['supervisor']
        elif interrupt == 0x3 or interrupt == 0x4:
            # Abort
            if secure:
                A, MODE = 1, self.processor_modes['abort']
                if ea:
                    F, MODE = 1, self.processor_modes['monitor']
            else:
                MODE = self.processor_modes['monitor']
                if ea:
                    A, F = 1, 1
                else:
                    MODE = self.processor_modes['abort']
                    if aw:
                        A = 1 
        elif interrupt == 0x5:
            # IRQ
            if secure:
                A, MODE = 1, self.processor_modes['irq']
                if irq:
                    F, MODE = 1, 1, self.processor_modes['monitor'] 
            else:
                MODE = self.processor_modes['irq']
                if irq:
                    A, F, MODE = 1, 1, 1, self.processor_modes['monitor']
                else:
                    if aw:
                        A = 1
        elif interrupt == 0x6:
            # FIQ
            if secure:
                A, F, MODE = 1, 1, self.processor_modes['fiq']
                if fiq:
                    MODE = 1, 1, self.processor_modes['monitor']
            else:
                if fiq:
                    A, F, MODE = 1, 1, self.processor_modes['monitor']
                else:
                    if aw:
                        MODE = self.processor_modes['monitor']
                        A = 1
                        if fw:
                            F = 1, 1
                    else:
                        if fw:
                            F = 1
        
        # disable certain interrupts
        new_cpsr |= (
                     (A and self.PROCESSOR_ASYNC_DISABLE)|
                     (I and self.PROCESSOR_IRQ_DISABLE)|
                     (F and self.PROCESSOR_FIQ_DISABLE)
                    )
        
        # new mode
        new_cpsr &= (~self.PROCESSOR_MODE)
        new_cpsr |= MODE
        
        # instruction set
        sctlr = self._SCTLR().value
        te = sctlr & self.SCTLR_TE
        new_cpsr &= (~self.PROCESSOR_THUMB)
        new_cpsr |= te and self.PROCESSOR_THUMB
        
        # endianness
        ee = sctlr & self.SCTLR_EE
        new_cpsr &= (~self.PROCESSOR_ENDIANESS)
        new_cpsr |= ee and self.PROCESSOR_ENDIANESS
        
        # it[7:0] = 0
        new_cpsr &= (~self.PROCESSOR_IT)
        
        # 5- Save spsr
        self.spsr_registers[MODE].value = self.cpsr.value
        
        # set lr
        self.registers[MODE][14] = lr
        
        # setting the new cpsr
        self.cpsr.value = new_cpsr 
        
        # 6- set ip to the appropriate value.
        normal_vectors = ((sctlr & self.SCTLR_V) == 0)
        
        exception_base_address = 0xFFFF0000
        if self._IsMonitorMode():
            exception_base_address = self._MVBAR().value
        elif normal_vectors:
            exception_base_address = self._VBAR().value
            
        offset = self.interrupt_offset_map[interrupt]
        ip = exception_base_address + offset
        self.set_ip(c_uint32(ip))

    # TODO Use later
    def _IsSecurityExtImplemented(self):
        return True

    def _TakeSVCException(self):
        thumb = self.cpsr.value & self.PROCESSOR_THUMB
        ip = self.get_ip()
        new_lr_value = (ip - 2) if thumb else (ip - 4)
        new_spcr = self.cpsr.value
    
    
    
    # Data Processing instructions mask
    DATA_PROCESSING_INS_MASK    = 0x0C000000
    DATA_PROCESSING_INS         = 0x00000000
    
    #
    LOAD_STORE_INS_MASK         = 0x0C000000
    LOAD_STORE_INS              = 0x04000000
    
    #
    MEDIA_INS_MASK              = 0x0E000010
    MEDIA_INS                   = 0x06000010
    
    #
    BRANCH_INS_MASK             = 0x0C000000
    BRANCH_INS                  = 0x08000000
    
    #
    SVC_COPROC_INS_MASK         = 0x0C000000
    SVC_COPROC_INS              = 0x0C000000
    
    def execute(self):
        #import ipdb;ipdb.set_trace()
        self._TakeException()
        op = self.fetch_next_op()
        
        condition = (op & self.CONDITION_MASK) >> self.CONDITION_MASK_SHIFT
        
        proceed = False
        if condition == 14:
            proceed = True
        elif condition == 0:
            if self.cpsr.value & self.PROCESSOR_Z:
                proceed = True
        elif condition == 1:
            if not (self.cpsr.value & self.PROCESSOR_Z):
                proceed = True
        elif condition == 2:
            if self.cpsr.value & self.PROCESSOR_C:
                proceed = True
        elif condition == 3:
            if not (self.cpsr.value & self.PROCESSOR_C):
                proceed = True
        elif condition == 4:
            if self.cpsr.value & self.PROCESSOR_Z:
                proceed = True
        elif condition == 5:
            if not (self.cpsr.value & self.PROCESSOR_Z):
                proceed = True
        elif condition == 6:
            if self.cpsr.value & self.PROCESSOR_V:
                proceed = True
        elif condition == 7:
            if not (self.cpsr.value & self.PROCESSOR_V):
                proceed = True
        elif condition == 8:
            if (self.cpsr.value & self.PROCESSOR_C) and (not (self.cpsr.value & self.PROCESSOR_Z)):
                proceed = True
        elif condition == 9:
            if (not (self.cpsr.value & self.PROCESSOR_C)) and (self.cpsr.value & self.PROCESSOR_Z):
                proceed = True
        elif condition == 10:
            overflow = ((self.cpsr.value & self.PROCESSOR_V) != 0)
            negative = ((self.cpsr.value & self.PROCESSOR_N) != 0)
            if overflow == negative:
                proceed = True
        elif condition == 11:
            overflow = ((self.cpsr.value & self.PROCESSOR_V) != 0)
            negative = ((self.cpsr.value & self.PROCESSOR_N) != 0)
            if overflow != negative:
                proceed = True
        elif condition == 12:
            overflow = ((self.cpsr.value & self.PROCESSOR_V) != 0)
            negative = ((self.cpsr.value & self.PROCESSOR_N) != 0)
            if (overflow == negative) and not (self.cpsr.value & self.PROCESSOR_Z):
                proceed = True
        elif condition == 13:
            overflow = ((self.cpsr.value & self.PROCESSOR_V) != 0)
            negative = ((self.cpsr.value & self.PROCESSOR_N) != 0)
            if (overflow != negative) and (self.cpsr.value & self.PROCESSOR_Z):
                proceed = True
        
        if not proceed:
            self.next_op()
            return
            
        if (op & self.LOAD_STORE_INS_MASK) == self.LOAD_STORE_INS:
            # Load/store word and unsigned byte mask
            if (op & self.LDR_LITERAL_OP_MASK) == self.LDR_LITERAL_OP:
                # NOTE: Always write this before LDR_IMMEDIATE_OP
                # LDR (literal)
                add = ((op & self.LDR_LITERAL_U) != 0)
                rt = (op & self.LDR_LITERAL_RT) >> self.LDR_LITERAL_RT_SHIT
                imm = op & self.LDR_LITERAL_IMM
                base = self.get_ip() & (~ 0x3)
                address = (base + imm) if add else (base - imm)
                data = self.system_bus.read(address)
                
                self.register_write(rt, data)
            elif (op & self.LDR_IMMEDIATE_OP_MASK) == self.LDR_IMMEDIATE_OP:
                # LDR (immediate, ARM)
                rn = (op & self.LDR_IMMEDIATE_RN) >> self.LDR_IMMEDIATE_RN_SHIFT
                rt = (op & self.LDR_IMMEDIATE_RT) >> self.LDR_IMMEDIATE_RT_SHIFT
                imm = (op & self.LDR_IMMEDIATE_IMM)
                
                if rn == 0xF:
                    #FIXME see LDR ( Literal )
                    # NOTE: We should never come to this point.
                    raise WrongExecutionFlow()
                
                if not (op & self.LDR_IMMEDIATE_P) and op & self.LDR_IMMEDIATE_W:
                    #FIXME see LDRT
                    raise NotImplementedOpCode()
                
                if rn == 0xD and not (op & self.LDR_IMMEDIATE_P) and op & self.LDR_IMMEDIATE_U and not (op & self.LDR_IMMEDIATE_W) and imm == 0x4:
                    #FIXME see  POP
                    raise NotImplementedOpCode()
    
                index = op & self.LDR_IMMEDIATE_P == 1
                add = op & self.LDR_IMMEDIATE_U == 1
                wback = not (op & self.LDR_IMMEDIATE_P) and op & self.LDR_IMMEDIATE_W
                 
                base = self.register_read(rn)
                offset_addr = base + imm if add else base - imm
                address = offset_addr if index else base
                data = self.system_bus.read(address)
                if wback:
                    self.register_write(rn, offset_addr)
    
                self.register_write(rt, data)
            elif (op & self.STR_IMMEDIATE_OP_MASK) == self.STR_IMMEDIATE_OP:
                p = op & self.STR_IMMEDIATE_P
                w = op & self.STR_IMMEDIATE_W
                u = op & self.STR_IMMEDIATE_U
                rt = (op & self.STR_IMMEDIATE_RT) >> self.STR_IMMEDIATE_RT_SHIFT
                rn = (op & self.STR_IMMEDIATE_RN) >> self.STR_IMMEDIATE_RN_SHIFT
                imm = op & self.STR_IMMEDIATE_IMM
                
                if (not p) and w:
                    #FIXME see STRT
                    raise NotImplementedOpCode()
                
                if rn == 0xD and p and (not u) and w and imm == 0x4:
                    #FIXME see PUSH
                    raise NotImplementedOpCode()
                
                index = (p != 0)
                add = (u != 0)
                wback = (not p) or (w != 0)
                
                if wback and (rn == 15 or rn == rt):
                    raise Unpredictable()
                
                rn_value = self.register_read(rn).value
                offset_addr = (rn_value + imm) if add else (rn_value - imm)
                address = offset_addr if index else rn_value
                self.system_bus.write(address, self.register_read(rt))
                
                if wback:
                    self.register_write(rn, c_uint32(offset_addr))
            elif (op & self.STR_REGISTER_OP_MASK) == self.STR_REGISTER_OP:
                p = op & self.STR_REGISTER_P
                u = op & self.STR_REGISTER_U
                w = op & self.STR_REGISTER_W
                type = (op & self.STR_REGISTER_TYPE) >> self.STR_REGISTER_TYPE_SHIFT
                rm = op & self.STR_REGISTER_RM
                imm = (op & self.STR_REGISTER_IMM) >> self.STR_REGISTER_IMM_SHIFT
                rt = (op & self.STR_REGISTER_RT) >> self.STR_REGISTER_RT_SHIFT
                rn = (op & self.STR_REGISTER_RN) >> self.STR_REGISTER_RN_SHIFT
                
                if (not p) and w:
                    #FIXME see STRT
                    raise NotImplementedOpCode()
                
                index = (p != 0)
                add = (u != 0)
                wback = (not p) or (w != 0)
                shift_t, shift_n = self._DecodeImmShift(type, imm)
                
                if rm == 0xF:
                    raise Unpredictable()
                
                if wback and (rn == 15 or rn == rt):
                    raise Unpredictable()
                
                carry = self.cpsr.value & self.PROCESSOR_C and 1
                offset = self._SHIFT(self.register_read(rm).value, shift_t, shift_n, carry)
                rn_value = self.register_read(rn).value
                offset_addr = (rn_value + offset) if add else (rn_value + offset)
                address = offset_addr if index else rn_value
                if rt == 0xF:
                    #FIXME see PCStoreValue
                    raise NotImplementedOpCode()
                else:
                    data = self.register_read(rt)
                    
                self.system_bus.write(address, data)
                if wback:
                    self.register_write(rn, c_uint32(offset_addr))
        elif (op & self.BRANCH_INS_MASK) == self.BRANCH_INS:
            if (op & self.B_OP_MASK) == self.B_OP:
                imm = self._SignExtend26to32((op & self.B_IMM) << 2)
                self.set_ip(c_uint32(self.get_ip() + imm))
                return
            elif (op & self.BL_OP_MASK) == self.BL_OP:
                imm = self._SignExtend26to32((op & self.B_IMM) << 2)
                lr = self.get_lr_link()
                self.register_write(14, c_uint32(lr))
                self.set_ip(c_uint32(self.get_ip() + imm))
        elif (op & self.DATA_PROCESSING_INS_MASK) == self.DATA_PROCESSING_INS:
            if (op & self.ADD_IMMEDIATE_OP_MASK) == self.ADD_IMMEDIATE_OP:
                rd = (op & self.ADD_IMMEDIATE_RD) >> self.ADD_IMMEDIATE_RD_SHIFT
                rn = (op & self.ADD_IMMEDIATE_RN) >> self.ADD_IMMEDIATE_RN_SHIFT
                set_flags = op & self.ADD_IMMEDIATE_S
                imm = op & self.ADD_IMMEDIATE_IMM
                result, carry, overflow = self._AddWithCarry(self.register_read(rn).value, imm, 0)
                
                if rn == 0xF and not set_flags:
                    #FIXME see ADR
                    raise NotImplementedOpCode()
                if rn == 0xD:
                    #FIXME see ADD (SP plus immediate)
                    raise NotImplementedOpCode()
                    
                if rd == 0xF and set_flags:
                    #FIXME see SUBS PC, LR and related instructions.
                    raise NotImplementedOpCode()
                
                self.register_write(rd, c_uint32(result))
                if set_flags:
                    self.cpsr.value |= (result & 0x80000000) and self.PROCESSOR_N
                    self.cpsr.value |= (result == 0) and self.PROCESSOR_Z
                    self.cpsr.value |= carry and self.PROCESSOR_C
                    self.cpsr.value |= overflow and self.PROCESSOR_V

            elif (op & self.ADD_REGISTER_OP_MASK) == self.ADD_REGISTER_OP:
                rd = (op & self.ADD_REGISTER_RD) >> self.ADD_REGISTER_RD_SHIFT
                rn = (op & self.ADD_REGISTER_RN) >> self.ADD_REGISTER_RN_SHIFT
                imm = (op & self.ADD_REGISTER_IMM) >> self.ADD_REGISTER_IMM_SHIFT
                type = (op & self.ADD_REGISTER_TYPE) >> self.ADD_REGISTER_TYPE_SHIFT
                shift_t, shift_n = self._DecodeImmShift(type, imm)
                rm = op & self.ADD_REGISTER_RM
                s = op & self.ADD_REGISTER_S
                set_flags = (s != 0)
                
                if rd == 0xF and s:
                    #FIXME see SUBS PC, LR and related instructions
                    raise NotImplementedOpCode()
                
                if rn == 0xD:
                    #FIXME see ADD (SP plus register)
                    raise NotImplementedOpCode()
    
                carry = self.cpsr.value & self.PROCESSOR_C and 1
                shifted = self._SHIFT(self.register_read(rm).value, shift_t, shift_n, carry)
                result, carry, overflow = self._AddWithCarry(self.register_read(rn).value, shifted, 0)
                
                if rd == 0xF:
                    # FIXME ALUWritePC
                    raise NotImplementedOpCode()
                else:
                    self.register_write(rd, c_uint32(result))
                    
                    if set_flags:
                        self.cpsr.value |= (result & 0x80000000) and self.PROCESSOR_N
                        self.cpsr.value |= (result == 0) and self.PROCESSOR_Z
                        self.cpsr.value |= carry and self.PROCESSOR_C
                        self.cpsr.value |= overflow and self.PROCESSOR_V
                        
            elif (op & self.SUB_REGISTER_OP_MASK) == self.SUB_REGISTER_OP:
                imm = (op & self.SUB_REGISTER_IMM) >> self.SUB_REGISTER_IMM_SHIFT
                rn = (op & self.SUB_REGISTER_RN) >> self.SUB_REGISTER_RN_SHIFT
                rd = (op & self.SUB_REGISTER_RD) >> self.SUB_REGISTER_RD_SHIFT
                type = (op & self.SUB_REGISTER_TYPE) >> self.SUB_REGISTER_TYPE_SHIFT
                rm = op & self.SUB_REGISTER_RM
                s = op & self.SUB_REGISTER_S
                set_flags = (s == 1)
                shift_t, shift_n = self._DecodeImmShift(type, imm)
                
                if rd == 0xF and set_flags:
                    #FIXME SUBS PC, LR and related instructions
                    raise NotImplementedOpCode()
                    
                if rn == 0xD:
                    #FIXME see SUB (SP minus register)
                    raise NotImplementedOpCode()
                
                carry = self.cpsr.value & self.PROCESSOR_C and 1
                shifted = self._SHIFT(self.register_read(rm).value, shift_t, shift_n, carry)
                complemented_shifted = c_uint32(-shifted).value
                result, carry, overflow = self._AddWithCarry(self.register_read(rn).value, complemented_shifted, 0)
                
                if rd == 0xF:
                    #FIXME see ALUWritePC(result)
                    raise NotImplementedOpCode()
                else:
                    self.register_write(rd, c_uint32(result))
                    if set_flags:
                        self.cpsr.value |= (result & 0x80000000) and self.PROCESSOR_N
                        self.cpsr.value |= (result == 0) and self.PROCESSOR_Z
                        self.cpsr.value |= carry and self.PROCESSOR_C
                        self.cpsr.value |= overflow and self.PROCESSOR_V

            elif (op & self.BFC_OP_MASK) == self.BFC_OP:
                rd = (op & self.BFC_RD) >> self.BFC_RD_SHIFT
                msbit = (op & self.BFC_MSB) >> self.BFC_MSB_SHIFT
                lsbit = (op & self.BFC_LSB) >> self.BFC_LSB_SHIFT
                
                if rd == 0xF:
                    raise Unpredictable()
                
                msb_mask = (1 << (msbit+1)) - 1
                lsb_mask = (1 << lsbit) - 1
                complemented_mask = (msb_mask - lsb_mask)
                mask = c_uint32(~complemented_mask).value
                rd_value = self.register_read(rd).value
                masked_value = rd_value & mask
                self.register_write(rd,c_uint32(masked_value))
                
            elif (op & self.CMP_REGISTER_OP_MASK) == self.CMP_REGISTER_OP:
                rn = (op & self.CMP_REGISTER_RN) >> self.CMP_REGISTER_RN_SHIFT
                rm = op & self.CMP_REGISTER_RM
                type = (op & self.CMP_REGISTER_TYPE) >> self.CMP_REGISTER_TYPE_SHIFT
                imm = (op & self.CMP_REGISTER_IMM) >> self.CMP_REGISTER_IMM_SHIFT
                shift_t, shift_n = self._DecodeImmShift(type, imm)
                carry = self.cpsr.value & self.PROCESSOR_C and 1
                shifted = self._SHIFT(self.register_read(rm).value, shift_t, shift_n, carry)
                complemented_shifted = c_uint32(-shifted).value
                result, carry, overflow = self._AddWithCarry(self.register_read(rn).value, complemented_shifted, 0)
                
                self.cpsr.value |= (result & 0x80000000) and self.PROCESSOR_N
                self.cpsr.value |= (result == 0) and self.PROCESSOR_Z
                self.cpsr.value |= carry and self.PROCESSOR_C
                self.cpsr.value |= overflow and self.PROCESSOR_V

            elif (op & self.MOV_IMMEDIATE_OP1_MASK) == self.MOV_IMMEDIATE_OP1:
                # FIXME
                rd = (op & self.MOV_IMMEDIATE_OP1_RD) >> self.MOV_IMMEDIATE_OP1_RD_SHIFT
                s = op & self.MOV_IMMEDIATE_OP1_S
                set_flags = (s!=0)
                imm = op & self.MOV_IMMEDIATE_OP1_IMM
                carry = self.cpsr.value & self.PROCESSOR_C and 1
                result, carry = self._ARMExpandImm_C(imm, carry)
                if rd == 0xF:
                    #FIXME see ALUWritePC(result)
                    raise NotImplementedOpCode()
                else:
                    self.register_write(rd, c_uint32(result))
                    if set_flags:
                        self.cpsr.value |= (result & 0x80000000) and self.PROCESSOR_N
                        self.cpsr.value |= (result == 0) and self.PROCESSOR_Z
                        self.cpsr.value |= carry and self.PROCESSOR_C

            elif (op & self.MOV_IMMEDIATE_OP2_MASK) == self.MOV_IMMEDIATE_OP2:
                rd = (op & self.MOV_IMMEDIATE_OP1_RD) >> self.MOV_IMMEDIATE_OP1_RD_SHIFT
                imm1 = op & self.MOV_IMMEDIATE_OP1_IMM
                imm2 = (op & self.MOV_IMMEDIATE_OP2_IMM) >> 4
                imm = imm1 | imm2
                
                if rd == 0xF:
                    raise Unpredictable
                else:
                    self.register_write(rd, c_uint32(result))
            elif (op & self.MOV_REGISTER_OP_MASK) == self.MOV_REGISTER_OP:
                rd = (op & self.MOV_REGISTER_RD) >> self.MOV_REGISTER_RD_SHIFT
                rm = op & self.MOV_REGISTER_RM
                s = op & self.MOV_REGISTER_S
                set_flags = (s != 0)
                result = self.register_read(rm)
                if rd == 0xF:
                    #FIXME see ALUWritePC(result)
                    raise NotImplementedOpCode()
                else:
                    self.register_write(rd, result)
                    if set_flags:
                        self.cpsr.value |= (result.value & 0x80000000) and self.PROCESSOR_N
                        self.cpsr.value |= (result.value == 0) and self.PROCESSOR_Z
            elif (op & self.LSL_IMMEDIATE_OP_MASK) == self.LSL_IMMEDIATE_OP:
                imm = (op & self.LSL_IMMEDIATE_IMM) >> self.LSL_IMMEDIATE_IMM_SHIFT
                rd = (op & self.LSL_IMMEDIATE_RD) >> self.LSL_IMMEDIATE_RD_SHIFT
                rm = op & self.LSL_IMMEDIATE_RM
                s = op & self.LSL_IMMEDIATE_S
                set_flags = (s!=0)
                
                if imm == 0:
                    #FIXME see MOV (Register)
                    raise WrongExecutionFlow()
                
                _, shift_n = self._DecodeImmShift(0x0, imm)
                carry = self.cpsr.value & self.PROCESSOR_C and 1
                result, carry = self._SHIFT_C(self.register_read(rm).value, self.SRType_LSL, shift_n, carry)
                if rd == 0xF:
                    #FIXME ALUWritePC()
                    raise NotImplementedOpCode()
                else:
                    self.register_write(rd, c_uint32(result))
                    if set_flags:
                        self.cpsr.value |= (result & 0x80000000) and self.PROCESSOR_N
                        self.cpsr.value |= (result == 0) and self.PROCESSOR_Z
                        self.cpsr.value |= carry and self.PROCESSOR_C
            elif (op & self.LSR_IMMEDIATE_OP_MASK) == self.LSR_IMMEDIATE_OP:
                imm = (op & self.LSR_IMMEDIATE_IMM) >> self.LSR_IMMEDIATE_IMM_SHIFT
                rd = (op & self.LSR_IMMEDIATE_RD) >> self.LSR_IMMEDIATE_RD_SHIFT
                rm = op & self.LSR_IMMEDIATE_RM
                s = op & self.LSR_IMMEDIATE_S
                set_flags = (s!=0)
                
                if imm == 0:
                    #FIXME see MOV (Register)
                    raise WrongExecutionFlow()
                
                _, shift_n = self._DecodeImmShift(0x1, imm)
                carry = self.cpsr.value & self.PROCESSOR_C and 1
                result, carry = self._SHIFT_C(self.register_read(rm).value, self.SRType_LSR, shift_n, carry)
                if rd == 0xF:
                    #FIXME ALUWritePC()
                    raise NotImplementedOpCode()
                else:
                    self.register_write(rd, c_uint32(result))
                    if set_flags:
                        self.cpsr.value |= (result & 0x80000000) and self.PROCESSOR_N
                        self.cpsr.value |= (result == 0) and self.PROCESSOR_Z
                        self.cpsr.value |= carry and self.PROCESSOR_C
            elif (op & self.ORR_IMMEDIATE_OP_MASK) == self.ORR_IMMEDIATE_OP:
                imm = op & self.ORR_IMMEDIATE_IMM
                rd = (op & self.ORR_IMMEDIATE_RD) >> self.ORR_IMMEDIATE_RD_SHIFT    
                rn = (op & self.ORR_IMMEDIATE_RN) >> self.ORR_IMMEDIATE_RN_SHIFT
                s = op & self.ORR_IMMEDIATE_S
                set_flags = (s != 0)
                
                if rd == 0xF and s:
                    #FIXME see SUBS PC, LR and related instructions
                    raise NotImplementedOpCode()
                
                carry = self.cpsr.value & self.PROCESSOR_C and 1
                imm, carry = self._ARMExpandImm_C(imm, carry)
                
                result = self.register_read(rn).value | imm
                
                if rd == 0xF:
                    #FIXME ALUWritePC(result)
                    raise NotImplementedOpCode()
                else:
                    self.register_write(rd, c_uint32(result))
                    if set_flags:
                        self.cpsr.value |= (result & 0x80000000) and self.PROCESSOR_N
                        self.cpsr.value |= (result == 0) and self.PROCESSOR_Z
                        self.cpsr.value |= carry and self.PROCESSOR_C
            elif (op & self.ORR_REGISTER_OP_MASK) == self.ORR_REGISTER_OP:
                imm = (op & self.ORR_REGISTER_IMM) >> self.ORR_REGISTER_IMM_SHIFT
                rn = (op & self.ORR_REGISTER_RN) >> self.ORR_REGISTER_RN_SHIFT
                rm = op & self.ORR_REGISTER_RM
                rd = (op & self.ORR_REGISTER_RD) >> self.ORR_REGISTER_RD_SHIFT
                type = (op & self.ORR_REGISTER_TYPE) >> self.ORR_REGISTER_TYPE_SHIFT
                s = op & self.ORR_REGISTER_S
                set_flags = (s != 0)
                
                if rd == 0xF and s:
                    #FIXME see SUBS PC, LR and related instructions
                    raise NotImplementedOpCode()
                
                shift_t, shift_n = self._DecodeImmShift(type, imm)
                carry = self.cpsr.value & self.PROCESSOR_C and 1
                shifted, carry = self._SHIFT_C(self.register_read(rm).value, type, imm, carry)
                result = self.register_read(rn).value | shifted
                
                if rd == 0xF:
                    #FIXME ALUWritePC(result)
                    raise NotImplementedOpCode()
                else:
                    self.register_write(rd, c_uint32(result))
                    if set_flags:
                        self.cpsr.value |= (result & 0x80000000) and self.PROCESSOR_N
                        self.cpsr.value |= (result == 0) and self.PROCESSOR_Z
                        self.cpsr.value |= carry and self.PROCESSOR_C
        elif (op & self.SVC_COPROC_INS_MASK) == self.SVC_COPROC_INS: 
            if (op & self.SVC_OP_MASK) == self.SVC_OP:
                imm = op & self.SVC_IMM # Not used at all.
                self.interrupt_triggered(self.IRQ_SVC)
                return
            elif (op & self.MCR_OP_MASK) == self.MCR_OP:
                opc1 = (op & self.MCR_OPC1) >> self.MCR_OPC1_SHIFT
                crn = (op & self.MCR_CRN) >> self.MCR_CRN_SHIFT
                rt = (op & self.MCR_RT) >> self.MCR_RT_SHIFT
                coproc = (op & self.MCR_COPROC) >> self.MCR_COPROC_SHIFT
                opc2 = (op & self.MCR_OPC2) >> self.MCR_OPC2_SHIFT
                crm = op & self.MCR_CRM
                if coproc == 0xF:
                    self._CP15_write(crn, opc1, crm, opc2, self.register_read(rt).value)
                else:
                    raise NotImplementedOpCode()
        else:
            raise InvalidInstructionOpCode()
        
        self.next_op()
    
    
    def _SignExtend26to32(self, imm):
        sign = ((imm & (1 << 25)) != 0)
        if sign:
            result = ((~ imm) + 1) & ((1 << 26) - 1)
            result = -result
        else:
            result = imm

        return result
        
        
    SRType_LSL = 0x0
    SRType_LSR = 0x1
    SRType_ASR = 0x2
    SRType_RRX = 0x3
    SRType_ROR = 0x4
    def _DecodeImmShift(self, type, imm):
        if type == 0:
            shift_t = self.SRType_LSL
            shift_n = imm 
        elif type == 1:
            shift_t = self.SRType_LSR
            shift_n = 32 if imm == 0 else imm
        elif type == 2:
            shift_t = self.SRType_ASR
            shift_n = 32 if imm == 0 else imm
        elif type == 3:
            if imm == 0:
                shift_t = self.SRType_RRX
                shift_n = 1
            else:
                shift_t = self.SRType_ROR
                shift_n = imm
        
        return shift_t, shift_n
    
    def _SHIFT(self, value, type, amount, carry_in):
        result, _ = self._SHIFT_C(value, type, amount, carry_in)
        return result

    def _SHIFT_C(self, value, type, amount, carry_in):
        if amount == 0:
            result, carry_out = value, carry_in
        else:
            if type == self.SRType_LSL:
                result, carry_out = self._LSL_C(value, amount)
            elif type == self.SRType_LSR:
                result, carry_out = self._LSR_C(value, amount)
            elif type == self.SRType_ASR:
                result, carry_out = self._ASR_C(value, amount)
            elif type == self.SRType_ROR:
                result, carry_out = self._ROR_C(value, amount)
            elif type == self.SRType_RRX:
                result, carry_out = self._RRX_C(value, amount)
                
        return result, carry_out
    
    def _ARMExpandImm_C(self, imm, carry_in):
        unrotated_value = imm & ((1 << 8) - 1)
        shift = (imm & (0xF << 8)) >> 8
        imm, carry_out = self._SHIFT_C(unrotated_value, self.SRType_ROR, shift, carry_in)
        return imm, carry_out
        
    def _LSL_C(self, x, shift):
        extended_x = c_uint64(x << shift)
        carry_out = (extended_x.value >> 32) & 0x1
        result = c_uint32(extended_x.value)
        return result.value, carry_out
    
    def _LSL(self, x, shift):
        if shift == 0:
            result = x
        else:
            result, _ = self._LSL_C(x, shift)
        return result
    
    def _LSR_C(self, x, shift):
        mask = 1 << (shift - 1)
        carry_out = x & mask
        return x >> shift, 1 if carry_out else 0
    
    def _LSR(self, x, shift):
        if shift == 0:
            result = x
        else:
            result, _ = self._LSR_C(x, shift)
            
        return result
    
    def _ROR_C(self, x, shift):
        mask = (1 << shift) - 1
        masked_x = x & mask
        shifted_value = masked_x << 32 - shift
        shifted_x = x >> shift
        result = shifted_value | shifted_x
        carry_out = x & (1 << (shift - 1))
        return result, 1 if carry_out else 0
    
    def _ROR(self, x, shift):
        if shift == 0:
            result = x
        else:
            result, _ = self._ASR_C(x, shift)
        
        return result
    
    def _ASR_C(self, x, shift):
        mask = ((1 << shift) - 1) << (32 - shift)
        masked_x = x & mask
        shifted_x = x >> shift
        result = shifted_x | masked_x
        carry_out = x & (1 << (shift - 1))
        return result, 1 if carry_out else 0
    
    def _ASR(self, x, shift):
        if shift == 0:
            result = x
        else:
            result, _ = self._ASR_C(x, shift)
        
        return result
    
    def _RRX_C(self, x, carry_in):
        carry_out = x & 1
        result = (x >> 1) | (carry_in << 31)
        return result, carry_out
    
    def _RRX(self, x, carry_in):
        result, _ = self._RRX_C(x, carry_in)
        return result
    
    def _AddWithCarry(self, op1, op2, carry_in):
        unsigned_sum = op1 + op2 + carry_in
        signed_sum = c_int32(op1).value + c_int32(op2).value + carry_in
        result = unsigned_sum & ((1 << 31) - 1)
        carry_out = 0 if result == unsigned_sum else 1
        overflow = 0 if result == c_int32(signed_sum).value else 1
        return (result, carry_out, overflow)
    
    def _IsMonitorMode(self):
        return (self.cpsr.value & self.PROCESSOR_MODE) == 0x16
    
    def _IsUserMode(self):
        return (self.cpsr.value & self.PROCESSOR_MODE) == 0x10
    
    def _IsPrivilegedMode(self):
        return not ((self.cpsr.value & self.PROCESSOR_MODE) == 0x10)
    
    def _IsSecure(self):
        return ((self._SCR().value & self.SCR_NS) == 0)
    
    SCR_NS  = 1 << 0
    SCR_IRQ = 1 << 1
    SCR_FIQ = 1 << 2
    SCR_EA  = 1 << 3
    SCR_FW  = 1 << 4
    SCR_AW  = 1 << 5
    def _SCR(self):
        return self._CP15_read(1, 0, 1, 0)
    
    SCTLR_V  = 0x1 << 13
    SCTLR_VE = 0x1 << 24
    SCTLR_EE = 0x1 << 25
    SCTLR_TE = 0x1 << 30
    def _SCTLR(self):
        return self._CP15_read(1, 0, 0, 0)
    
    def _VBAR(self):
        return self._CP15_read(12, 0, 0, 0)
    
    def _MVBAR(self):
        return self._CP15_read(12, 0, 0, 1)
    
    def _CP15_read(self, crn, opc1, crm, opc2):
        privileged = self._IsPrivilegedMode()
        secure = ((self.cp15_registers[1][0][1][0][0].value & self.SCR_NS) == 0)
        user_mode = self._IsUserMode()
        if crn == 1:
            if opc1 == 0 and crm == 0 and opc2 == 0:
                # SCTRL
                if not privileged:
                    raise AccessViolation()
                
                bank = 0 if secure else 1
                return self.cp15_registers[1][0][0][0][bank]
            if opc1 == 0 and crm == 1 and opc2 == 0:
                # SCR
                if not (privileged and secure):
                    raise AccessViolation()
                
                return self.cp15_registers[1][0][1][0][0]
        elif crn == 12:
            # Security Extension registers.
            if opc1 == 0 and crm == 0 and opc2 == 0:
                # VBAR ( Banked , read/write priviledged)
                if not privileged:
                    raise AccessViolation()
                
                bank = 0 if secure else 1
                return self.cp15_registers[12][0][0][0][bank]
            elif opc1 == 0 and crm == 0 and opc2 == 1:
                # MVBAR ( Banked , read/write )
                if not privileged:
                    raise AccessViolation()
                
                bank = 0 if secure else 1
                return self.cp15_registers[12][0][0][1][bank]
            elif opc1 == 0 and crm == 1 and opc2 == 0:
                # ISR ( read-only )
                if not privileged:
                    raise AccessViolation()
                
                return self.cp15_registers[12][0][1][0][0]
    
    def _CP15_write(self, crn, opc1, crm, opc2, value):
        privileged = self._IsPrivilegedMode()
        secure = self._IsSecure()
        user_mode = self._IsUserMode()
        
        if crn == 1:
            if opc1 == 0 and crm == 0 and opc2 == 0:
                # SCTRL
                if not privileged:
                    raise AccessViolation()
                
                bank = 0 if secure else 1
                self.cp15_registers[1][0][0][0][bank].value = value
            if opc1 == 0 and crm == 1 and opc2 == 0:
                # SCR
                if not (privileged and secure):
                    raise AccessViolation()
                
                self.cp15_registers[1][0][1][0][0].value = value
        elif crn == 12:
            # Security Extension registers.
            if opc1 == 0 and crm == 0 and opc2 == 0:
                # VBAR ( Banked , read/write priviledged)
                if not privileged:
                    raise AccessViolation()
                
                bank = 0 if secure else 1
                self.cp15_registers[12][0][0][0][bank].value = value & (~0x1F)
            elif opc1 == 0 and crm == 0 and opc2 == 1:
                # MVBAR ( Banked , read/write )
                if not privileged:
                    raise AccessViolation()
                
                bank = 0 if secure else 1
                self.cp15_registers[12][0][0][1][bank].value = value & (~0x1F)
            elif opc1 == 0 and crm == 1 and opc2 == 0:
                # ISR ( read-only )
                raise AccessViolation()
    
    def set_ip(self, address):
        self.ip.value = address.value
        
    def get_ip(self):
        thumb = self.cpsr.value & self.PROCESSOR_THUMB 
        return (self.ip.value + 8) if not thumb else (self.ip.value + 4)
    
    def get_lr_link(self):
        thumb = self.cpsr.value & self.PROCESSOR_THUMB 
        return (self.ip.value + 4) if not thumb else (self.ip.value + 2)
    
    def next_op(self):
        self.set_ip(c_uint32(self.ip.value + self.word_size))
        
    def run(self):
        while True:
            self.execute()