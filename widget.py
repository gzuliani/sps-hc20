#!/usr/bin/python
# -*- coding: utf8 -*-

try:
    # python 3.x
    import tkinter as tk
    from tkinter import simpledialog as tkSimpleDialog
except:
    # python 2.x
    import Tkinter as tk
    import tkSimpleDialog

from palette import Palette


def center_window(window):
    window.update_idletasks()
    w = window.winfo_screenwidth()
    h = window.winfo_screenheight()
    size = tuple(int(_) for _ in window.geometry().split('+')[0].split('x'))
    x = w/2 - size[0]/2
    y = h/2 - size[1]/2
    window.geometry("%dx%d+%d+%d" % (size + (x, y)))

class StyledWidget(object):

    _FOREGROUND_COLOR = Palette.BASE02
    _BACKGROUND_COLOR = Palette.BASE2

    def __init__(self, root):
        self._root = root
        self._create_widgets()
        self._create_bindings()
        self._define_layout()
        self._apply_style()

    def _create_widgets(self):
        pass

    def _create_bindings(self):
        pass

    def _define_layout(self):
        pass

    def _apply_style(self):
        self._root['background'] = self._BACKGROUND_COLOR

    def _enable(self, widget):
        self._set_widget_state(widget, tk.NORMAL)

    def _disable(self, widget):
        self._set_widget_state(widget, tk.DISABLED)

    def _is_enabled(self, widget):
        return str(widget['state']) == tk.NORMAL

    def _is_disabled(self, widget):
        return str(widget['state']) == tk.DISABLED

    def _set_widget_state(self, widget, state):
        widget['state'] = state


class StyledFrame(StyledWidget):

    def __init__(self, root):
        self._root = root
        self._frame = tk.Frame(self._root)
        StyledWidget.__init__(self, root)

    def _apply_style(self):
        StyledWidget._apply_style(self)
        self._frame['background'] = self._BACKGROUND_COLOR
        for widget in self._frame.winfo_children():
            if widget.winfo_class() == 'TLabel':
                widget['background'] = self._BACKGROUND_COLOR

    def grid(self, *args, **kwargs):
        self._frame.grid(*args, **kwargs)

    def grid_forget(self):
        self._frame.grid_forget()


class BaseDialog(tkSimpleDialog.Dialog):

    def __init__(self, master, title):
        tkSimpleDialog.Dialog.__init__(self, master, title)

    def buttonbox(self):
        # no default button box
        pass

    def wait_window(self, window=None):
        center_window(self)
        self.focus_force()
        return tkSimpleDialog.Dialog.wait_window(self, window)
