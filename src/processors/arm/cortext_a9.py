import logging
import threading
import global_env
from ctypes import c_uint32, c_uint64, c_int32, c_int64
from controllers.interfaces import AbstractInterruptConsumer
import sys

INITIAL_IP = c_uint32(0x0)
CPSR_RESET = c_uint32(0x0)
MIDR_RESET = c_uint32(0x412FC092)

class NotImplementedInstructionSet(Exception):
    pass

class NoRegisterFound(Exception):
    pass

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

class TranslationFault(Exception):
    def __init__(self, domain):
        self.domain
        
class PageTranslationFault(Exception):
    def __init__(self, domain):
        self.domain
        
class SectionTranslationFault(Exception):
    def __init__(self, domain):
        self.domain

class AccessFlagFault(Exception):
    def __init__(self, domain):
        self.domain
        
class SectionPermissionFault(Exception):
    def __init__(self, domain):
        self.domain
        
class PagePermissionFault(Exception):
    def __init__(self, domain):
        self.domain
        
class SectionDomainFault(Exception):
    def __init__(self, domain):
        self.domain

class PageDomainFault(Exception):
    def __init__(self, domain):
        self.domain

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
    LDR_IMMEDIATE_W         = 0x00200000
    LDR_IMMEDIATE_U         = 0x00800000
    
    LDR_LITERAL_OP_MASK     = 0x0F7F0000
    LDR_LITERAL_OP          = 0x051F0000
    LDR_LITERAL_IMM         = 0x00000FFF
    LDR_LITERAL_RT          = 0x0000F000
    LDR_LITERAL_RT_SHIT     = 12
    LDR_LITERAL_U           = 0x00800000
    
    LDR_REGISTER_OP_MASK    = 0x0E500010
    LDR_REGISTER_OP         = 0x06100000
    LDR_REGISTER_P          = 0x01000000
    LDR_REGISTER_U          = 0x00800000
    LDR_REGISTER_W          = 0x00200000
    LDR_REGISTER_RN         = 0x000F0000
    LDR_REGISTER_RN_SHIFT   = 16
    LDR_REGISTER_RT         = 0x0000F000
    LDR_REGISTER_RT_SHIFT   = 12
    LDR_REGISTER_IMM        = 0x00000F80
    LDR_REGISTER_IMM_SHIFT  = 7
    LDR_REGISTER_TYPE       = 0x00000060
    LDR_REGISTER_TYPE_SHIFT = 5
    LDR_REGISTER_RM         = 0x0000000F
    
    LDRB_IMMEDIATE_OP_MASK  = 0x0E500000
    LDRB_IMMEDIATE_OP       = 0x04500000
    LDRB_IMMEDIATE_P        = 0x01000000
    LDRB_IMMEDIATE_U        = 0x00800000
    LDRB_IMMEDIATE_W        = 0x00200000
    LDRB_IMMEDIATE_RN       = 0x000F0000
    LDRB_IMMEDIATE_RN_SHIFT = 16
    LDRB_IMMEDIATE_RT       = 0x0000F000
    LDRB_IMMEDIATE_RT_SHIFT = 12
    LDRB_IMMEDIATE_IMM      = 0x00000FFF
    
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
    
    BX_OP_MASK              = 0x0FFFFFF0
    BX_OP                   = 0x012FFF10
    BX_RM                   = 0x0000000F
    
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
    
    SUB_IMMEDIATE_OP_MASK   = 0x0FE00000
    SUB_IMMEDIATE_OP        = 0x02400000
    SUB_IMMEDIATE_RN        = 0x000F0000
    SUB_IMMEDIATE_RN_SHIFT  = 16
    SUB_IMMEDIATE_RD        = 0x0000F000
    SUB_IMMEDIATE_RD_SHIFT  = 12
    SUB_IMMEDIATE_IMM       = 0x00000FFF
    SUB_IMMEDIATE_S         = 0x00100000
    
    # ADR #FIXME ( two forms )
    SUB_IMMEDIATE_OP_MASK   = 0x0F7F0000
    SUB_IMMEDIATE_OP        = 0x024F0000
    SUB_IMMEDIATE_RD        = 0x0000F000
    SUB_IMMEDIATE_RD_SHIFT  = 12
    SUB_IMMEDIATE_IMM       = 0x00000FFF
    SUB_IMMEDIATE_ADD       = 0x00800000

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
    CMP_IMMEDIATE_OP_MASK   = 0x0FF0F000
    CMP_IMMEDIATE_OP        = 0x03500000
    CMP_IMMEDIATE_RN        = 0x000F0000
    CMP_IMMEDIATE_RN_SHIFT  = 16
    CMP_IMMEDIATE_IMM       = 0x00000FFF
    
    
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
    
    LDM_OP_MASK             = 0x0FD00000
    LDM_OP                  = 0x08900000
    LDM_RN                  = 0x000F0000
    LDM_RN_SHIFT            = 16
    LDM_W                   = 0x00200000
    LDM_REGISTERS           = 0x0000FFFF
    
    STM_OP_MASK             = 0x0FD00000
    STM_OP                  = 0x08800000
    STM_RN                  = 0x000F0000
    STM_RN_SHIFT            = 16
    STM_W                   = 0x00200000
    STM_REGISTERS           = 0x0000FFFF
    
    # Test bitwise AND
    TST_IMMEDIATE_OP_MASK   = 0x0FF0F000
    TST_IMMEDIATE_OP        = 0x03100000
    TST_IMMEDIATE_RN        = 0x000F0000
    TST_IMMEDIATE_RN_SHIFT  = 16
    TST_IMMEDIATE_IMM       = 0x00000FFF
    
    # MVN
    MVN_IMMEDIATE_OP_MASK   = 0x0FEF0000
    MVN_IMMEDIATE_OP        = 0x03E00000
    MVN_IMMEDIATE_S         = 0x00100000
    MVN_IMMEDIATE_RD        = 0x0000F000
    MVN_IMMEDIATE_RD_SHIFT  = 12
    MVN_IMMEDIATE_IMM       = 0x00000FFF
    
    MVN_REGISTER_SH_OP_MASK = 0x0FEF0090
    MVN_REGISTER_SH_OP      = 0x01E00010
    MVN_REGISTER_SH_S       = 0x00100000
    MVN_REGISTER_SH_RD      = 0x0000F000
    MVN_REGISTER_SH_RD_SHIFT= 12
    MVN_REGISTER_SH_RS      = 0x00000F00
    MVN_REGISTER_SH_RS_SHIFT= 8
    MVN_REGISTER_SH_TYPE    = 0x00000060
    MVN_REGISTER_SH_TYPE_SHIFT = 5
    MVN_REGISTER_SH_RM      = 0x0000000F

    # Bitwise Bit Clear
    BIC_IMMEDIATE_OP_MASK   = 0x0FE00000
    BIC_IMMEDIATE_OP        = 0x03C00000
    BIC_IMMEDIATE_S         = 0x00100000
    BIC_IMMEDIATE_RN        = 0x000F0000
    BIC_IMMEDIATE_RN_SHIFT  = 16
    BIC_IMMEDIATE_RD        = 0x0000F000
    BIC_IMMEDIATE_RD_SHIFT  = 12
    BIC_IMMEDIATE_IMM       = 0x00000FFF
    
    BIC_REGISTER_SH_OP_MASK = 0x0FE00090
    BIC_REGISTER_SH_OP      = 0x01C00010
    BIC_REGISTER_SH_S       = 0x00100000
    BIC_REGISTER_SH_RN      = 0x000F0000
    BIC_REGISTER_SH_RN_SHIFT= 16
    BIC_REGISTER_SH_RD      = 0x0000F000
    BIC_REGISTER_SH_RD_SHIFT= 12
    BIC_REGISTER_SH_RS      = 0x00000F00
    BIC_REGISTER_SH_RS_SHIFT= 8
    BIC_REGISTER_SH_TYPE    = 0x00000060
    BIC_REGISTER_SH_TYPE_SHIFT= 5
    BIC_REGISTER_SH_RM      = 0x0000000F
    
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
    
    ORR_REGISTER_SH_OP_MASK = 0x0FE00090
    ORR_REGISTER_SH_OP      = 0x01800010
    ORR_REGISTER_SH_S       = 0x00100000
    ORR_REGISTER_SH_RN      = 0x000F0000
    ORR_REGISTER_SH_RN_SHIFT= 16
    ORR_REGISTER_SH_RD      = 0x0000F000
    ORR_REGISTER_SH_RD_SHIFT= 12
    ORR_REGISTER_SH_RS      = 0x00000F00
    ORR_REGISTER_SH_RS_SHIFT= 8
    ORR_REGISTER_SH_TYPE    = 0x00000060
    ORR_REGISTER_SH_TYPE_SHIFT= 5
    ORR_REGISTER_SH_RM      = 0x0000000F
    
    # AND
    AND_IMMEDIATE_OP_MASK   = 0x0FE00000
    AND_IMMEDIATE_OP        = 0x02000000
    AND_IMMEDIATE_S         = 0x00100000
    AND_IMMEDIATE_RN        = 0x000F0000
    AND_IMMEDIATE_RN_SHIFT  = 16
    AND_IMMEDIATE_RD        = 0x0000F000
    AND_IMMEDIATE_RD_SHIFT  = 12
    AND_IMMEDIATE_IMM       = 0x00000FFF
    
    AND_REGISTER_OP_MASK    = 0x0FE00010
    AND_REGISTER_OP         = 0x00000000
    AND_REGISTER_S          = 0x00100000
    AND_REGISTER_RN         = 0x000F0000
    AND_REGISTER_RN_SHIFT   = 16
    AND_REGISTER_RD         = 0x0000F000
    AND_REGISTER_RD_SHIFT   = 12
    AND_REGISTER_IMM        = 0x00000F80
    AND_REGISTER_IMM_SHIFT  = 7
    AND_REGISTER_TYPE       = 0x00000060
    AND_REGISTER_TYPE_SHIFT = 5
    AND_REGISTER_RM         = 0x0000000F
    
    # SVC
    SVC_OP_MASK             = 0x0F000000
    SVC_OP                  = 0x0F000000
    SVC_IMM                 = 0x00FFFFFF
    
    # Move to coprocessor from register
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
    
    # Move to register from coprocessor
    MRC_OP_MASK             = 0x0F100010
    MRC_OP                  = 0x0E100010
    MRC_OPC1                = 0x00E00000
    MRC_OPC1_SHIFT          = 21
    MRC_CRN                 = 0x000F0000
    MRC_CRN_SHIFT           = 16
    MRC_RT                  = 0x0000F000
    MRC_RT_SHIFT            = 12
    MRC_COPROC              = 0x00000F00
    MRC_COPROC_SHIFT        = 8
    MRC_OPC2                = 0x000000E0
    MRC_OPC2_SHIFT          = 5
    MRC_CRM                 = 0x0000000F
    
    # Move to register from special register
    MRS_OP_MASK             = 0x0FBF0FFF
    MRS_OP                  = 0x010F0000
    MRS_RD                  = 0x0000F000
    MRS_RD_SHIFT            = 12
    MRS_READ_SAVED          = 0x00400000
    
    MRS_USER_MASK           = 0xF80F0000
    MRS_SVC_MASK            = 0xFF0FFFFF
    
    # Move to special register from arm core register
    MSR_REGISTER_OP_MASK    = 0x0FB0FFF0
    MSR_REGISTER_OP         = 0x0120F000
    MSR_REGISTER_MASK       = 0x000F0000
    MSR_REGISTER_MASK_SHIFT = 16
    MSR_REGISTER_RN         = 0x0000000F
    MSR_REGISTER_R          = 0x00400000
    
    # PUSH
    PUSH_OP1_MASK           = 0x0FFF0000
    PUSH_OP1                = 0x092D0000
    PUSH_OP1_REGISTERS      = 0x0000FFFF
    
    PUSH_OP2_MASK           = 0x0000F000
    PUSH_OP2                = 0x052D0004
    PUSH_OP2_RT             = 0x0000F000
    PUSH_OP2_RT_SHIFT       = 12
    
    POP_OP1_MASK            = 0x0FFF0000
    POP_OP1                 = 0x08BD0000
    POP_OP1_REGISTERS       = 0x0000FFFF
    
    POP_OP2_MASK            = 0x0FFF0FFF
    POP_OP2                 = 0x049D0004
    POP_OP2_RT              = 0x0000F000
    POP_OP2_RT_SHIFT        = 12
    

    def __init__(self, name, system_bus, security_extensions=True):
        threading.Thread.__init__(self)
        # A word is 4-bytes long.
        self.logger = logging.getLogger(name)
        self.name = name
        self.system_bus = system_bus
        self.word_size = 4
        self.received_interrupts = {}
        global_env.THREAD_ENV.engine_id = name
        self.HaveSecurityExt = security_extensions
        
        self.init_registers()
        self.init_interrupts()
        self.init_ophandlers()
        
    def get_name(self):
        return self.name
    
    PAGEDIR_TYPE_MASK   = 0x00003
    DOMAIN_MASK         = 0x1E0
    DOMAIN_MASK_SHIFT   = 5
    def _mmu_translate(self, vaddress, read_access=True, instruction=False):
        if not (self._SCTLR().value & self.SCTLR_M):
            return vaddress

        #TODO
        # 1- lookup instruction or data micro TLB using (vaddress + ASID + Security state in)
        # 2- If not found, lookup main TLB using (vaddress + ASID + Security state in)
        # 3- If not found, do a translation table walk.
        n = self._TTBCR().value & self.TTBCR_N
        tmp = vaddress & (((1 << n) - 1) << (31 - n))
        
        if tmp:
            translation_base = self._TTBCR1().value & (((1 << 18) - 1) << 14)
            table_index = vaddress & (((1 << 12) - 1) << 20)
            tbi = translation_base + (table_index << 2)
        else:
            translation_base = self._TTBCR0().value & (((16 + n) - 1) << (14 - n)) 
            table_index = vaddress & ((12 - n) << 20)
            tbi = translation_base + (table_index << 2)
            
        pdte = self.system_bus.read(tbi).value # page directory table entry
        pdte_type = pdte & self.PAGEDIR_TYPE_MASK # page directoy table entry type
        
        pte = None
        domain = (pdte & self.DOMAIN_MASK) >> self.DOMAIN_MASK_SHIFT
        secure = self._IsSecure()
        if pdte_type == 1:
            # pagetable
            # NS
            ns = pdte & 0x8
            if (not secure) and (not ns):
                raise PageTranslationFault(domain)
            # page table base address
            ptba = pdte & (~0x3FF)
            # level 2 table index
            l2ti = vaddress & (0xFF << 12)
            tbi = ptba | (l2ti << 2)
            # level 2 descriptor
            pte = self.system_bus.read(tbi).value
            if pte & 0x2:
                # small page
                # XN
                xn = pte & 0x1
                paddress = pte & (~0x3FF)
            elif pte & 0x1:
                # large page
                # XN
                xn = pte & 0x8000
                paddress = pte & (~0xFFFF)
            else:
                raise PageTranslationFault(domain)
        elif pdte_type == 2:
            # XN
            xn = pdte & 0x10 
            if (pdte & 40000):
                # supersection
                # NS
                ns = pdte & 0x40000
                if (not secure) and (not ns):
                    raise SectionTranslationFault(domain)
                paddress = pdte & (~0xFFFFF)
            else:
                # section
                # NS
                ns = pdte & 0x40000
                if (not secure) and (not ns):
                    raise SectionTranslationFault(domain)
                paddress = pdte & (~0xFFFFFF)
        else:
            raise SectionTranslationFault(domain)
        
        if xn and instruction:
            if pte:
                raise PagePermissionFault(domain)
            raise SectionPermissionFault(domain)

        dtype = self._DACR_domain_type(domain)
        if (dtype == self.DACR_NACCESS) or (dtype == self.DACR_RESERVED):
            if pte:
                raise PageDomainFault()
            raise SectionDomainFault(domain)
        elif dtype == self.DACR_CLIENT:
            if pte != None:
                ap = (pte & 0x30) >> 4 
                ap |= (pte & 0x200) >> 7 # 9 - 2
            else:
                ap = (pdte & 0x300) >> 10
                ap |= (pdte & 0x4000) >> 13 # 15 - 2
            
            privileged = self._IsPrivilegedMode()
            if ap == 0:
                if pte:
                    raise PagePermissionFault(domain)
                raise SectionPermissionFault(domain)
            elif ap == 1:
                if not privileged:
                    if pte:
                        raise PagePermissionFault(domain)
                    raise SectionPermissionFault(domain) 
            elif ap == 2:
                if not privileged and not read_access:
                    if pte:
                        raise PagePermissionFault(domain)
                    raise SectionPermissionFault(domain)
            elif ap == 3:
                pass
            elif ap == 4:
                # reserver
                pass
            elif ap == 5:
                if not privileged or (privileged and not read_access):
                    if pte:
                        raise PagePermissionFault(domain)
                    raise SectionPermissionFault(domain)
            elif ap == 6:
                if not read_access:
                    if pte:
                        raise PagePermissionFault(domain)
                    raise SectionPermissionFault(domain)
            elif ap == 7:
                if not read_access:
                    if pte:
                        raise PagePermissionFault(domain)
                    raise SectionPermissionFault(domain)
        
        # If we're here then we passed all the checks.
        return paddress

    def mmu_read(self, vaddress, instruction=False):
        fs = None
        try:
            paddress = self._mmu_translate(vaddress, instruction=instruction)
        except SectionTranslationFault as ex:
            fs = 0x5
        except PageTranslationFault as ex:
            fs = 0x7
        except SectionDomainFault as ex:
            fs = 0x9
        except PageDomainFault as ex:
            fs = 0xB
        except SectionPermissionFault as ex:
            fs = 0xD
        except PagePermissionFault as ex:
            fs = 0xF
        
        if fs:
            if instruction:
                self._IFAR().value = vaddress
                self._IFSR().value = (fs & 0xF) | ((fs & 0x10) << 10)
            else:
                self._DFAR().value = vaddress
                self._DFSR().value = ex.domain << 4 | (fs & 0xF) | ((fs & 0x10) << 10)
        else:
            return self.system_bus.read(paddress)
        
    def mmu_write(self, vaddress, value, instruction=False):
        fs = None
        try:
            paddress = self._mmu_translate(vaddress, read_access=False, instruction=instruction)
        except SectionTranslationFault as ex:
            fs = 0x5
        except PageTranslationFault as ex:
            fs = 0x7
        except SectionDomainFault as ex:
            fs = 0x9
        except PageDomainFault as ex:
            fs = 0xB
        except SectionPermissionFault as ex:
            fs = 0xD
        except PagePermissionFault as ex:
            fs = 0xF
        
        if fs:
            if instruction:
                self._IFAR().value = vaddress
                self._IFSR().value = (fs & 0xF) | ((fs & 0x10) << 10)
            else:
                self._DFAR().value = vaddress
                self._DFSR().value = ex.domain << 4 | (fs & 0xF) | ((fs & 0x10) << 10) | (1 << 11)
        else:
            self.system_bus.write(paddress, value)
                
    def fetch_next_op(self):
        self.logger.info("Fetching next opcode from address (%s)", hex(self.ip.value))
        op = self.mmu_read(self.ip.value, instruction=True)
        return op.value
    
    def init_ophandlers(self):
        def def_LDR_LITERAL_OP(op):
            skip = False
            # LDR (literal)
            add = ((op & self.LDR_LITERAL_U) != 0)
            rt = (op & self.LDR_LITERAL_RT) >> self.LDR_LITERAL_RT_SHIT
            imm = op & self.LDR_LITERAL_IMM
            base = self.get_ip() & (~ 0x3)
            address = (base + imm) if add else (base - imm)
            data = self.mmu_read(address)
            if rt == 0xF:
                if not (address & 3):
                    self._LoadWritePC(data)
                    skip = True
                else:
                    raise Unpredictable()
            elif not (address & 3):
                self.register_write(rt, data)
            else:
                raise NotImplementedOpCode()
            
            return skip
            
        def def_LDR_IMMEDIATE_OP(op):
            # LDR (immediate, ARM)
            rn = (op & self.LDR_IMMEDIATE_RN) >> self.LDR_IMMEDIATE_RN_SHIFT
            rt = (op & self.LDR_IMMEDIATE_RT) >> self.LDR_IMMEDIATE_RT_SHIFT
            imm = (op & self.LDR_IMMEDIATE_IMM)
            
            if rn == 0xF:
                skip = self.op_handlers['LDR_LITERAL_OP'](op)
                return skip
            
            if not (op & self.LDR_IMMEDIATE_P) and op & self.LDR_IMMEDIATE_W:
                #FIXME see LDRT
                raise NotImplementedOpCode()
            
            if rn == 0xD and not (op & self.LDR_IMMEDIATE_P) and op & self.LDR_IMMEDIATE_U and not (op & self.LDR_IMMEDIATE_W) and imm == 0x4:
                skip = self.op_handlers['POP_OP2'](op)
                return skip

            index = (op & self.LDR_IMMEDIATE_P) != 0
            add = (op & self.LDR_IMMEDIATE_U) != 1
            wback = not (op & self.LDR_IMMEDIATE_P) and op & self.LDR_IMMEDIATE_W
             
            base = self.register_read(rn).value
            offset_addr = (base + imm) if add else (base - imm)
            address = offset_addr if index else base
            data = self.mmu_read(address)
            if wback:
                self.register_write(rn, offset_addr)

            self.register_write(rt, data)
            return False
            
        def def_LDR_REGISTER_OP(op):
            skip = False
            p = op & self.LDR_REGISTER_P
            w = op & self.LDR_REGISTER_W
            u = op & self.LDR_REGISTER_U
            rt = (op & self.LDR_REGISTER_RT) >> self.LDR_REGISTER_RT_SHIFT
            rn = (op & self.LDR_REGISTER_RN) >> self.LDR_REGISTER_RN_SHIFT
            imm = (op & self.LDR_REGISTER_IMM) >> self.LDR_REGISTER_IMM_SHIFT
            type = (op & self.LDR_REGISTER_TYPE) >> self.LDR_REGISTER_TYPE_SHIFT
            rm = op & self.LDR_REGISTER_RM
            if p == 0 and w != 0:
                #FIXME see LDRT
                raise NotImplementedOpCode()
            index = p != 0
            add = u != 0
            wback = (p == 0) or (w != 0)
            shift_t, shift_n = self._DecodeImmShift(type, imm)
            if rm == 0xF:
                raise Unpredictable()
            if wback and (rn == 0xF or rn == rt):
                raise Unpredictable()
            
            carry = self.cpsr.value & self.PROCESSOR_C and 1
            offset = self._SHIFT(self.register_read(rm).value, shift_t, shift_n, carry)
            value = self.register_read(rn).value
            offset_addr = (value + offset) if add else (value - offset)
            address = offset_addr if index else self.register_read(rn)
            data = self.mmu_read(address)
            if wback:
                self.register_write(rn, c_uint32(data))
            if rt == 0xF:
                if address & 3 == 0:
                    self._LoadWritePC(data)
                    skip = True
                else:
                    raise Unpredictable()
            #Check the reference her for more states
            else:
                self.register_write(rt, data)
            return skip
            
        def def_STR_IMMEDIATE_OP(op):
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
                skip = self.op_handlers['PUSH_OP2'](op)
                return skip
            
            index = (p != 0)
            add = (u != 0)
            wback = (not p) or (w != 0)
            
            if wback and (rn == 15 or rn == rt):
                raise Unpredictable()
            
            rn_value = self.register_read(rn).value
            offset_addr = (rn_value + imm) if add else (rn_value - imm)
            address = offset_addr if index else rn_value
            self.mmu_write(address, self.register_read(rt))
            
            if wback:
                self.register_write(rn, c_uint32(offset_addr))
                
            return False
        
        def def_STR_REGISTER_OP(op):
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
                
            self.mmu_write(address, data)
            if wback:
                self.register_write(rn, c_uint32(offset_addr))
                
            return False
                
        def def_B_OP(op):
            imm = self._SignExtend26to32((op & self.B_IMM) << 2)
            self.set_ip(c_uint32(self.get_ip() + imm))
            return True

        def def_BL_OP(op):
            imm = self._SignExtend26to32((op & self.B_IMM) << 2)
            lr = self.get_lr_link()
            self.register_write(14, c_uint32(lr))
            self.set_ip(c_uint32(self.get_ip() + imm))
            return True
        
        def def_BX_OP(op):
            rm = op & self.BX_RM
            address = self.register_read(rm)
            self._BXWritePC(address)
            return True

        def def_LDM_OP(op):
            w = op & self.LDM_W
            register_list = op & self.LDM_REGISTERS
            bit_count = self._BitCount(register_list)
            rn = (op & self.LDM_RN) >> self.LDM_RN_SHIFT
            if w != 0 and rn == 0xD and bit_count >=2:
                skip = self.op_handlers['POP_OP1'](op)
                return skip
            
            wback = (w != 0)
            if rn == 0xF or bit_count < 1:
                raise Unpredictable()
            
            rn_index = 1 << rn
            if wback and (register_list & rn_index):
                raise Unpredictable()
            
            address = self.register_read(rn).value
            for i in range(15):
                if register_list & (1 << i):
                    self.register_write(i, self.mmu_read(address))
                    address += 4
                
            if register_list & (1 << 15):
                self._BXWritePC(self.mmu_read(address))

            if wback:
                self.register_write(rn, c_uint32(address))
            
            return False

        def def_STM_OP(op):
            w = op & self.LDM_W
            register_list = op & self.STM_REGISTERS
            bit_count = self._BitCount(register_list)
            rn = (op & self.STM_RN) >> self.STM_RN_SHIFT
            if rn == 0xF or bit_count < 1:
                raise Unpredictable()
            
            wback = (w != 0)
            address = self.register_read(rn).value
            for i in range(15):
                if register_list & (1 << i):
                    #TODO:Check the reference for the branching here, not sure what it means !!
                    #if rn == i and wback and 
                    self.mmu_write(address, self.register_read(i))
                    address += 4
                
            if register_list & (1 << 15):
                # PCStoreValue
                raise NotImplementedOpCode()
            if wback:
                self.register_write(rn, c_uint32(address))
                
            return False


        def def_PUSH_OP1(op):
            register_list = op & self.PUSH_OP1_REGISTERS
            bit_count = self._BitCount(register_list)
            if register_list & (1 << 13):
                raise Unpredictable()

            if bit_count < 2:
                # see STMDB / STMFD
                raise NotImplementedOpCode()
            
            address = self.register_read(13).value - (4 * bit_count)
            for i in range(15):
                if register_list & (1 << i):
                    #TODO:Check the reference for the branching here, not sure what it means !!
                    #if rn == i and wback and 
                    self.mmu_write(address, self.register_read(i))
                    address += 4
            if register_list & (1 << 15):
                # see PCStoreValue(pc)
                raise NotImplementedOpCode()
            
            self.register_read(13).value -= (4 * bit_count)
            return False
            
        def def_PUSH_OP2(op):
            rt = (op & self.PUSH_OP2_RT) >> self.PUSH_OP2_RT_SHIFT
            if rt == 0xD:
                raise Unpredictable()
            if rt == 0xF:
                # see PCStoreValue(pc)
                raise NotImplementedOpCode()

            address = self.register_read(13).value - 4
            self.mmu_write(address, self.register_read(rt))
            self.register_read(13).value -= 4
            return False
            
        def def_POP_OP1(op):
            skip = False
            register_list = op & self.POP_OP1_REGISTERS
            bit_count = self._BitCount(register_list)
            if bit_count < 2:
                skip = self.op_handlers['LDM_OP'](op)
                return skip
            if register_list & (1 << 13):
                raise Unpredictable()
            
            address = self.register_read(13).value
            for i in range(15):
                if register_list & (1 << i):
                    #TODO:Check the reference for the branching here, not sure what it means !!
                    #if rn == i and wback and 
                    self.register_write(i, self.mmu_read(address))
                    address += 4
            
            if register_list & (1 << 15):
                self._BXWritePC(self.mmu_read(address))
                skip = True
            
            self.register_read(13).value += (4 * bit_count)
            return skip
            
        def def_POP_OP2(op):
            skip = False
            rt = (op & self.POP_OP2_RT) >> self.POP_OP2_RT_SHIFT
            if rt == 0xD:
                raise Unpredictable()
            
            address = self.register_read(13).value 
            
            if rt == 0xF:
                self._BXWritePC(self.mmu_read(address))
                skip = True
            else:
                self.register_write(rt, self.mmu_read(address))
            
            self.register_read(13).value += 4
            return skip

        def def_CMP_REGISTER_OP(op):
            rn = (op & self.CMP_REGISTER_RN) >> self.CMP_REGISTER_RN_SHIFT
            rm = op & self.CMP_REGISTER_RM
            type = (op & self.CMP_REGISTER_TYPE) >> self.CMP_REGISTER_TYPE_SHIFT
            imm = (op & self.CMP_REGISTER_IMM) >> self.CMP_REGISTER_IMM_SHIFT
            shift_t, shift_n = self._DecodeImmShift(type, imm)
            carry = self.cpsr.value & self.PROCESSOR_C and 1
            shifted = self._SHIFT(self.register_read(rm).value, shift_t, shift_n, carry)
            complemented_shifted = c_uint64(-shifted).value
            result, carry, overflow = self._AddWithCarry(self.register_read(rn).value, complemented_shifted, 0)
            
            self.cpsr.value |= (result & 0x80000000) and self.PROCESSOR_N
            self.cpsr.value |= (result == 0) and self.PROCESSOR_Z
            self.cpsr.value |= carry and self.PROCESSOR_C
            self.cpsr.value |= overflow and self.PROCESSOR_V
            return False
        
        def def_CMP_IMMEDIATE_OP(op):
            imm = op & self.CMP_IMMEDIATE_IMM
            imm = self._ARMExpandImm(imm)
            rn = (op & self.CMP_IMMEDIATE_RN) >> self.CMP_IMMEDIATE_RN_SHIFT
            result, carry, overflow = self._AddWithCarry(self.register_read(rn).value, self._NOT(imm), 1)
            
            self.cpsr.value |= (result & 0x80000000) and self.PROCESSOR_N
            self.cpsr.value |= (result == 0) and self.PROCESSOR_Z
            self.cpsr.value |= carry and self.PROCESSOR_C
            self.cpsr.value |= overflow and self.PROCESSOR_V
            return False
        
        def def_TST_IMMEDIATE_OP(op):
            rn = (op & self.TST_IMMEDIATE_RN) >> self.TST_IMMEDIATE_RN_SHIFT
            imm = op & self.TST_IMMEDIATE_IMM
            carry = self.cpsr.value & self.PROCESSOR_C and 1
            result, carry = self._ARMExpandImm_C(imm, carry)
            
            self.cpsr.value |= (result & 0x80000000) and self.PROCESSOR_N
            self.cpsr.value |= (result == 0) and self.PROCESSOR_Z
            self.cpsr.value |= carry and self.PROCESSOR_C
            return False
        
        def def_MSR_REGISTER_OP(op):
            #TODO:Support non-maskable interrupts
            rn = op & self.MSR_REGISTER_RN
            if rn == 0xF:
                raise Unpredictable()
            mask = (op & self.MSR_REGISTER_MASK) >> self.MSR_REGISTER_MASK_SHIFT
            if mask == 0x0:
                raise Unpredictable()
            write_spsr = (op & self.MSR_REGISTER_R) != 0
            privileged = self._IsPrivilegedMode()
            mask = ((0x8 & mask) and 0xFF000000) | ((0x4 & mask) and 0x00FF0000) | ((0x2 & mask) and privileged and 0x0000FF00) | ((0x1 & mask) and privileged and 0x000000FF)
            
            secure = self._IsSecure()
            if not secure:
                scr = self._SCR().value
                f = (scr & self.SCR_FW) == 0
                a = (scr & self.SCR_AW) == 0
                mask = (mask & ((f and 0xFFFFFFBF) & (a and 0xFFFFFEFF)))
            before_mask = self.register_read(rn).value
            after_mask = before_mask & mask
            
            value = self.cpsr.value
            if privileged:
                if write_spsr:
                    MODE = value & self.PROCESSOR_MODE
                    self.spsr_registers[MODE] = before_mask
                else:
                    unchanging_bits = value & self._NOT(mask)
                    result = unchanging_bits | after_mask
                    if (not secure) and (result & self.PROCESSOR_MODE) == self.processor_modes['monitor']:
                        raise Unpredictable()
                    self.cpsr.value = result
            else:
                unchanging_bits = value & self._NOT(mask)
                self.cpsr.value = unchanging_bits | after_mask
                
            return False
        
        def def_MVN_IMMEDIATE_OP(op):
            skip = False
            s = op & self.MVN_IMMEDIATE_S
            set_flags = (s != 0)
            rd = (op & self.MVN_IMMEDIATE_RD) >> self.MVN_IMMEDIATE_RD_SHIFT
            imm = op & self.MVN_IMMEDIATE_IMM
            carry = self.cpsr.value & self.PROCESSOR_C and 1
            imm, carry = self._ARMExpandImm_C(imm, carry)
            result = self._NOT(imm)
            if rd == 0xF:
                self._ALUWritePC(c_uint32(result))
                skip = True
            else:
                self.register_write(rd, c_uint32(result))
                if set_flags:
                    self.cpsr.value |= (result & 0x80000000) and self.PROCESSOR_N
                    self.cpsr.value |= (result == 0) and self.PROCESSOR_Z
                    self.cpsr.value |= carry and self.PROCESSOR_C
            return skip
            
        def def_MVN_REGISTER_SH_OP(op):
            rd = (op & self.MVN_REGISTER_SH_RD) >> self.MVN_REGISTER_SH_RD_SHIFT
            rs = (op & self.MVN_REGISTER_SH_RS) >> self.MVN_REGISTER_SH_RS_SHIFT
            type = (op & self.MVN_REGISTER_SH_TYPE) >> self.MVN_REGISTER_SH_TYPE_SHIFT
            rm = op & self.MVN_REGISTER_SH_RM
            s = op & self.MVN_REGISTER_SH_S
            set_flags = (s != 0)
            shift_t = self._DecodeRegShift(type)
            
            if rd == 0xF or rm == 0xF or rs == 0xF:
                raise Unpredictable()
            
            rs_value = self.register_read(rs).value
            shift_n = rs_value & 0xFF
            carry = self.cpsr.value & self.PROCESSOR_C and 1
            shifted, carry = self._SHIFT_C(self.register_read(rm).value, shift_t, shift_n, carry)
            result = self._NOT(shifted)
            self.register_write(rd, c_uint32(result))
            if set_flags:
                self.cpsr.value |= (result & 0x80000000) and self.PROCESSOR_N
                self.cpsr.value |= (result == 0) and self.PROCESSOR_Z
                self.cpsr.value |= carry and self.PROCESSOR_C
            
            return False

        def def_BIC_IMMEDIATE_OP(op):
            skip = False
            rd = (op & self.BIC_IMMEDIATE_RD) >> self.BIC_IMMEDIATE_RD_SHIFT
            rn = (op & self.BIC_IMMEDIATE_RN) >> self.BIC_IMMEDIATE_RN_SHIFT
            imm = op & self.BIC_IMMEDIATE_IMM
            s = op & self.BIC_IMMEDIATE_S
            set_flags = (s != 0)
            
            if rd == 0xF and s:
                #FIXME see SUBS PC, LR and related instructions
                raise NotImplementedOpCode()
            
            carry = (self.cpsr.value & self.PROCESSOR_C) and 1
            imm, carry = self._ARMExpandImm_C(imm, carry)
            result = (self.register_read(rn).value & self._NOT(imm))
            if rd == 0xF:
                self._ALUWritePC(c_uint32(result))
                skip = True
            else:
                self.register_write(rd, c_uint32(result))
                if set_flags:
                    self.cpsr.value |= (result & 0x80000000) and self.PROCESSOR_N
                    self.cpsr.value |= (result == 0) and self.PROCESSOR_Z
                    self.cpsr.value |= carry and self.PROCESSOR_C
            return skip

        def def_MRS_OP(op):
            rd = (op & self.MRS_RD) >> self.MRS_RD_SHIFT
            read_spsr = ((op & self.MRS_READ_SAVED) != 0)
            
            value = self.cpsr.value
            if self._IsPrivilegedMode():
                if read_spsr:
                    MODE = value & self.PROCESSOR_MODE
                    value = self.spsr_registers[MODE]
                
                value &= self.MRS_SVC_MASK
            else:
                value &= self.MRS_USER_MASK
            
            self.register_write(rd, c_uint32(value))
            return False

        def def_ORR_REGISTER_OP(op):
            skip = False
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
            carry = (self.cpsr.value & self.PROCESSOR_C) and 1
            shifted, carry = self._SHIFT_C(self.register_read(rm).value, shift_t, shift_n, carry)
            result = self.register_read(rn).value | shifted
            
            if rd == 0xF:
                self._ALUWritePC(c_uint32(result))
                skip = True
            else:
                self.register_write(rd, c_uint32(result))
                if set_flags:
                    self.cpsr.value |= (result & 0x80000000) and self.PROCESSOR_N
                    self.cpsr.value |= (result == 0) and self.PROCESSOR_Z
                    self.cpsr.value |= carry and self.PROCESSOR_C
            return skip

        def def_ORR_IMMEDIATE_OP(op):
            skip = False
            imm = op & self.ORR_IMMEDIATE_IMM
            rn = (op & self.ORR_IMMEDIATE_RN) >> self.ORR_IMMEDIATE_RN_SHIFT
            rd = (op & self.ORR_IMMEDIATE_RD) >> self.ORR_IMMEDIATE_RD_SHIFT
            s = op & self.ORR_IMMEDIATE_S
            set_flags = (s != 0)
            
            if rd == 0xF and s:
                #FIXME see SUBS PC, LR and related instructions
                raise NotImplementedOpCode()
            
            carry = (self.cpsr.value & self.PROCESSOR_C) and 1
            imm, carry = self._ARMExpandImm_C(imm, carry)
            result = self.register_read(rn).value | imm
            
            if rd == 0xF:
                self._ALUWritePC(c_uint32(result))
                skip = True
            else:
                self.register_write(rd, c_uint32(result))
                if set_flags:
                    self.cpsr.value |= (result & 0x80000000) and self.PROCESSOR_N
                    self.cpsr.value |= (result == 0) and self.PROCESSOR_Z
                    self.cpsr.value |= carry and self.PROCESSOR_C
            return skip

        def def_ORR_REGISTER_SH_OP(op):
            rd = (op & self.ORR_REGISTER_SH_RD) >> self.ORR_REGISTER_SH_RD_SHIFT
            rn = (op & self.ORR_REGISTER_SH_RN) >> self.ORR_REGISTER_SH_RN_SHIFT
            rm = op & self.ORR_REGISTER_SH_RM
            rs = (op & self.ORR_REGISTER_SH_RS) >> self.ORR_REGISTER_SH_RS_SHIFT
            type = (op & self.ORR_REGISTER_SH_TYPE) >> self.ORR_REGISTER_SH_TYPE_SHIFT
            s = op & self.ORR_REGISTER_SH_S
            set_flags = (s != 0)
            
            if rd == 0xF or rm == 0xF or rn == 0xF or rs == 0xF:
                raise Unpredictable()
            
            shift_t = self._DecodeRegShift(type)
            rs_value = self.register_read(rs).value
            shift_n = rs_value & 0xFF
            carry = (self.cpsr.value & self.PROCESSOR_C) and 1
            shifted, carry = self._SHIFT_C(self.register_read(rm).value, shift_t, shift_n, carry)
            result = self.register_read(rn).value | shifted
            self.register_write(rd, c_uint32(result))
            if set_flags:
                    self.cpsr.value |= (result & 0x80000000) and self.PROCESSOR_N
                    self.cpsr.value |= (result == 0) and self.PROCESSOR_Z
                    self.cpsr.value |= carry and self.PROCESSOR_C
            return False
                
        def def_BIC_REGISTER_SH_OP(op):
            rd = (op & self.BIC_REGISTER_SH_RD) >> self.BIC_REGISTER_SH_RD_SHIFT
            rn = (op & self.BIC_REGISTER_SH_RN) >> self.BIC_REGISTER_SH_RN_SHIFT
            rm = op & self.BIC_REGISTER_SH_RM
            rs = (op & self.BIC_REGISTER_SH_RS) >> self.BIC_REGISTER_SH_RS_SHIFT
            type = (op & self.BIC_REGISTER_SH_TYPE) >> self.BIC_REGISTER_SH_TYPE_SHIFT
            s = op & self.BIC_REGISTER_SH_S
            set_flags = (s != 0)
            
            if rd == 0xF or rm == 0xF or rn == 0xF or rs == 0xF:
                raise Unpredictable()
            
            shift_t = self._DecodeRegShift(type)
            rs_value = self.register_read(rs).value
            shift_n = rs_value & 0xFF
            carry = (self.cpsr.value & self.PROCESSOR_C) and 1
            shifted, carry = self._SHIFT_C(self.register_read(rm).value, shift_t, shift_n, carry)
            result = self.register_read(rn).value & self._NOT(shifted)
            self.register_write(rd, c_uint32(result))
            if set_flags:
                    self.cpsr.value |= (result & 0x80000000) and self.PROCESSOR_N
                    self.cpsr.value |= (result == 0) and self.PROCESSOR_Z
                    self.cpsr.value |= carry and self.PROCESSOR_C
            return False

        def def_MCR_OP(op):
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
            return False

        def def_MRC_OP(op):    
            opc1 = (op & self.MRC_OPC1) >> self.MRC_OPC1_SHIFT
            crn = (op & self.MRC_CRN) >> self.MRC_CRN_SHIFT
            rt = (op & self.MRC_RT) >> self.MRC_RT_SHIFT
            coproc = (op & self.MRC_COPROC) >> self.MRC_COPROC_SHIFT
            opc2 = (op & self.MRC_OPC2) >> self.MRC_OPC2_SHIFT
            crm = op & self.MRC_CRM
            if coproc == 0xF:
                value = self._CP15_read(crn, opc1, crm, opc2)
                self.register_write(rt, value)
            else:
                raise NotImplementedOpCode()
            return False

        def def_LSR_IMMEDIATE_OP(op):
            skip = False
            imm = (op & self.LSR_IMMEDIATE_IMM) >> self.LSR_IMMEDIATE_IMM_SHIFT
            rd = (op & self.LSR_IMMEDIATE_RD) >> self.LSR_IMMEDIATE_RD_SHIFT
            rm = op & self.LSR_IMMEDIATE_RM
            s = op & self.LSR_IMMEDIATE_S
            set_flags = (s!=0)
            
            _, shift_n = self._DecodeImmShift(0x1, imm)
            carry = self.cpsr.value & self.PROCESSOR_C and 1
            result, carry = self._SHIFT_C(self.register_read(rm).value, self.SRType_LSR, shift_n, carry)
            if rd == 0xF:
                self._ALUWritePC(c_uint32(result))
                skip = True
            else:
                self.register_write(rd, c_uint32(result))
                if set_flags:
                    self.cpsr.value |= (result & 0x80000000) and self.PROCESSOR_N
                    self.cpsr.value |= (result == 0) and self.PROCESSOR_Z
                    self.cpsr.value |= carry and self.PROCESSOR_C
            return skip

        def def_LSL_IMMEDIATE_OP(op):
            skip = False
            imm = (op & self.LSL_IMMEDIATE_IMM) >> self.LSL_IMMEDIATE_IMM_SHIFT
            rd = (op & self.LSL_IMMEDIATE_RD) >> self.LSL_IMMEDIATE_RD_SHIFT
            rm = op & self.LSL_IMMEDIATE_RM
            s = op & self.LSL_IMMEDIATE_S
            set_flags = (s!=0)

            _, shift_n = self._DecodeImmShift(0x0, imm)
            carry = self.cpsr.value & self.PROCESSOR_C and 1
            result, carry = self._SHIFT_C(self.register_read(rm).value, self.SRType_LSL, shift_n, carry)
            if rd == 0xF:
                self._ALUWritePC(c_uint32(result))
                skip = True
            else:
                self.register_write(rd, c_uint32(result))
                if set_flags:
                    self.cpsr.value |= (result & 0x80000000) and self.PROCESSOR_N
                    self.cpsr.value |= (result == 0) and self.PROCESSOR_Z
                    self.cpsr.value |= carry and self.PROCESSOR_C
            return skip

        def def_AND_REGISTER_OP(op):
            skip = False
            s = op & self.AND_REGISTER_S
            rn = (op & self.AND_REGISTER_RN) >> self.AND_REGISTER_RN_SHIFT
            rd = (op & self.AND_REGISTER_RD) >> self.AND_REGISTER_RD_SHIFT
            rm = op & self.AND_REGISTER_RM
            imm = (op & self.AND_REGISTER_IMM) >> self.AND_REGISTER_IMM_SHIFT
            type = (op & self.AND_REGISTER_TYPE) >> self.AND_REGISTER_TYPE_SHIFT
            set_flags = (s!=0)
            
            if rd == 0xF and (s != 0):
                #FIXME: see SUBS PC, LR and related instructions
                raise NotImplementedOpCode()
            
            carry = self.cpsr.value & self.PROCESSOR_C and 1
            shift_t, shift_n = self._DecodeImmShift(type, imm)
            shifted, carry = self._SHIFT_C(self.register_read(rm).value, shift_t, shift_n, carry)
            result = self.register_read(rn).value | shifted 
            if rd == 0xF:
                self._ALUWritePC(c_uint32(result))
                skip = True
            else:
                self.register_write(rd, c_uint32(result))
                if set_flags:
                    self.cpsr.value |= (result & 0x80000000) and self.PROCESSOR_N
                    self.cpsr.value |= (result == 0) and self.PROCESSOR_Z
                    self.cpsr.value |= carry and self.PROCESSOR_C
            return skip

        def def_AND_IMMEDIATE_OP(op):
            skip = False
            rn = (op & self.AND_IMMEDIATE_RN) >> self.AND_IMMEDIATE_RN_SHIFT
            rd = (op & self.AND_IMMEDIATE_RD) >> self.AND_IMMEDIATE_RD_SHIFT
            imm = op & self.AND_IMMEDIATE_IMM
            s = op & self.AND_IMMEDIATE_S
            set_flags = s != 0
            
            if rd == 0xF and s:
                #FIXME see SUBS PC, LR and related instructions
                raise NotImplementedOpCode()
            
            carry = self.cpsr.value & self.PROCESSOR_C and 1
            imm, carry = self._ARMExpandImm_C(imm, carry)
            result = self.register_read(rn).value & imm
            if rd == 0xF:
                self._ALUWritePC(c_uint32(result))
                skip = True
            else:
                self.register_write(rd, c_uint32(result))
                if set_flags:
                    self.cpsr.value |= (result & 0x80000000) and self.PROCESSOR_N
                    self.cpsr.value |= (result == 0) and self.PROCESSOR_Z
                    self.cpsr.value |= carry and self.PROCESSOR_C
            return skip
        
        def def_ADD_IMMEDIATE_OP(op):
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
            return False

        def def_ADD_REGISTER_OP(op):
            skip = False
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
                self._ALUWritePC(c_uint32(result))
                skip = True
            else:
                self.register_write(rd, c_uint32(result))
                
                if set_flags:
                    self.cpsr.value |= (result & 0x80000000) and self.PROCESSOR_N
                    self.cpsr.value |= (result == 0) and self.PROCESSOR_Z
                    self.cpsr.value |= carry and self.PROCESSOR_C
                    self.cpsr.value |= overflow and self.PROCESSOR_V
            return skip

        def def_SUB_REGISTER_OP(op):
            skip = False
            imm = (op & self.SUB_REGISTER_IMM) >> self.SUB_REGISTER_IMM_SHIFT
            rn = (op & self.SUB_REGISTER_RN) >> self.SUB_REGISTER_RN_SHIFT
            rd = (op & self.SUB_REGISTER_RD) >> self.SUB_REGISTER_RD_SHIFT
            type = (op & self.SUB_REGISTER_TYPE) >> self.SUB_REGISTER_TYPE_SHIFT
            rm = op & self.SUB_REGISTER_RM
            s = op & self.SUB_REGISTER_S
            set_flags = (s != 0)
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
                self._ALUWritePC(c_uint32(result))
                skip = True
            else:
                self.register_write(rd, c_uint32(result))
                if set_flags:
                    self.cpsr.value |= (result & 0x80000000) and self.PROCESSOR_N
                    self.cpsr.value |= (result == 0) and self.PROCESSOR_Z
                    self.cpsr.value |= carry and self.PROCESSOR_C
                    self.cpsr.value |= overflow and self.PROCESSOR_V
            return skip

        def def_LDRB_IMMEDIATE_OP(op):
            rn = (op & self.LDRB_IMMEDIATE_RN) >> self.LDRB_IMMEDIATE_RN_SHIFT
            rt = (op & self.LDRB_IMMEDIATE_RT) >> self.LDRB_IMMEDIATE_RT_SHIFT
            p = op & self.LDRB_IMMEDIATE_P
            u = op & self.LDRB_IMMEDIATE_U
            w = op & self.LDRB_IMMEDIATE_W
            imm = op & self.LDRB_IMMEDIATE_IMM
            
            if rn == 0xF:
                #FIXME see LDRB literal
                raise NotImplementedOpCode()
            if not p and w != 0:
                #FIXME see LDRBT
                raise NotImplementedOpCode()
            
            index = p != 0
            add = u != 0
            wback = (p == 0) or (w != 0)
            
            if rt == 0xF or (wback and rt == rn):
                raise Unpredictable()
            
            value = self.register_read(rn).value
            offset_addr = (value + imm) if add else (value - imm)
            address = offset_addr if index else value
            tmp_value = self.mmu_read(address).value
            self.register_write(rt, c_uint32(tmp_value & 0xFF))
            if wback:
                self.register_write(rn, c_uint32(offset_addr))
            return False

        def def_SUB_IMMEDIATE_OP(op):
            skip = False
            imm = op & self.SUB_IMMEDIATE_IMM
            rn = (op & self.SUB_IMMEDIATE_RN) >> self.SUB_IMMEDIATE_RN_SHIFT
            rd = (op & self.SUB_IMMEDIATE_RD) >> self.SUB_IMMEDIATE_RD_SHIFT
            set_flags = ((op & self.SUB_IMMEDIATE_S) != 0)
            imm = self._ARMExpandImm(imm)
            
            if rd == 0xF and set_flags:
                #FIXME SUBS PC, LR and related instructions
                raise NotImplementedOpCode()
                
            if rn == 0xD:
                #FIXME see SUB (SP minus register)
                raise NotImplementedOpCode()
            
            if rn == 0xF and not set_flags:
                # FIXME: see ADR ( tmp hack for now)
                tmp = (op & 0x00C00000) >> 22
                if tmp == 1:
                    add = False
                elif tmp == 2:
                    add = True
                result = (self.get_ip() + imm) if add else (self.get_ip() - imm)
            else:
                result, carry, overflow = self._AddWithCarry(self.register_read(rn).value, self._NOT(imm), 1)
            
            if rd == 0xF:
                self._ALUWritePC(c_uint32(result))
                skip = True
            else:
                self.register_write(rd, c_uint32(result))
                if set_flags:
                    self.cpsr.value |= (result & 0x80000000) and self.PROCESSOR_N
                    self.cpsr.value |= (result == 0) and self.PROCESSOR_Z
                    self.cpsr.value |= carry and self.PROCESSOR_C
                    self.cpsr.value |= overflow and self.PROCESSOR_V
            return skip
        
        def def_MOV_IMMEDIATE_OP1(op):
            # FIXME
            skip = False
            rd = (op & self.MOV_IMMEDIATE_OP1_RD) >> self.MOV_IMMEDIATE_OP1_RD_SHIFT
            s = op & self.MOV_IMMEDIATE_OP1_S
            set_flags = (s!=0)
            imm = op & self.MOV_IMMEDIATE_OP1_IMM
            carry = self.cpsr.value & self.PROCESSOR_C and 1
            result, carry = self._ARMExpandImm_C(imm, carry)
            if rd == 0xF:
                self._ALUWritePC(c_uint32(result))
                skip = True
            else:
                self.register_write(rd, c_uint32(result))
                if set_flags:
                    self.cpsr.value |= (result & 0x80000000) and self.PROCESSOR_N
                    self.cpsr.value |= (result == 0) and self.PROCESSOR_Z
                    self.cpsr.value |= carry and self.PROCESSOR_C
            return skip

        def def_MOV_REGISTER_OP(op):
            skip = False
            rd = (op & self.MOV_REGISTER_RD) >> self.MOV_REGISTER_RD_SHIFT
            rm = op & self.MOV_REGISTER_RM
            s = op & self.MOV_REGISTER_S
            set_flags = (s != 0)
            result = self.register_read(rm)
            if rd == 0xF:
                self._ALUWritePC(result)
                skip = True
            else:
                self.register_write(rd, result)
                if set_flags:
                    self.cpsr.value |= (result.value & 0x80000000) and self.PROCESSOR_N
                    self.cpsr.value |= (result.value == 0) and self.PROCESSOR_Z
            return skip
        
        def def_BFC_OP(op):
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
            return False
        
        def def_MOV_IMMEDIATE_OP2(op):
            rd = (op & self.MOV_IMMEDIATE_OP1_RD) >> self.MOV_IMMEDIATE_OP1_RD_SHIFT
            imm1 = op & self.MOV_IMMEDIATE_OP1_IMM
            imm2 = (op & self.MOV_IMMEDIATE_OP2_IMM) >> 4
            imm = imm1 | imm2
            
            if rd == 0xF:
                raise Unpredictable()
            else:
                self.register_write(rd, c_uint32(imm))


        self.op_handlers = {            
                            'LDR_LITERAL_OP'    : def_LDR_LITERAL_OP,
                            'LDR_IMMEDIATE_OP'  : def_LDR_IMMEDIATE_OP,
                            'LDRB_IMMEDIATE_OP' : def_LDRB_IMMEDIATE_OP,
                            'LDR_REGISTER_OP'   : def_LDR_REGISTER_OP,
                            'STR_IMMEDIATE_OP'  : def_STR_IMMEDIATE_OP,
                            'STR_REGISTER_OP'   : def_STR_REGISTER_OP,
                            'BFC_OP'            : def_BFC_OP,
                            'B_OP'              : def_B_OP,
                            'BL_OP'             : def_BL_OP,
                            'BX_OP'             : def_BX_OP,
                            'LDM_OP'            : def_LDM_OP,
                            'STM_OP'            : def_STM_OP,
                            'PUSH_OP1'          : def_PUSH_OP1,
                            'PUSH_OP2'          : def_PUSH_OP2,
                            'POP_OP1'           : def_POP_OP1,
                            'POP_OP2'           : def_POP_OP2,
                            'CMP_REGISTER_OP'   : def_CMP_REGISTER_OP,
                            'CMP_IMMEDIATE_OP'  : def_CMP_IMMEDIATE_OP,
                            'TST_IMMEDIATE_OP'  : def_TST_IMMEDIATE_OP,
                            'MSR_REGISTER_OP'   : def_MSR_REGISTER_OP,
                            'MVN_IMMEDIATE_OP'  : def_MVN_IMMEDIATE_OP,
                            'MVN_REGISTER_SH_OP': def_MVN_REGISTER_SH_OP,
                            'BIC_IMMEDIATE_OP'  : def_BIC_IMMEDIATE_OP,
                            'BIC_REGISTER_SH_OP': def_BIC_REGISTER_SH_OP,
                            'MRS_OP'            : def_MRS_OP,
                            'ADD_IMMEDIATE_OP'  : def_ADD_IMMEDIATE_OP,
                            'ADD_REGISTER_OP'   : def_ADD_REGISTER_OP,
                            'SUB_REGISTER_OP'   : def_SUB_REGISTER_OP,
                            'SUB_IMMEDIATE_OP'  : def_SUB_IMMEDIATE_OP,
                            'ORR_REGISTER_OP'   : def_ORR_REGISTER_OP,
                            'ORR_IMMEDIATE_OP'  : def_ORR_IMMEDIATE_OP,
                            'ORR_REGISTER_SH_OP': def_ORR_REGISTER_SH_OP,
                            'AND_REGISTER_OP'   : def_AND_REGISTER_OP,
                            'AND_IMMEDIATE_OP'  : def_AND_IMMEDIATE_OP,
                            'MCR_OP'            : def_MCR_OP,
                            'MRC_OP'            : def_MRC_OP,
                            'LSR_IMMEDIATE_OP'  : def_LSR_IMMEDIATE_OP,
                            'LSL_IMMEDIATE_OP'  : def_LSL_IMMEDIATE_OP,
                            'MOV_IMMEDIATE_OP1' : def_MOV_IMMEDIATE_OP1,
                            'MOV_IMMEDIATE_OP2' : def_MOV_IMMEDIATE_OP2,
                            'MOV_REGISTER_OP'   : def_MOV_REGISTER_OP
                            }
        
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
        
        for _, mode in processor_modes.items():
            self.registers[mode].append(self.ip)
        # Setting the processor in supervisor mode.
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
        midr = MIDR_RESET
        init_cp15_register(0, 0, 0, 0, True, midr) # VBAR ( common )
        init_cp15_register(12, 0, 0, 0, True, c_uint32()) # VBAR ( secure )
        init_cp15_register(12, 0, 0, 0, False, c_uint32()) # VBAR ( non-secure )
        init_cp15_register(12, 0, 0, 1, True, c_uint32()) # MVBAR ( secure )
        init_cp15_register(12, 0, 1, 0, True, c_uint32()) # ISR ( secure )
        init_cp15_register(12, 0, 1, 0, False, c_uint32()) # ISR ( non-secure )
        init_cp15_register(1, 0, 0, 0, True, c_uint32()) # SCTLR ( secure )
        init_cp15_register(1, 0, 0, 0, False, c_uint32()) # SCR ( secure )
        init_cp15_register(1, 0, 1, 0, True, c_uint32()) # SCTLR ( non-secure )
        init_cp15_register(2, 0, 0, 0, False, c_uint32()) # TTBR0 ( non-secure )
        init_cp15_register(2, 0, 0, 0, True, c_uint32()) # TTBR0 ( secure )
        init_cp15_register(2, 0, 0, 1, False, c_uint32()) # TTBR1 ( non-secure )
        init_cp15_register(2, 0, 0, 1, True, c_uint32()) # TTBR1 ( secure )
        init_cp15_register(2, 0, 0, 2, False, c_uint32()) # TTBCR ( non-secure )
        init_cp15_register(2, 0, 0, 2, True, c_uint32()) # TTBCR ( non-secure )
        init_cp15_register(3, 0, 0, 0, False, c_uint32()) # DACR ( secure )
        init_cp15_register(3, 0, 0, 0, True, c_uint32()) # DACR ( non-secure )
        init_cp15_register(5, 0, 0, 0, False, c_uint32()) # DFSR ( secure )
        init_cp15_register(5, 0, 0, 0, True, c_uint32()) # DFSR ( non-secure )
        init_cp15_register(5, 0, 0, 1, False, c_uint32()) # IFSR ( secure )
        init_cp15_register(5, 0, 0, 1, True, c_uint32()) # IFSR ( non-secure )
        init_cp15_register(6, 0, 0, 0, False, c_uint32()) # DFAR ( secure )
        init_cp15_register(6, 0, 0, 0, True, c_uint32()) # DFAR ( non-secure )
        init_cp15_register(6, 0, 0, 2, False, c_uint32()) # IFAR ( secure )
        init_cp15_register(6, 0, 0, 2, True, c_uint32()) # IFAR ( non-secure )
    
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
                    F, MODE = 1, self.processor_modes['monitor'] 
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
                            F = 1
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
        self._TakeException()
        skip = False
        self.op = op = self.fetch_next_op()

        global_env.dbg_event.wait()
        if global_env.STEPPING or op in global_env.GDB_ops or self.ip.value in global_env.GDB_IPs:
            global_env.dbg_breakpoint_hit = True
            global_env.dbg_event.clear()
            global_env.dbg_event.wait()
        
        condition = (op & self.CONDITION_MASK) >> self.CONDITION_MASK_SHIFT
        
        proceed = False
        h_cond = condition >> 1
        l_cond = condition & 1
        if condition == 14:
            proceed = True
        else:
            if h_cond == 0:
                res = self.cpsr.value & self.PROCESSOR_Z
            elif h_cond == 1:
                res = self.cpsr.value & self.PROCESSOR_C
            elif h_cond == 2:
                res = self.cpsr.value & self.PROCESSOR_N
            elif h_cond == 3:
                res = self.cpsr.value & self.PROCESSOR_V
            elif h_cond == 4:
                res = self.cpsr.value & self.PROCESSOR_C and not self.cpsr.value & self.PROCESSOR_Z
            elif h_cond == 5:
                overflow = ((self.cpsr.value & self.PROCESSOR_V) != 0)
                negative = ((self.cpsr.value & self.PROCESSOR_N) != 0)
                res = overflow == negative
            elif h_cond == 6:
                overflow = ((self.cpsr.value & self.PROCESSOR_V) != 0)
                negative = ((self.cpsr.value & self.PROCESSOR_N) != 0)
                zero = ((self.cpsr.value & self.PROCESSOR_Z) != 0)
                res = (overflow == negative) and zero
            elif h_cond == 7:
                res = True 

            if l_cond == 1:
                proceed = not res

        if not proceed:
            self.next_op()
            return

        if (op & self.LOAD_STORE_INS_MASK) == self.LOAD_STORE_INS:
            # Load/store word and unsigned byte mask
            if (op & self.LDR_LITERAL_OP_MASK) == self.LDR_LITERAL_OP:
                skip = self.op_handlers['LDR_LITERAL_OP'](op)
            elif (op & self.LDR_IMMEDIATE_OP_MASK) == self.LDR_IMMEDIATE_OP:
                skip = self.op_handlers['LDR_IMMEDIATE_OP'](op)
            elif (op & self.LDRB_IMMEDIATE_OP_MASK) == self.LDRB_IMMEDIATE_OP:
                skip = self.op_handlers['LDRB_IMMEDIATE_OP'](op)
            elif (op & self.LDR_REGISTER_OP_MASK) == self.LDR_REGISTER_OP:
                skip = self.op_handlers['LDR_REGISTER_OP'](op)
            elif (op & self.STR_IMMEDIATE_OP_MASK) == self.STR_IMMEDIATE_OP:
                skip = self.op_handlers['STR_IMMEDIATE_OP'](op)
            elif (op & self.STR_REGISTER_OP_MASK) == self.STR_REGISTER_OP:
                skip = self.op_handlers['STR_REGISTER_OP'](op)
            else:
                raise NotImplementedOpCode()
        elif (op & self.BRANCH_INS_MASK) == self.BRANCH_INS:
            if (op & self.B_OP_MASK) == self.B_OP:
                skip = self.op_handlers['B_OP'](op)
            elif (op & self.BL_OP_MASK) == self.BL_OP:
                skip = self.op_handlers['BL_OP'](op)
            elif (op & self.LDM_OP_MASK) == self.LDM_OP:
                skip = self.op_handlers['LDM_OP'](op)
            elif (op & self.STM_OP_MASK) == self.STM_OP:
                skip = self.op_handlers['STM_OP'](op)
            elif (op & self.PUSH_OP1_MASK) == self.PUSH_OP1:
                skip = self.op_handlers['PUSH_OP1'](op)
            elif (op & self.PUSH_OP2_MASK) == self.PUSH_OP2:
                skip = self.op_handlers['PUSH_OP2'](op)
            elif (op & self.POP_OP1_MASK) == self.POP_OP1:
                skip = self.op_handlers['POP_OP1'](op)
            elif (op & self.POP_OP2_MASK) == self.POP_OP2:
                skip = self.op_handlers['POP_OP2'](op)
            else:
                raise NotImplementedOpCode()
        elif (op & self.DATA_PROCESSING_INS_MASK) == self.DATA_PROCESSING_INS:
            if (op & self.ADD_IMMEDIATE_OP_MASK) == self.ADD_IMMEDIATE_OP:
                skip = self.op_handlers['ADD_IMMEDIATE_OP'](op)
            elif (op & self.ADD_REGISTER_OP_MASK) == self.ADD_REGISTER_OP:
                skip = self.op_handlers['ADD_REGISTER_OP'](op)       
            elif (op & self.SUB_REGISTER_OP_MASK) == self.SUB_REGISTER_OP:
                skip = self.op_handlers['SUB_REGISTER_OP'](op)
            elif (op & self.SUB_IMMEDIATE_OP_MASK) == self.SUB_IMMEDIATE_OP:
                skip = self.op_handlers['SUB_IMMEDIATE_OP'](op)
            elif (op & self.BFC_OP_MASK) == self.BFC_OP:
                skip = self.op_handlers['BFC_OP'](op)
            elif (op & self.CMP_REGISTER_OP_MASK) == self.CMP_REGISTER_OP:
                skip = self.op_handlers['CMP_REGISTER_OP'](op)
            elif (op & self.CMP_IMMEDIATE_OP_MASK) == self.CMP_IMMEDIATE_OP:
                skip = self.op_handlers['CMP_IMMEDIATE_OP'](op)
            elif (op & self.MOV_IMMEDIATE_OP1_MASK) == self.MOV_IMMEDIATE_OP1:
                skip = self.op_handlers['MOV_IMMEDIATE_OP1'](op)
            elif (op & self.MOV_IMMEDIATE_OP2_MASK) == self.MOV_IMMEDIATE_OP2:
                skip = self.op_handlers['MOV_IMMEDIATE_OP2'](op)
            elif (op & self.MOV_REGISTER_OP_MASK) == self.MOV_REGISTER_OP:
                skip = self.op_handlers['MOV_REGISTER_OP'](op)
            elif (op & self.LSL_IMMEDIATE_OP_MASK) == self.LSL_IMMEDIATE_OP:
                skip = self.op_handlers['LSL_IMMEDIATE_OP'](op)
            elif (op & self.LSR_IMMEDIATE_OP_MASK) == self.LSR_IMMEDIATE_OP:
                skip = self.op_handlers['LSR_IMMEDIATE_OP'](op)
            elif (op & self.ORR_IMMEDIATE_OP_MASK) == self.ORR_IMMEDIATE_OP:
                skip = self.op_handlers['ORR_IMMEDIATE_OP'](op)
            elif (op & self.ORR_REGISTER_OP_MASK) == self.ORR_REGISTER_OP:
                skip = self.op_handlers['ORR_REGISTER_OP'](op)
            elif (op & self.ORR_REGISTER_SH_OP_MASK) == self.ORR_REGISTER_SH_OP:
                skip = self.op_handlers['ORR_REGISTER_SH_OP'](op)
            elif (op & self.AND_REGISTER_OP_MASK) == self.AND_REGISTER_OP:
                skip = self.op_handlers['AND_REGISTER_OP'](op)
            elif (op & self.AND_IMMEDIATE_OP_MASK) == self.AND_IMMEDIATE_OP:
                skip = self.op_handlers['AND_IMMEDIATE_OP'](op)
            elif (op & self.TST_IMMEDIATE_OP_MASK) == self.TST_IMMEDIATE_OP:
                skip = self.op_handlers['TST_IMMEDIATE_OP'](op)
            elif (op & self.MVN_IMMEDIATE_OP_MASK) == self.MVN_IMMEDIATE_OP:
                skip = self.op_handlers['MVN_IMMEDIATE_OP'](op)
            elif (op & self.MVN_REGISTER_SH_OP_MASK) == self.MVN_REGISTER_SH_OP:
                skip = self.op_handlers['MVN_REGISTER_SH_OP'](op)
            elif (op & self.BIC_IMMEDIATE_OP_MASK) == self.BIC_IMMEDIATE_OP:
                skip = self.op_handlers['BIC_IMMEDIATE_OP'](op)
            elif (op & self.BIC_REGISTER_SH_OP_MASK) == self.BIC_REGISTER_SH_OP:
                skip = self.op_handlers['BIC_REGISTER_SH_OP'](op)
            elif (op & self.MRS_OP_MASK) == self.MRS_OP:
                skip = self.op_handlers['MRS_OP'](op)
            elif (op & self.MSR_REGISTER_OP_MASK) == self.MSR_REGISTER_OP:
                skip = self.op_handlers['MSR_REGISTER_OP'](op)
            elif (op & self.BX_OP_MASK) == self.BX_OP:
                skip = self.op_handlers['BX_OP'](op)
            else:
                raise NotImplementedOpCode()
        elif (op & self.SVC_COPROC_INS_MASK) == self.SVC_COPROC_INS: 
            if (op & self.SVC_OP_MASK) == self.SVC_OP:
                imm = op & self.SVC_IMM # Not used at all.
                self.interrupt_triggered(self.IRQ_SVC)
                skip = False
            elif (op & self.MCR_OP_MASK) == self.MCR_OP:
                skip = self.op_handlers['MCR_OP'](op)
            elif (op & self.MRC_OP_MASK) == self.MRC_OP:    
                skip = self.op_handlers['MRC_OP'](op)
            else:
                raise NotImplementedOpCode()
        else:
            raise InvalidInstructionOpCode()
        
        if not skip:
            self.next_op()

    
    def _SignExtend26to32(self, imm):
        sign = ((imm & (1 << 25)) != 0)
        if sign:
            result = ((~ imm) + 1) & ((1 << 26) - 1)
            result = -result
        else:
            result = imm

        return result
        
    
    
    def _BitCount(self, value):
        # register_list
        count = 0
        for x in range(32):
            count += (value & (1 << x)) and 1
            
        return count
                
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
    
    def _DecodeRegShift(self, type):
        if type == 0:
            shift_t = self.SRType_LSL 
        elif type == 1:
            shift_t = self.SRType_LSR
        elif type == 2:
            shift_t = self.SRType_ASR
        elif type == 3:
            shift_t = self.SRType_ROR
        
        return shift_t
    
    def _NOT(self, value):
        return c_uint32(~value).value

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
    
    def _ARMExpandImm(self, imm):
        carry = self.cpsr.value & self.PROCESSOR_C and 1
        result, _ = self._ARMExpandImm_C(imm, carry)
        return result
    
    def _ARMExpandImm_C(self, imm, carry_in):
        unrotated_value = imm & ((1 << 8) - 1)
        shift = (imm & (0xF << 8)) >> 8
        imm, carry_out = self._SHIFT_C(unrotated_value, self.SRType_ROR, 2*shift, carry_in)
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
        signed_sum = c_int64(op1).value + c_int64(op2).value + carry_in
        result = unsigned_sum & ((1 << 31) - 1)
        carry_out = 0 if result == unsigned_sum else 1
        overflow = 0 if result == c_int64(signed_sum).value else 1
        return (result, carry_out, overflow)
    
    def _LoadWritePC(self, address):
        self._BXWritePC(address)
        
    def _ALUWritePC(self, address):
        thumb = self.cpsr.value & self.PROCESSOR_THUMB
        if not thumb:
            self._BXWritePC(address)
        else:
            #FIXME: BranchWritePC
            raise NotImplementedOpCode()
        
    def _BXWritePC(self, address):
        if address.value & 1:
            raise NotImplementedInstructionSet()
        elif address.value & 2 == 0:
            self.set_ip(address)
        else:
            raise Unpredictable()
    
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
    
    SCTLR_M     = 0x1 << 0
    SCTLR_V     = 0x1 << 13
    SCTLR_VE    = 0x1 << 24
    SCTLR_EE    = 0x1 << 25
    SCTLR_TE    = 0x1 << 30
    def _SCTLR(self):
        return self._CP15_read(1, 0, 0, 0)
    
    def _VBAR(self):
        return self._CP15_read(12, 0, 0, 0)
    
    def _MVBAR(self):
        return self._CP15_read(12, 0, 0, 1)
    
    TTBCR_N = 0x7
    def _TTBCR(self):
        return self._CP15_read(2, 0, 0, 2)
    
    def _TTBCR0(self):
        return self._CP15_read(2, 0, 0, 0)
    
    def _TTBCR1(self):
        return self._CP15_read(2, 0, 0, 1)
    
    
    def _DFAR(self):
        return self._CP15_read(6, 0, 0, 0)
    
    def _DFSR(self):
        return self._CP15_read(5, 0, 0, 0)
    
    def _IFAR(self):
        return self._CP15_read(6, 0, 0, 2)
    
    def _IFSR(self):
        return self._CP15_read(5, 0, 0, 1)
    
    DACR_NACCESS    = 0x0
    DACR_CLIENT     = 0x1
    DACR_MANAGER    = 0x2
    DACR_RESERVED   = 0x3
    def _DACR_domain_type(self, domain_number):
        mask = 0x3 << 2 * domain_number
        domains = self._CP15_read(3, 0, 0, 0).value
        domain = domains & mask
        domain = domain >> (2 * domain_number)
        return domain
    
    
    
    def _CP15_read(self, crn, opc1, crm, opc2):
        privileged = self._IsPrivilegedMode()
        secure = ((self.cp15_registers[1][0][1][0][0].value & self.SCR_NS) == 0)
        
        if crn == 0:
            if opc1 == 0 and crm == 0 and opc2 == 0:
                # MIDR
                if not privileged:
                        raise AccessViolation()
                
                return self.cp15_registers[0][0][0][0][0]
        elif crn == 1:
            if opc1 == 0 and crm == 0 and opc2 == 0:
                # SCTRL
                if not privileged:
                    raise AccessViolation()
                
                bank = 0 if secure else 1
                return self.cp15_registers[1][0][0][0][bank]
            elif opc1 == 0 and crm == 1 and opc2 == 0:
                # SCR
                if not (privileged and secure):
                    raise AccessViolation()
                
                return self.cp15_registers[1][0][1][0][0]
        elif crn == 2:
            if opc1 == 0 and crm == 0 and opc2 == 0:
                # TTBR0
                bank = 0 if secure else 1
                return self.cp15_registers[1][0][0][0][bank]
            elif opc1 == 0 and crm == 0 and opc2 == 1:
                # TTBR0
                bank = 0 if secure else 1
                return self.cp15_registers[1][0][0][0][bank]
            elif opc1 == 0 and crm == 0 and opc2 == 2:
                # TTBCR
                if not privileged:
                    raise AccessViolation()
                
                bank = 0 if secure else 1
                return self.cp15_registers[1][0][0][0][bank]
        elif crn == 3:
            if opc1 == 0 and crm == 0 and opc2 == 0:
                # DACR
                if not privileged:
                    raise AccessViolation()
                
                bank = 0 if secure else 1
                return self.cp15_registers[3][0][0][0][bank]
        elif crn == 5:
            if opc1 == 0 and crm == 0 and opc2 == 0:
                # DFSR
                if not privileged:
                    raise AccessViolation()
                
                bank = 0 if secure else 1
                return self.cp15_registers[5][0][0][0][bank]
            elif opc1 == 0 and crm == 0 and opc2 == 1:
                # IFSR
                if not privileged:
                    raise AccessViolation()
                
                bank = 0 if secure else 1
                return self.cp15_registers[5][0][0][1][bank]
        elif crn == 6:
            if opc1 == 0 and crm == 0 and opc2 == 0:
                # DFAR
                if not privileged:
                    raise AccessViolation()
                
                bank = 0 if secure else 1
                return self.cp15_registers[6][0][0][0][bank]
            elif opc1 == 0 and crm == 0 and opc2 == 2:
                # IFAR
                if not privileged:
                    raise AccessViolation()
                
                bank = 0 if secure else 1
                return self.cp15_registers[6][0][0][2][bank]
        elif crn == 7:
            #TODO: Not sure yet
            raise AccessViolation()
        elif crn == 8:
            # read-only
            raise AccessViolation()
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
        
        raise NoRegisterFound()
    
    def _CP15_write(self, crn, opc1, crm, opc2, value):
        privileged = self._IsPrivilegedMode()
        secure = self._IsSecure()
        
        if crn == 0:
            if opc1 == 0 and crm == 0 and opc2 == 0:
                # MIDR ( read-only )
                raise AccessViolation()
        elif crn == 1:
            if opc1 == 0 and crm == 0 and opc2 == 0:
                # SCTRL
                if not privileged:
                    raise AccessViolation()
                
                bank = 0 if secure else 1
                self.cp15_registers[1][0][0][0][bank].value = value
                return
            if opc1 == 0 and crm == 1 and opc2 == 0:
                # SCR
                if not (privileged and secure):
                    raise AccessViolation()
                
                self.cp15_registers[1][0][1][0][0].value = value
                return
        elif crn == 2:
            if opc1 == 0 and crm == 0 and opc2 == 0:
                # TTBR0
                bank = 0 if secure else 1
                self.cp15_registers[1][0][0][0][bank].value = value
                return
            elif opc1 == 0 and crm == 0 and opc2 == 1:
                # TTBR0
                bank = 0 if secure else 1
                self.cp15_registers[1][0][0][0][bank].value = value
                return
            elif opc1 == 0 and crm == 0 and opc2 == 2:
                # TTBCR
                if not privileged:
                    raise AccessViolation()

                bank = 0 if secure else 1
                self.cp15_registers[1][0][0][0][bank].value = value
                return
        elif crn == 3:
            if opc1 == 0 and crm == 0 and opc2 == 0:
                # DACR
                if not privileged:
                    raise AccessViolation()

                bank = 0 if secure else 1
                self.cp15_registers[3][0][0][0][bank].value = value
                return
        elif crn == 5:
            if opc1 == 0 and crm == 0 and opc2 == 0:
                # DFSR
                if not privileged:
                    raise AccessViolation()
                
                bank = 0 if secure else 1
                self.cp15_registers[5][0][0][0][bank].value = value
                return
            elif opc1 == 0 and crm == 0 and opc2 == 1:
                # IFSR
                if not privileged:
                    raise AccessViolation()
                
                bank = 0 if secure else 1
                self.cp15_registers[5][0][0][1][bank].value = value
                return
        elif crn == 6:
            if opc1 == 0 and crm == 0 and opc2 == 0:
                # DFAR
                if not privileged:
                    raise AccessViolation()
                
                bank = 0 if secure else 1
                self.cp15_registers[6][0][0][0][bank].value = value
                return
            elif opc1 == 0 and crm == 0 and opc2 == 2:
                # IFAR
                if not privileged:
                    raise AccessViolation()
                
                bank = 0 if secure else 1
                self.cp15_registers[6][0][0][2][bank].value = value
                return
        elif crn == 7:
            #TODO: Not sure about this yet.
            if not privileged:
                    raise AccessViolation()
            #TODO: Implement real cache simulation
            if opc1 == 0 and crm == 5 and opc2 == 0:
                return
        elif crn == 8:
            #TODO: Implement TLB Simulation
            if not privileged:
                raise AccessViolation()
            if opc1 == 0 and crm == 7 and opc2 == 0:
                # TLBIALL
                return
        elif crn == 12:
            # Security Extension registers.
            if opc1 == 0 and crm == 0 and opc2 == 0:
                # VBAR ( Banked , read/write priviledged)
                if not privileged:
                    raise AccessViolation()
                
                bank = 0 if secure else 1
                self.cp15_registers[12][0][0][0][bank].value = value & (~0x1F)
                return
            elif opc1 == 0 and crm == 0 and opc2 == 1:
                # MVBAR ( Banked , read/write )
                if not privileged:
                    raise AccessViolation()
                
                bank = 0 if secure else 1
                self.cp15_registers[12][0][0][1][bank].value = value & (~0x1F)
                return
            elif opc1 == 0 and crm == 1 and opc2 == 0:
                # ISR ( read-only )
                raise AccessViolation()

        raise NoRegisterFound()
    
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
    
    _stopped = False
    def run(self):
        while True:
            if self._stopped:
                sys.exit(0)

            self.execute()
    
    def stop(self):
        self._stopped = True
    
    def get_info(self):
        return '''Instruction pointer    : %s
Opcode    : %s''' % (hex(self.ip.value), hex(self.op))