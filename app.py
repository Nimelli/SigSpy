from serialManager import SerialProc
from settings import MAX_LINE
from queue import Queue
import time
import logging

def ts_ms():
    return round(time.time() * 1000)

def check_int(s):
    if len(s) <= 0:
        logging.error(s)
        return False
    
    if s[0] in ('-', '+'):
        return s[1:].isdigit()
    return s.isdigit()    

class MYAPP():
    def __init__(self, dpg) -> None:
        self.dpg = dpg

        self.data_in_queue = Queue() # host in
        self.data_out_queue = Queue() # host out
        self.serProc = SerialProc(self.data_in_queue, self.data_out_queue)
        self.serProc.start()

        self.t_start_first = 0
        self.plot_data_x = []
        self.plot_data_y = []
        for i in range(MAX_LINE):
            self.plot_data_y.append([])

        self.log_val = ""

    def on_close(self):
        logging.info("Exiting")
        self.serProc.close()

    def btn(self, sender, app_data):
        logging.debug(f"sender is: {sender}")
        logging.debug(f"app_data is: {app_data}")
    
        
    def on_btn_open_port(self, sender, app_data):
        com_port = self.dpg.get_value("com_port_txt")
        self.serProc.open(com_port.split(':')[0]) # open
        self.serProc.start()

    def on_btn_close_port(self, sender, app_data):
        self.serProc.close()

    def on_btn_send_cmd(self, sender, app_data):
        cmd = bytearray()
        cmd_txt = self.dpg.get_value("send_cmd_txt")
        cmd.extend(cmd_txt.encode("utf-8"))
        cmd.extend(b"\r\n")
        self.data_out_queue.put(cmd)

    def on_btn_clear_plot(self, sender, app_data):
        self.plot_data_x = []
        for i in range(MAX_LINE):
            self.dpg.set_value('serial_plot_series_{}'.format(i), [[], []])
            self.plot_data_y[i] = []

        self.dpg.fit_axis_data("x_axis")
        self.dpg.fit_axis_data("y_axis")

    def on_btn_clear_log(self, sender, app_data):
        self.log_val = ""
        self.dpg.set_value("serial_log", self.log_val)

    def get_data_from_input_buf(self):
        """ read data from input queue, decode and separate (coma separated) the different signals """
        new_data_flag = False
        raw_data = []
        signals_data =[]

        for i in range(MAX_LINE):
             signals_data.append([])

        while not self.data_in_queue.empty():
            new_data_flag = True
            line = self.data_in_queue.get()
            raw_data.append(line)

            # expected bytes are in format: b"s1, s2,.., sn \r\n"
            line_split = line.decode("utf-8").splitlines()[0].split(',') # remove \r\n, split by coma
            nb_sig = len(line_split)
            if(nb_sig == 0):
                break
            if(nb_sig > MAX_LINE):
                logging.warning("Too many signals: {}".format(nb_sig))
                break
            
            i = 0
            for sig in line_split: # iterate over the different signals
                if(i >= MAX_LINE):
                    # max signals reached
                    break

                sigv = sig.strip() # remove leading, trailing spaces if any

                if(check_int(sigv)): # signal must be int, for this implementation
                    signals_data[i].append(int(sigv)) 
                else:
                    logging.info("Not a digit: {}".format(line_split))
                    pass

                i += 1

            self.data_in_queue.task_done() # TODO: is it needed or not ?
        
        return (new_data_flag, raw_data, signals_data)

    def update_UI_input_data(self, raw_data, signals_data):
        """ update UI element with the received data """
        # append to log
        for line in raw_data:
            self.log_val = line.decode("utf-8") + self.log_val
        self.dpg.set_value("serial_log", self.log_val)

        # add new data in plot data
        i=0
        for sig in signals_data:
            self.plot_data_y[i].extend(sig)
            i += 1

        if(len(self.plot_data_x) == 0):
            self.t_start_first = ts_ms()

        ts = ts_ms() - self.t_start_first
        self.plot_data_x.append(ts)

        # update UI
        for i in range(MAX_LINE):
            if(len(self.plot_data_y[i]) > 0):
                self.dpg.set_value('serial_plot_series_{}'.format(i), [self.plot_data_x, self.plot_data_y[i]])

        self.dpg.fit_axis_data("x_axis")
        self.dpg.fit_axis_data("y_axis")

    
    def mainloop(self):
        """ dpk runs at 60FPS, this loop is called as fast """
        (new_data_flag, raw_data, signals_data) = self.get_data_from_input_buf()  
        if(new_data_flag):
            self.update_UI_input_data(raw_data, signals_data)