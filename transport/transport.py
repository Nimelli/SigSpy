from settings import MAX_LINE, T_NAME_SERIAL, T_NAME_TCP

from .serialManager import SerialProc
from .tcpManager import TcpProc

import logging
from queue import Queue


def check_int(s):
    if len(s) <= 0:
        logging.error(s)
        return False
    
    if s[0] in ('-', '+'):
        return s[1:].isdigit()
    return s.isdigit()

class Transport():
    def __init__(self) -> None:
        self.data_in_queue = Queue() # host in
        self.data_out_queue = Queue() # host out

        self.t_selection = ""
        self.is_open = False
        self.serProc = SerialProc(self.data_in_queue, self.data_out_queue)
        self.tcpProc = TcpProc(self.data_in_queue, self.data_out_queue)

    def print_debug_info(self):
        logging.debug("IN queue approximate size: {}, OUT queue approximate size: {}".format(self.data_in_queue.qsize(), self.data_out_queue.qsize()))

    def select(self, name):
        logging.debug("transport select")
        if(self.is_open):
            # can't change transport if is open already
            return

        self.t_selection = name
    
    def open(self, settings):
        self.close() # just in case
        logging.debug("transport open")

        if(self.t_selection == T_NAME_SERIAL):
            if(len(settings) != 1):
                logging.error("open wrong parameters: {}, len: {}".format(settings, len(settings)))
                return
            self.is_open = self.serProc.open(settings[0]) # open
        elif(self.t_selection == T_NAME_TCP):
            if(len(settings) != 2):
                logging.error("open wrong parameters: {}, len: {}".format(settings, len(settings)))
                return
            #TODO: more check on parameters
            self.is_open = self.tcpProc.open(host=str(settings[0]), port=int(settings[1])) # default localhaost

    def start(self):
        if(self.is_open):
            logging.debug("transport start")
            if(self.t_selection == T_NAME_SERIAL):
                self.serProc.start()
            elif(self.t_selection == T_NAME_TCP):
                self.tcpProc.start()

    def close(self):
        logging.debug("transport close")
        self.serProc.close()
        self.tcpProc.close()
        self.is_open = False

    def write(self, cmd_b):
        self.data_out_queue.put(cmd_b)        

    def get_data_from_input_buf(self):
        """ read data from input queue, decode and separate (coma separated) the different signals
            Assume data coming line by line and with specific format
            This function needs to change to support other data format """

        def __inner_add_byte_to_signal(b, signal_idx):
            if(signal_idx >= MAX_LINE):
                logging.error("too many signals {}".format(signal_idx))
                return

            b_strip = b.strip() # remove leading, trailing spaces if any, also removes \r\n
            b_dec = b_strip.decode("utf-8")

            if(check_int(b_dec)): # signal must be int, for this implementation
                signals_data[signal_idx].append(int(b_dec)) 
            else:
                logging.info("Not a digit: {}".format(b_strip))


        new_data_flag = False
        raw_data = []
        signals_data =[]

        for i in range(MAX_LINE):
             signals_data.append([])

        get_cnt = 0
        while not self.data_in_queue.empty():
            new_data_flag = True
            line_chunk = self.data_in_queue.get()
            get_cnt += 1
            raw_data.append(line_chunk)

            if(get_cnt > 1024): # TBC size, actually should monitor if this is continuously increasing
                logging.warning("consummer app cannot process as fast as data comes in")
                break # loosing data

            signal_idx = 0
            for b in line_chunk.split(b','):
                j = b.find(b"\n")
                if(j > 0): 
                    # if chunk greater than 1, split can produce a b like bytearray(b'sn\r\ns0')
                    # which contain last item and first item of next chunk

                    b_now = b[:j]
                    b_next = b[j+1:]

                    __inner_add_byte_to_signal(b_now, signal_idx)
                    # end of line
                    signal_idx = 0 # reset

                    if(len(b_next) > 0):
                        __inner_add_byte_to_signal(b_next, signal_idx)
                    
                else:
                    __inner_add_byte_to_signal(b, signal_idx)
                    
                
                signal_idx += 1

            self.data_in_queue.task_done() # TODO: is it needed or not ?
        
        return (new_data_flag, raw_data, signals_data)