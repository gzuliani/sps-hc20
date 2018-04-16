#!/usr/bin/python
# -*- coding: utf8 -*-

try:
    # python 3.x
    import tkinter as tk
    import tkinter.ttk as ttk
except:
    # python 2.x
    import Tkinter as tk
    import ttk

from widget import BaseDialog


# InputNumberDialog labels
RUBOUT_BUTTON_LABEL = "<<"
OK_BUTTON_LABEL = "OK"
CANCEL_BUTTON_LABEL = "Annulla"


class InputNumberDialog(BaseDialog):

    def __init__(self, master, title, message, default):
        self.value = ''
        self._message = message
        self._default = default
        BaseDialog.__init__(self, master, title)

    def body(self, master):
        self._value = tk.StringVar()
        self._value.trace_variable("w", self._on_write)
        tk.Label(master, text=self._message, justify=tk.LEFT).grid(
            row=0, column=0, columnspan=3, stick=tk.W, padx=5, pady=5)
        self._entry = ttk.Entry(master, textvariable=self._value)
        if self._default is not None:
            self._entry.insert(0, str(self._default))
            self._entry.selection_range(0, tk.END)
            self._entry.focus_set()
        self._entry.grid(row=1, column=0, columnspan=3, padx=5, pady=(20, 5))
        ttk.Button(master, text='1', command=self._on_1).grid(
            row=2, column=0, stick=tk.EW, padx=5, pady=(20, 5))
        ttk.Button(master, text='2', command=self._on_2).grid(
            row=2, column=1, stick=tk.EW, padx=5, pady=(20, 5))
        ttk.Button(master, text='3', command=self._on_3).grid(
            row=2, column=2, stick=tk.EW, padx=5, pady=(20, 5))
        ttk.Button(master, text='4', command=self._on_4).grid(
            row=3, column=0, stick=tk.EW, padx=5, pady=(20, 5))
        ttk.Button(master, text='5', command=self._on_5).grid(
            row=3, column=1, stick=tk.EW, padx=5, pady=(20, 5))
        ttk.Button(master, text='6', command=self._on_6).grid(
            row=3, column=2, stick=tk.EW, padx=5, pady=(20, 5))
        ttk.Button(master, text='7', command=self._on_7).grid(
            row=4, column=0, stick=tk.EW, padx=5, pady=(20, 5))
        ttk.Button(master, text='8', command=self._on_8).grid(
            row=4, column=1, stick=tk.EW, padx=5, pady=(20, 5))
        ttk.Button(master, text='9', command=self._on_9).grid(
            row=4, column=2, stick=tk.EW, padx=5, pady=(20, 5))
        ttk.Button(master, text='0', command=self._on_0).grid(
            row=5, column=1, stick=tk.EW, padx=5, pady=(20, 5))
        ttk.Button(
            master,
            text=RUBOUT_BUTTON_LABEL,
            command=self._on_rubout).grid(
                row=5, column=2, stick=tk.EW, padx=5, pady=(20, 5))
        ttk.Separator(master, orient='horizontal').grid(
            row=6, column=0, columnspan=3, stick=tk.EW, pady=(20, 5))
        ttk.Button(master, text=OK_BUTTON_LABEL, command=self.ok).grid(
            row=7, column=1, stick=tk.W, padx=5, pady=(20, 5))
        ttk.Button(master, text=CANCEL_BUTTON_LABEL, command=self.cancel).grid(
            row=7, column=2, stick=tk.W, padx=5, pady=(20, 5))
        self.bind("<Key-0>", self._on_0)
        self.bind("<Key-1>", self._on_1)
        self.bind("<Key-2>", self._on_2)
        self.bind("<Key-3>", self._on_3)
        self.bind("<Key-4>", self._on_4)
        self.bind("<Key-5>", self._on_5)
        self.bind("<Key-6>", self._on_6)
        self.bind("<Key-7>", self._on_7)
        self.bind("<Key-8>", self._on_8)
        self.bind("<Key-9>", self._on_9)
        self.bind("<BackSpace>", self._on_rubout)
        self.bind("<Escape>", self.cancel)
        self.bind("<Return>", self.ok)
        self.bind("<KP_Enter>", self.ok)

    def apply(self):
        self.value = self._value.get()

    def validate(self):
        value = self._value.get()
        return len(value) > 0 and value.isdigit()

    def _on_write(self, *args, **kwargs):
        pass

    def _on_0(self, event=None):
        self._on_digit('0')

    def _on_1(self, event=None):
        self._on_digit('1')

    def _on_2(self, event=None):
        self._on_digit('2')

    def _on_3(self, event=None):
        self._on_digit('3')

    def _on_4(self, event=None):
        self._on_digit('4')

    def _on_5(self, event=None):
        self._on_digit('5')

    def _on_6(self, event=None):
        self._on_digit('6')

    def _on_7(self, event=None):
        self._on_digit('7')

    def _on_8(self, event=None):
        self._on_digit('8')

    def _on_9(self, event=None):
        self._on_digit('9')

    def _on_rubout(self, event=None):
        if self.focus_get() != self._entry:
            self._entry.delete(len(self._entry.get()) - 1, tk.END)

    def _on_digit(self, digit):
        if self.focus_get() != self._entry:
            self._entry.insert(tk.END, digit)


class InputTimeDialog(InputNumberDialog):

    def __init__(self, master, title, message, default):
        self._prev_length = len(default)
        InputNumberDialog.__init__(self, master, title, message, default)

    def validate(self):
        value = self._value.get()
        return len(value) == 5

    def _on_write(self, *args, **kwargs):
        curr_length = len(self._value.get())
        if curr_length > self._prev_length and curr_length == 2:
            self._entry.insert(tk.END, ':')
        if curr_length < self._prev_length \
            and curr_length == 3 \
            and self._entry.get()[-1] == ':':
            self._entry.delete(len(self._entry.get()) - 1, tk.END)
        self._prev_length = curr_length
