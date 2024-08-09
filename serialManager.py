import logging
import serial
import threading

import serial.tools.list_ports
import time


class SerialProc():
    def __init__(self, data_in_queue, data_out_queue) -> None:
        self.ser = None
        self.readline_buf = bytearray()
        self.data_in_queue = data_in_queue
        self.data_out_queue = data_out_queue

        self.thread_stop = threading.Event()
        self.threads = []
        
    @staticmethod
    def list_port():
        ports = serial.tools.list_ports.comports()
        info = []
        for port, desc, hwid in sorted(ports):
            info.append("{}: {}".format(port, desc))
        return info

    def open(self, port, baudrate=115200, timeout=1):
        try:
            self.ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)
        except serial.serialutil.SerialException:
            logging.error("Can not open Com port")
    
    def start(self):
        if(self.ser):
            self.ser.flushInput()
            self.ser.flushOutput()
            self.thread_stop.clear()
            thread_reader = threading.Thread(target=self.reader)
            thread_cmder = threading.Thread(target=self.commander)
            self.threads.append(thread_reader)
            self.threads.append(thread_cmder)
            thread_reader.start()
            thread_cmder.start()

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