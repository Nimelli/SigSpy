import dearpygui.dearpygui as dpg
from app import MYAPP
from serialManager import SerialProc
from settings import MAX_LINE

import logging
logging.basicConfig(level=logging.DEBUG)
    

# UI
dpg.create_context()
myApp = MYAPP(dpg)
dpg.set_exit_callback(myApp.on_close)

with dpg.window(label="Serial Port", tag="Primary Window"):
    with dpg.child_window(autosize_x=True, height=100):
        with dpg.group(horizontal=True):
            all_ports = SerialProc.list_port()
            logging.debug(all_ports)
            dpg.add_combo(all_ports, label="COM Port", tag="com_port_txt")
            dpg.add_button(label="Open Port", callback=myApp.on_btn_open_port, tag="open_port")
            dpg.add_button(label="Close Port", callback=myApp.on_btn_close_port, tag="close_port")

        with dpg.group(horizontal=True):
            dpg.add_input_text(tag="send_cmd_txt")
            dpg.add_button(label="Send cmd", callback=myApp.on_btn_send_cmd, tag="send_cmd")
    # create plot

with dpg.window(label="Plot", tag="plotwin", pos=(200, 200)):
    # create plot
    with dpg.plot(label="Line Series", height=400, width=800):
        # optionally create legend
        dpg.add_plot_legend()

        # REQUIRED: create x and y axes
        dpg.add_plot_axis(dpg.mvXAxis, label="x", tag="x_axis")
        dpg.add_plot_axis(dpg.mvYAxis, label="y", tag="y_axis")

        dpg.set_axis_limits_auto("x_axis")
        dpg.set_axis_limits_auto("y_axis")

        # series belong to a y axis
        for i in range(MAX_LINE):
            dpg.add_line_series([], [], parent="y_axis", tag="serial_plot_series_{}".format(i))

    dpg.add_button(label="Clear", callback=myApp.on_btn_clear_plot, tag="clear_plot")

with dpg.window(label="Log", tag="log", pos=(0, 200), height=200, width=200):
    dpg.add_text("(reverse) last received at the top", wrap=0)
    dpg.add_button(label="Clear", callback=myApp.on_btn_clear_log, tag="clear_log")
    with dpg.child_window():
        dpg.add_text(wrap=0, tag="serial_log")


# debug usefull
#dpg.show_documentation()
#dpg.show_style_editor()
#dpg.show_debug()
#dpg.show_about()
dpg.show_metrics()
#dpg.show_font_manager()
#dpg.show_item_registry()

dpg.create_viewport(title='SigSpy', width=1200, height=800)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("Primary Window", True)

# below replaces, start_dearpygui()

# start_time = time.time()
# fpsCounter = 0
while dpg.is_dearpygui_running():
    

    # Use dpg.show_metrics() instead
    # fpsCounter += 1
    # if (time.time() - start_time) > 1 : # print every second
    #     print("FPS: ", fpsCounter / (time.time() - start_time))
    #     fpsCounter = 0
    #     start_time = time.time()

    myApp.mainloop()

    dpg.render_dearpygui_frame()

dpg.destroy_context()