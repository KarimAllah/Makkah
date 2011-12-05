class BankNotFoundError(Exception):
    def __init__(self, bank):
        Exception.__init__(self)
        self.bank = bank
        
class OutOfRangeError(Exception):
    def __init__(self, address, bank=0):
        Exception.__init__(self)
        self.address    = address
        self.bank       = bank
        
class ReadOnlyMemory(Exception):
    def __init__(self, address):
        self.address = address