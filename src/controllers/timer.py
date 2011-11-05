import logging

from time import sleep
from controllers.interfaces import AbstractInterruptProducer,\
    AbstractInterruptConsumer

TIMER_LOW = 0
TIMER_HIGH = 10000000
TIMER_TICK_DURATION = 0.000001 # 1 microsecond
TIMER_IRQ = 0x1

from threading import Thread

class PeriodicWorker(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.stopped = True
        self.running = False
    
    def run(self):
        self.stopped = False
        self.running = True
        while True:
            if self.stopped:
                break
            
            self.logger.info("Running periodic task")
            self.parameters['periodic_task'](self.parameters['args'])
            sleep(self.parameters['sleep_duration'])
            
        # Used here to allow us to restart our thread.
        Thread.__init__(self)
        self.running = False
    
    #FIXME: Should be asynchronous.    
    def stop(self):
        self.logger.info("Stopping periodic task")
        self.stopped = True
        while True:
            if self.running == False:
                break
        
    #FIXME: Should be asynchronous.
    def reset(self):
        self.logger.info("Resetting periodic task")
        self.stop()
        while True:
            if self.running == False:
                self.start()
                break

class SimpleTimer(PeriodicWorker, AbstractInterruptProducer):
    def __init__(self, name):
        PeriodicWorker.__init__(self)
        AbstractInterruptProducer.__init__(self, name)
        
        self.logger = logging.getLogger(name)
        
        # Used to collect variables used between us and our parent (PeriodicWorker)
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
    
    def start(self):
        sleep_duration = (self.high - self.low) * TIMER_TICK_DURATION
        
        # The run() method is implemented in the worker class.
        self.parameters['sleep_duration'] = sleep_duration
        self.parameters['periodic_task'] = super(SimpleTimer, self).trigger_interrupt
        self.parameters['args'] = TIMER_IRQ
        if self.running:
            self.logger.warn("Timer is already running")
            return
        super(SimpleTimer, self).start()
        
class SimpleConsumer(AbstractInterruptConsumer):
    def __init__(self, name):
        AbstractInterruptConsumer.__init__(self, name)