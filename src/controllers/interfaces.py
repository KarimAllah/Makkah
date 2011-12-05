import logging
from controllers.exceptions.memory_exceptions import BankNotFoundError,\
    OutOfRangeError
import global_env

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

class AbstractBankedAddressableObject(object):
    def __init__(self, wordsize= 4, multi_targets=False):
        self.slaves = {}
        self.regions_map = {}
        self.word_size = wordsize
    
    def attach_slave(self, addressable_object, start_addr, end_addr, offset = 0, bank="default"):
        bucket = self.slaves.get(bank, None)
        if not bucket:
            self.slaves[bank] = []
            
        self.slaves[bank].append((start_addr, end_addr, offset, addressable_object))
             
    def _serve_region(self, start, end, bank="default"):
        bucket = self.regions_map.get(bank, None)
        if not bucket:
            self.regions_map[bank] = []
            
        if start > end:
            start, end = end, start

        self.regions_map[bank].append((start, end))
    
    def read(self, address, bank="default", implicit=False):
        bucket = self.regions_map.get(bank, None)
        if not bucket and not implicit:
            raise BankNotFoundError(bank)
        elif not bucket and implicit:
            bucket = self.regions_map.get("default", None)

        if bucket:
            for start, end in bucket:
                if start <= address < end:
                    return self._read(address)
            
        bucket = self.slaves.get(bank, None)
        if not bucket and not implicit:
            raise BankNotFoundError(bank)
        elif not bucket and implicit:
            bucket = self.slaves.get("default", None)
            if not bucket:
                raise BankNotFoundError
            
        for start, end, offset, slave in bucket:
            if start <= address < end:
                return slave.read(address - start + offset, bank, implicit)
        
        raise OutOfRangeError(address, bank)

    #override
    def _read(self, address, bank="default"):
        self.logger.info("Reading from address (%s) through bank (%s)", address, bank)
    
    def write(self, address, value, bank="default", implicit=False):
        bucket = self.regions_map.get(bank, None)
        if not bucket and not implicit:
            raise BankNotFoundError(bank)
        elif not bucket and implicit:
            bucket = self.regions_map.get("default", None)

        if bucket:
            for start, end in bucket:
                if start <= address < end:
                    self._write(address, value)
                    return
        
        bucket = self.slaves.get(bank, None)
        if not bucket and not implicit:
            raise BankNotFoundError(bank)
        elif not bucket and implicit:
            bucket = self.slaves.get("default", None)
            if not bucket:
                raise BankNotFoundError
                
        for start, end, offset, slave in bucket:
            if start <= address < end:
                slave.write(address - start + offset, value, bank, implicit)
                return
        
        raise OutOfRangeError(address, bank)
        
    #override
    def _write(self, address, value, bank="default" ):
        self.logger.info("Writing value (%s) to address (%s) through bank (%s)", value, address, bank)
    
        
class AbstractImplicitBankedAddressableObject(AbstractBankedAddressableObject):
    def __init__(self, wordsize= 4, multi_targets=False):
        self.slaves = {}
        self.regions_map = {}
        self.word_size = wordsize
        
    def read(self, address):
        bank = global_env.THREAD_ENV.engine_id
        return super(AbstractImplicitBankedAddressableObject, self).read(address, bank, True)
        
    def write(self, address, value):
        bank = global_env.THREAD_ENV.engine_id
        super(AbstractImplicitBankedAddressableObject, self).write(address, value, bank, True)


class AbstractBankedAddressableObjectProxy(AbstractBankedAddressableObject):
    def __init__(self, wordsize = 4, multi_targets=False):
        AbstractBankedAddressableObject.__init__(self, wordsize, multi_targets)
        self.translation_enabled = False
    
    def read(self, vaddress, bank=0):
        address = self.resolve_address(vaddress, bank)
        value = super(AbstractBankedAddressableObjectProxy, self).read(address)
        self.logger.info("Reading value (%s) from (vaddress=%s, address=%s) through bank (%s)", value, vaddress, address, bank)
        return value
    
    def write(self, vaddress, value, bank=0):
        address = self.resolve_address(vaddress, bank)
        self.logger.info("Writing value (%s) to (vaddress=%s,address=%s) through bank (%s)", value, vaddress, address, bank)
        super(AbstractBankedAddressableObjectProxy, self).write(address, value, bank)
        
    
    def raw_read(self, address, bank=0):
        value = super(AbstractBankedAddressableObjectProxy, self).read(address, bank)
        self.logger.info("Raw reading value (%s) from address (%s) through bank (%s)", value, address, bank)
        return value
    
    def raw_write(self, address, value, bank=0):
        self.logger.info("Raw writing value (%s) to address (%s) through bank (%s)", value, address, bank)
        super(AbstractBankedAddressableObjectProxy, self).write(address, value, bank)
    
    def resolve_address(self, vaddress, bank=0):
        return vaddress
    
    def enable_proxy(self):
        self.translation_enabled = True
    
    def disable_proxy(self):
        self.translation_enabled = False