import socket

class CharDevice(object):
    def __init__(self, port, address='127.0.0.1', ):
        self._socket = None
        self._address = address
        self._port = port
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind((self._address, self._port))
        self._server_socket.listen(5)
    
    def connect(self):
        self._socket, _ = self._server_socket.accept()
        self._socket.settimeout(0.1)
        
    def read_byte(self):
        return self._socket.recv(1)
    
    def write_byte(self, byte):
        return self._socket.sendall(chr(byte))
    
    def write(self, buffer, length, index = 0):
        for i in range(length):
            self._socket.sendall(chr(buffer[index + i]))
            
    def stop(self):
        self._server_socket.close()