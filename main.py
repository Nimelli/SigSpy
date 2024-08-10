import dearpygui.dearpygui as dpg

from app import MYAPP
from transport.serialManager import SerialProc # for com port list
from settings import MAX_LINE

import logging
logging.basicConfig(level=logging.DEBUG)
    

# UI
dpg.create_context()
myApp = MYAPP(dpg)
dpg.set_exit_callback(myApp.on_close)

def show_plot_cursor():
    dpg.configure_item("vc1", show=True)
    dpg.configure_item("hc1", show=True)
    dpg.configure_item("vc2", show=True)
    dpg.configure_item("hc2", show=True)

def hide_plot_cursor():
    dpg.configure_item("vc1", show=False)
    dpg.configure_item("hc1", show=False)
    dpg.configure_item("vc2", show=False)
    dpg.configure_item("hc2", show=False)

def print_cursor_dx():
    dpg.set_value("delta_x", "dX: {:.2f}".format(dpg.get_value("vc2") - dpg.get_value("vc1")))

def print_cursor_dy():
    dpg.set_value("delta_y", "dY: {:.2f}".format(dpg.get_value("hc2") - dpg.get_value("hc1")))

with dpg.window(label="Serial Port", tag="Primary Window"):
    with dpg.child_window(autosize_x=True, height=100):
        with dpg.group(horizontal=True):
            all_ports = SerialProc.list_port()
            logging.debug(all_ports)
            dpg.add_combo(all_ports, label="COM Port", tag="com_port_txt")
            dpg.add_button(label="Open Port", callback=myApp.on_btn_open_port)
            dpg.add_button(label="Close Port", callback=myApp.on_btn_close)

        with dpg.group(horizontal=True):
            dpg.add_input_text(tag="send_cmd_txt")
            dpg.add_button(label="Send cmd", callback=myApp.on_btn_send_cmd)


    with dpg.child_window(autosize_x=True, height=100):
        with dpg.group(horizontal=True):
            dpg.add_button(label="Open TCP", callback=myApp.on_btn_open_tcp)
            dpg.add_button(label="Close TCP", callback=myApp.on_btn_close)

with dpg.window(label="Plot", tag="plotwin", pos=(200, 200)):
    # create plot
    with dpg.plot(label="Line Series", height=400, width=800):
        # optionally create legend
        dpg.add_plot_legend()

        # REQUIRED: create x and y axes
        dpg.add_plot_axis(dpg.mvXAxis, label="x", tag="x_axis")
        dpg.add_plot_axis(dpg.mvYAxis, label="y", tag="y_axis")

        dpg.add_drag_line(tag="vc1", label="vc1", color=[255, 0, 0, 255], show=False, callback=print_cursor_dx)
        dpg.add_drag_line(tag="vc2", label="vc2", color=[255, 0, 0, 255], show=False, callback=print_cursor_dx)
        dpg.add_drag_line(tag="hc1", label="hc1", color=[255, 255, 0, 255], vertical=False, callback=print_cursor_dy)
        dpg.add_drag_line(tag="hc2", label="hc2", color=[255, 255, 0, 255], vertical=False, callback=print_cursor_dy)

        dpg.set_axis_limits_auto("x_axis")
        dpg.set_axis_limits_auto("y_axis")

        # series belong to a y axis
        for i in range(MAX_LINE):
            dpg.add_line_series([], [], parent="y_axis", tag="serial_plot_series_{}".format(i))

    with dpg.group(horizontal=True):
        dpg.add_button(label="Clear", callback=myApp.on_btn_clear_plot, tag="clear_plot")
        dpg.add_button(label="Show cursor", callback=show_plot_cursor)
        dpg.add_button(label="Hide cursor", callback=hide_plot_cursor)
        dpg.add_text(tag="delta_x", wrap=0)
        dpg.add_text(tag="delta_y", wrap=0)

    with dpg.tree_node(label="Signal stat"):
        for i in range(MAX_LINE):
            with dpg.tree_node(label="Sig {}".format(i), tag="stat_sig_{}".format(i), show=False):
                dpg.add_text(tag="stat_sig_min_{}".format(i))
                dpg.add_text(tag="stat_sig_max_{}".format(i))
                dpg.add_text(tag="stat_sig_avg_{}".format(i))
                dpg.add_text(tag="stat_sig_std_{}".format(i))


with dpg.window(label="Log", tag="log", pos=(0, 200), height=200, width=200):
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
dpg.show_item_registry()

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