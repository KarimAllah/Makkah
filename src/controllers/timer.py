import logging

from time import sleep
from controllers.interfaces import InterruptConsumerInterface

TIMER_LOW = 0
TIMER_HIGH = 1000000
TIMER_TICK_DURATION = 0.000001 # 1 microsecond
TIMER_IRQ = 0x1

from threading import Thread

class PeriodicWorker(Thread):
    def __init__(self, name):
        Thread.__init__(self)
        self.name = name
        
        self.stopped = True
        self.running = False
    
    def run(self):
        self.stopped = False
        self.running = True
        while True:
            if self.stopped:
                break
            
            sleep(self.parameters['sleep_duration'])
            self.logger.info("Calling periodic task for (%s)", self.name)
            self.parameters['periodic_task'](self.parameters['args'])
            
        # Used here to allow us to restart our thread.
        Thread.__init__(self)
        self.running = False
        
    def stop(self):
        self.logger.info("Stopping periodic task for (%s)", self.name)
        self.stopped = True
        while True:
            if self.running == False:
                break    
        
    def reset(self):
        self.logger.info("Resetting periodic task for (%s)", self.name)
        self.stop()
        while True:
            if self.running == False:
                self.launch()
                break    

class SimpleTimer(PeriodicWorker):
    def __init__(self, name):
        PeriodicWorker.__init__(self, name)
        self.logger = logging.getLogger(name)
        # Used to collect variables used between us and our parent (Worker)
        self.parameters = {}
        self.name = name
        self.low = TIMER_LOW
        self.high = TIMER_HIGH
    
    def get_low(self):
        return self.low
    
    def set_low(self, value):
        if value > TIMER_HIGH or value < TIMER_LOW:
            raise ValueError("LOW should be between %s and %s" % (TIMER_LOW, TIMER_HIGH))
        
        self.logger.info("Setting LOW to (%s)", value) 
        self.low = value
    
    def get_high(self):
        return self.high
    
    def set_high(self, value):
        if value > TIMER_HIGH or value < TIMER_LOW:
            raise ValueError("HIGH should be between %s and %s" % (TIMER_LOW, TIMER_HIGH))
        
        self.logger.info("Setting HIGH to (%s)", value)
        self.high = value
        
    def set_interrupt_consumer(self, interrupt_consumer, irq_number):
        if irq_number != 0:
            self.logger.warn("Only one interrupt (0x0) exists")
            return
        
        self.interrupt_consumer = interrupt_consumer
    
    def launch(self):
        sleep_duration = (self.high - self.low) * TIMER_TICK_DURATION
        
        # The run() method is implemented in the worker class.
        self.parameters['sleep_duration'] = sleep_duration
        self.parameters['periodic_task'] = self.interrupt_consumer.trigger_interrupt
        self.parameters['args'] = TIMER_IRQ
        self.start()
        
class SimpleConsumer(InterruptConsumerInterface):
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.name = name
    
    def trigger_interrupt(self, unique_id):
        self.logger.info("InterruptLine (%s) was triggered.", unique_id)