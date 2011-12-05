import os
from ctypes import c_uint32

class BinaryFileReader(object):
    def __init__(self, filepath):
        self.filepath = filepath
        self.file = open(filepath, 'rb')
    
    def readin(self, write_fn, size, memory_offset = 0, file_offset=0):
        self.file.seek(file_offset)
        data = self.file.read()
        for index in range(0, size, 4):
            i1 = (ord(data[index]) & 0xFF)
            i2 = (ord(data[index + 1]) & 0xFF) << 8
            i3 = (ord(data[index + 2]) & 0xFF) << 16
            i4 = (ord(data[index + 3]) & 0xFF) << 24
            i = c_uint32(i1 | i2 | i3 | i4)
            
            write_fn(memory_offset + index, i)

    def close(self):
        self.file.close()
        
    def getsize(self):
        return os.path.getsize(self.filepath)