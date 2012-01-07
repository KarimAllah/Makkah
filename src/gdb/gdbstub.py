# Written basically based on gdbstub.c from QEMU
import re
import sys
import time
import logging
import threading
import global_env
from ctypes import c_uint8
import socket

PIBuffer_Size = 4 * 1024

logger = logging.getLogger("GDBStubServer")

GDBStates = {
                'RS_INACTIVE'   : 0x0,
                'RS_IDLE'       : 0x1,
                'RS_GETLINE'    : 0x2,
                'RS_CHKSUM1'    : 0x3,
                'RS_CHKSUM2'    : 0x4,
                'RS_SYSCALL'    : 0x5
             }

class GDBStubServer(threading.Thread):
    def __init__(self, char_driver):
        threading.Thread.__init__(self)
        self.char_driver = char_driver
        self.PIBuffer = (c_uint8 * PIBuffer_Size)()
        self.PIBuffer_index = 0
        self.state = GDBStates['RS_IDLE']
        self.line_csum = c_uint8()
        self._stopped = False
    
    def run(self):
        while True:
            try:
                if self._stopped:
                    logger.critical("System was stopped")
                    break
    
                input = self.char_driver.read_byte()
                if not input:
                    logger.critical("Client closed connection.")
                    break
                logger.critical("Received char (%s) => (%s)", ord(input), input)
                self.process_byte(input)
            except socket.timeout:
                # check events now
                if global_env.dbg_breakpoint_hit:
                    global_env.dbg_breakpoint_hit = False
                    self._send_anonymous_stop_signal()
            except:
                break
        
        logger.critical("Makkah: Terminated via GDBstub")
        global_env.stop_all()
        global_env.dbg_event.set()
    
    def _send_anonymous_stop_signal(self):
        str = "S05"
        self._put_packet(self._str_to_buf(str), len(str))
    
    ORD_Dollar = ord('$')
    ORD_HASH = ord('#')
    ORD_MINUS = ord('-')
    ORD_PLUS = ord('+')
    def _fromhex(self, v):
        # v is a string
        return int(v, 16)

    def _tohex(self, v, padding=0, fill_char='0'):
        # v is an int
        value = hex(v)
        output = value[2:-1] if value[-1] == 'L' else value[2:]

        if padding:
            output = output.rjust(padding, fill_char)
            
        out = ''
        for index in range(len(output) / 2):
            out += output[-(index * 2 + 2)] + output[-(index * 2 + 1)]
            
        return out or output
        

    def process_byte(self, char):
        ch = ord(char)

        if self.last_packet_length:
            if char == '-':
                logger.critical("Got NACK, retransmitting\n")
                self._put_packet(self.last_packet, self.last_packet_length)  
            elif char == '+':
                logger.critical("Got ACK\n")
            else:
                logger.critical("Got '%s' when expecting ACK/NACK\n", ch);
            
            if char == '+' or char == '$':
                self.last_packet_length = 0
            
            if char != '$':
                return

        if global_env.dbg_event.isSet():
            #FIXME: We need to make sure that everything has actually stop before going any further 
            global_env.dbg_event.clear()
        else:
            if self.state == GDBStates['RS_IDLE']:
                if char == '$':
                    self.PIBuffer_index = 0
                    self.state = GDBStates['RS_GETLINE']
            elif self.state == GDBStates['RS_GETLINE']:
                if char == '#':
                    self.state = GDBStates['RS_CHKSUM1']
                elif (self.PIBuffer_index >= PIBuffer_Size - 1):
                    self.state = GDBStates['RS_IDLE']
                else:
                    self.PIBuffer[self.PIBuffer_index] = ch
                    self.PIBuffer_index += 1
            elif self.state == GDBStates['RS_CHKSUM1']:
                self.PIBuffer[self.PIBuffer_index] = 0
                self.line_csum.value = self._fromhex(char) << 4
                self.state = GDBStates['RS_CHKSUM2']
            elif self.state == GDBStates['RS_CHKSUM2']:
                self.line_csum.value |= self._fromhex(char);
                csum = 0;
                for index in range(self.PIBuffer_index):
                    csum += self.PIBuffer[index]

                if self.line_csum.value != csum & 0xFF:
                    self.char_driver.write_byte(self.ORD_MINUS)
                    self.state = GDBStates['RS_IDLE']
                else:
                    self.char_driver.write_byte(self.ORD_PLUS)
                    self.state = self.gdb_handle_packet()
            elif ch == 3:
                self._send_anonymous_stop_signal()
            else:
                self._abort()
    
    def _abort(self):
        logger.warn("GDB Connection was aborted.")

    ORD_0 = ord('0')
    ORD_X = ord('x')
    ORD_x = ord('X')
    ORD_A = ord('A')
    ORD_a = ord('a')
    ORD_F = ord('F')
    ORD_f = ord('f')
    def _strtoul(self, _buffer, i=0, hex=False):
        result = '';sign = +1
        if _buffer[i] == self.ORD_MINUS:
            sign = -1
            i += 1

        while True:
            value = chr(_buffer[i])
            if not ((hex and ((self.ORD_A <= _buffer[i] <= self.ORD_F) or (self.ORD_a <= _buffer[i] <= self.ORD_f))) or value.isdigit()):
                break

            result += value
            i += 1

        
        return (sign * int(result or '0', 16 if hex else 10)), i

    ENOSYS = 1
    def gdb_handle_packet(self):
        def unknown_command():
            _buffer = (c_uint8 * 2)()
            _buffer[0] = ord('\x00')
            _buffer[1] = ord('\x00')
            self._put_packet(_buffer, 1)

        index = 0
        ch = chr(self.PIBuffer[index])
        index = 1
        if ch == 'z' or ch == 'Z':
            type, index = self._strtoul(self.PIBuffer, index, True)
            if self.PIBuffer[index] == ord(','):
                index += 1
            addr, index = self._strtoul(self.PIBuffer, index, True)
            if self.PIBuffer[index] == ord(','):
                index += 1
            length, index = self._strtoul(self.PIBuffer, index, True)

            if ch == 'Z':
                res = self._gdb_breakpoint_insert(addr, length, type);
            else:
                res = self._gdb_breakpoint_remove(addr, length, type);
            if res >= 0:
                str = "OK"
                self._put_packet(self._str_to_buf(str), len(str))
            elif res == -self.ENOSYS:
                str = ""
                self._put_packet(self._str_to_buf(str), len(str))
            else:
                str = "E22"
                self._put_packet(self._str_to_buf(str), len(str))
        elif ch == '?':
            # Initializing.
            str = "T05thread:01;"
            global_env.GDB_IPs = []
            global_env.GDB_ops = []
            self._put_packet(self._str_to_buf(str), len(str))
        elif ch == 'H':
            type = self.PIBuffer[index]
            index += 1
            thread, index = self._strtoul(self.PIBuffer, index, True)
            if thread == -1 or thread == 0:
                str = "OK"
                self._put_packet(self._str_to_buf(str), len(str));
            else:
                raise NotImplemented()
        elif ch == 'q':
            next_char = chr(self.PIBuffer[index])
            if next_char == 'C':
                # Current thread.
                str = 'QC1'
                self._put_packet(self._str_to_buf(str), len(str))
            else:
                unknown_command()
        elif ch == 'g':
            #FIXME
            str = ''
            for i in range(16):
                value = self._tohex(global_env.main_cpu.register_read(i).value, 8, '0')
                logger.critical(value)
                str += value
                logger.critical("Reading register (%s) => (%s)", i, value)
            self._put_packet(self._str_to_buf(str), len(str))
        elif ch == 'p':
            #FIXME
            register_no, index = self._strtoul(self.PIBuffer, index, True)
            if register_no < 16:
                str = self._tohex(global_env.main_cpu.register_read(register_no).value, 8, '0')
                logger.critical("Reading register (%s) => (%s)", register_no, str)
                self._put_packet(self._str_to_buf(str), len(str))
            else:
                str = '00000000'
                self._put_packet(self._str_to_buf(str), len(str))
        elif ch == 'm':
            addr, index = self._strtoul(self.PIBuffer, index, True)
            if self.PIBuffer[index] == ord(','):
                index += 1
            length, _ = self._strtoul(self.PIBuffer, index, True)
            arr_length = length * 2
            _buffer = (c_uint8 * arr_length)()
            
            # Change your identity to imitate the cpu that's accessing this memory region
            global_env.THREAD_ENV.engine_id = global_env.main_cpu.get_name()
            i = 0
            try:
                for _ in range(length / 4):
                    value = global_env.main_cpu.mmu_read(addr + i).value
                    hex_value = (self._tohex(value, 8, '0'))
                    for index in range(8):
                        _buffer[index] = ord(hex_value[index])
                    i += 4

                self._put_packet(_buffer, arr_length)
            except:
                str = "E14"
                self._put_packet(self._str_to_buf(str), len(str))
        elif ch == 'v':
            if chr(self.PIBuffer[index]) == 'C' and chr(self.PIBuffer[index + 1]) == 'o' and \
                chr(self.PIBuffer[index + 2]) == 'n' and chr(self.PIBuffer[index + 3]) == 't':
                if chr(self.PIBuffer[index + 4]) == '?':
                    str = 'vCont;c;C;s;S'
                    self._put_packet(self._str_to_buf(str), len(str))
                elif chr(self.PIBuffer[index + 4]) == ';' and chr(self.PIBuffer[index + 5]) == 'c':
                    global_env.STEPPING = False
                    global_env.dbg_event.set()
                elif chr(self.PIBuffer[index + 4]) == ';' and chr(self.PIBuffer[index + 5]) == 's':
                    global_env.STEPPING = True
                    global_env.dbg_event.set()
        elif ch == 'k':
            logger.critical("Makkah: Terminated via GDBstub")
            global_env.stop_all()
            global_env.dbg_event.set()
        else:
            unknown_command()

        return GDBStates['RS_IDLE']

    def _str_to_buf(self, str):
        _buffer = (c_uint8 * len(str))()
        for index in range(len(str)):
            _buffer[index] = ord(str[index])
            
        return _buffer

    last_packet = (c_uint8 * PIBuffer_Size)()
    last_packet_length = 0
    def _put_packet(self, _buffer, length, index=0):
        if _buffer != self.last_packet:
            csum = 0
            self.last_packet[0] = self.ORD_Dollar
            i = 1
            for _ in range(length):
                self.last_packet[i] = _buffer[index + i - 1]
                csum += _buffer[index + i - 1]
                i += 1
    
            self.last_packet[i] = self.ORD_HASH
            self.last_packet[i + 1] = ord(self._tohex((csum >> 4) & 0xf)[0])
            self.last_packet[i + 2] = ord(self._tohex(csum & 0xf)[0])
            self.last_packet_length = i + 3

        for index in range(self.last_packet_length):
            logger.critical("Sending char (%s) => (%s)", self.last_packet[index], chr(self.last_packet[index]))

        self.char_driver.write(self.last_packet, self.last_packet_length)
    
    def _gdb_breakpoint_insert(self, addr, len, type):
        try:
            if type == 0 or type == 1:
                global_env.GDB_IPs.append(addr)
            else:
                raise NotImplemented()
            
            return 0
        except:
            return -self.ENOSYS
    
    def stop(self):
        self._stopped = True

    def _gdb_breakpoint_remove(self, addr, len, type):
        try:
            if type == 0 or type == 1:
                global_env.GDB_IPs.remove(addr)
            else:
                raise NotImplemented()
            
            return 0
        except:
            return -self.ENOSYS

    break1_re = re.compile('^b \d+$')
    break1_number_re = re.compile('\d+$')
    break2_re = re.compile('^b 0x[\d|a|b|c|d|e|f|A|B|C|D|E|F]+$')
    break2_number_re = re.compile('[\d|a|b|c|d|e|f|A|B|C|D|E|F]+$') 
    def breakpoint_prompt(self):
        while True:
            if self._stopped:
                sys.exit(0)

            input = raw_input("makkah_db $ ")
            self._execute(input)
            
    _latest_command = ''
    def _execute(self, input):
        if input:
            self._latest_command = input
        else:
            input = self._latest_command

        if input == 'q':
            global_env.stop_all()
            global_env.dbg_event.set()
        elif input == 'h':
            logger.critical("In the future this will show you the help.")
        elif input == 'c' or input == 'continue':
            logger.critical("Continue")
            global_env.dbg_event.set()
        elif input == 'ci':
            logger.critical(global_env.get_info())
            logger.critical("Continue ..")
            global_env.dbg_event.set()
        elif input == 'n' or input == 'next':
            global_env.STEPPING = True
            global_env.dbg_event.set()
            logger.critical("Next ..")
        elif input == 's off':
            global_env.STEPPING = False
        elif input == 's on':
            global_env.STEPPING = True
        elif self.break1_re.match(input):
            # Breakpoint decimal
            address = self.break1_number_re.search(input).group()
            self._gdb_breakpoint_insert(int(address), 4, 0)
        elif self.break2_re.match(input):
            # Breakpoint hex
            address = self.break2_number_re.search(input).group()
            self._gdb_breakpoint_remove(int(address, 16), 4, 0)
        elif input == 'info' or input == 'i':
            print global_env.get_info()
        else:
            logger.critical("Wrong command.")
    