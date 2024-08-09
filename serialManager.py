import logging
import serial
import threading

import serial.tools.list_ports
import time
import numpy as np
from random import randint


from settings import DEV_VIRTUAL, DEV_VIRT_PORT, DEV_VIRT_NAME

class VirtualSerial():
    def __init__(self) -> None:
        logging.debug("VIRTUAL in use")
        self.in_waiting = 1

        self.s1 = 0
        self.s2 = 0
        self.s3 = 0
        self.s4 = 0
        self.s5 = 0
        self.s6 = 0

    def open(self):
        logging.debug("VIRTUAL open")
        self.t_start_ms = round(time.time()*1000)

    def close(self):
        logging.debug("VIRTUAL close")

    def flushInput(self):
        pass

    def flushOutput(self):
        pass

    def read(self, n):
        time.sleep(0.01) # get flooded otherwise
        self.s1 += 1
        if(self.s1 > 255):
            self.s1 = 0
        self.s2 = randint(-50, -40)
        self.s3 = randint(-30, -20)
        self.s4 = randint(0, 20)
        self.s5 = randint(30, 40)
        self.s6 = randint(50, 100)

        buf = bytearray()
        for i in range(n):
            s = "{}, {},{},{} , {} , {}\r\n".format(self.s1, self.s2, self.s3, self.s4, self.s5, self.s6)
            buf.extend(s.encode("utf-8"))

        self.in_waiting = 1
        return buf

    def write(self, buff):
        logging.debug("VIRTUAL: {}".format(buff))

class SerialProc():
    def __init__(self, data_in_queue, data_out_queue) -> None:
        self.ser = None
        self.readline_buf = bytearray()
        self.data_in_queue = data_in_queue
        self.data_out_queue = data_out_queue

        self.thread_stop = threading.Event()
        self.threads = []
        self.running = False
        
    @staticmethod
    def list_port():
        ports = serial.tools.list_ports.comports()
        info = []
        for port, desc, hwid in sorted(ports):
            info.append("{}: {}".format(port, desc))

        if(DEV_VIRTUAL):
            info.append(DEV_VIRT_NAME)
        return info

    def open(self, port, baudrate=115200, timeout=1):
        if(self.running):
            # TBC: or close first then open
            return

        if(DEV_VIRTUAL and port==DEV_VIRT_PORT):
            self.ser = VirtualSerial()
            return

        try:
            self.ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)
        except serial.serialutil.SerialException:
            logging.error("Can not open Com port")
    
    def start(self):
        if(self.ser and not self.running):
            self.ser.flushInput()
            self.ser.flushOutput()
            self.thread_stop.clear()
            thread_reader = threading.Thread(target=self.reader)
            thread_cmder = threading.Thread(target=self.commander)
            self.threads.append(thread_reader)
            self.threads.append(thread_cmder)
            thread_reader.start()
            thread_cmder.start()
            self.running = True

    def reader(self):
        """ to run in thread - listen serial and add to in queue """
        logging.debug("serial reader start")
        while not self.thread_stop.is_set():
            line = self.readline()
            self.data_in_queue.put(line)

    def commander(self):
        """ to run in thread - check out queue and send to serial """
        logging.debug("serial commander start")
        while not self.thread_stop.is_set():
            buff = bytearray()
            while not self.data_out_queue.empty():
                buff.extend(self.data_out_queue.get())
                self.ser.write(buff)

            time.sleep(0.05) # no need to poll too fast 


    def readline(self):
        """ optimized readline"""
        i = self.readline_buf.find(b"\n")
        if i >= 0:
            r = self.readline_buf[:i+1]
            self.readline_buf = self.readline_buf[i+1:]
            return r
        while True:
            i = max(1, min(2048, self.ser.in_waiting))
            data = self.ser.read(i)
            i = data.find(b"\n")
            if i >= 0:
                r = self.readline_buf + data[:i+1]
                self.readline_buf[0:] = data[i+1:]
                return r
            else:
                self.readline_buf.extend(data)
    
    def close(self):
        if(self.ser):
            logging.debug("Close port")
            self.thread_stop.set() # stop thread
            for t in self.threads:
                t.join()
            self.ser.close()
            self.ser = None
            self.running = False