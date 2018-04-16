#!/usr/bin/python
# -*- coding: utf8 -*-

try:
    # python 3.x
    import tkinter as tk
    import tkinter.ttk as ttk
    from tkinter import messagebox as tkMessageBox
except:
    # python 2.x
    import Tkinter as tk
    import ttk
    import tkMessageBox

import re
import threading
import time

from dialog import InputTimeDialog
from palette import Palette
from widget import StyledFrame


# timer-related labels
TIMER_START_BUTTON_LABEL = "Avvia"
TIMER_STOP_BUTTON_LABEL = "Pausa"
TIMER_SET_BUTTON_LABEL = "Cambia"
TIMER_RESET_BUTTON_LABEL = "Azzera"
SET_TIMER_VALUE = "Impostazione Timer"
INPUT_TIMER_VALUE = "Immettere il nuovo orario (MM:SS):"
INVALID_TIMER_VALUE = \
    "L'orario \"{}\" non è valido.\n\n" \
    "Minuti e secondi vanno specificati usando due cifre, " \
    "il numero di secondi dev'essere inferiore a 60 e i due " \
    "devono essere separati da un carattere qualunque."


class ThreadedClock(object):

    def __init__(self, resolution):
        self._thread = None
        self._should_stop = False
        self._observer = None
        self._seconds_to_ticks = 10 ** (-resolution)
        self._pause = 1. / (self._seconds_to_ticks * 2)

    def register(self, observer):
        self._observer = observer

    def start_stop(self):
        if self._thread:
            self._should_stop = True
            self._thread.join()
            self._thread = None
        else:
            self._should_stop = False
            self._thread = threading.Thread(target=self._run)
            self._thread.start()

    def _run(self):
        point_in_time = int(time.time() * self._seconds_to_ticks)
        while not self._should_stop:
            new_point_in_time = int(time.time() * self._seconds_to_ticks)
            if new_point_in_time - point_in_time < 1:
                time.sleep(self._pause)
            else:
                if self._observer:
                    for i in range(new_point_in_time - point_in_time):
                        self._observer.tick()
                point_in_time = new_point_in_time


class Timer(object):

    def __init__(self):
        self._resolution = -2 # set resolution to 1/100s
        self._clock = ThreadedClock(self._resolution)
        self._ticks_to_seconds = float(10 ** (-self._resolution))
        self._clock.register(self)
        self._ticks = 0
        self._is_running = False

    def peek(self):
        elapsed = self._ticks / self._ticks_to_seconds
        return (int(elapsed / 60), int(elapsed) % 60, int(100 * elapsed) % 100)

    def is_running(self):
        return self._is_running

    def is_reset(self):
        return self._ticks == 0

    def start_stop(self):
        self._clock.start_stop()
        self._is_running = not self._is_running

    def start(self):
        if not self._is_running:
            self.start_stop()

    def stop(self):
        if self._is_running:
            self.start_stop()

    def set(self, minute, second):
        assert not self._is_running
        self._ticks = (minute * 60 + second) * self._ticks_to_seconds

    def reset(self):
        assert not self._is_running
        self._ticks = 0

    def tick(self):
        self._ticks += 1


class StopWatch(object):

    def __init__(self, timer, observer=None):
        self._timer = timer
        self._stop_minute = None
        self._observer = observer

    def stop_at_minute(self, minute):
        self._stop_minute = minute

    def tick(self):
        minute, _, _ = self._timer.peek()
        if self._stop_minute \
            and self._timer.is_running() \
            and minute >= self._stop_minute:
            self._timer.stop()
            if self._observer:
                self._observer.on_stop()


class TimeViewConfig(object):

    def __init__(
        self,
        period_duration=30,
        countdown=False,
        leading_zero_in_minute=False,
        hires_timer_on_last_minute=True):
            self.period_duration = period_duration
            self.countdown = countdown
            self.leading_zero_in_minute = leading_zero_in_minute
            self.hires_timer_on_last_minute = hires_timer_on_last_minute


class TimeView(object):

    def __init__(self, config=TimeViewConfig()):
        self.configure(config)

    def configure(self, config):
        self._config = config
        if self._config.leading_zero_in_minute:
            self._layout = '{:02d}:{:02d}'
        else:
            self._layout = '{: >2d}:{:02d}'

    def peek_figures(self, timer):
        minute, second, cent = timer.peek()
        is_last_minute = (minute == self._config.period_duration - 1)
        minute, second, cent = self._adjust(minute, second, cent)
        if self._config.hires_timer_on_last_minute and is_last_minute:
            left, right = second, (cent / 10) * 10
        else:
            left, right = minute, second
        return left, right

    def peek_label(self, timer):
        return self._layout.format(*self.peek_figures(timer))

    def adjust(self, minute, second):
        minute, second, _ = self._normalize(minute, second, 0)
        if self._config.countdown:
            return self._invert(minute, second, 0)[:2]
        else:
            return minute, second

    def render(self, minute, second):
        return self._layout.format(*self.adjust(minute, second))

    def _adjust(self, minute, second, cent):
        minute, second, cent = self._normalize(minute, second, cent)
        if self._config.countdown:
            return self._invert(minute, second, cent)
        else:
            return minute, second, cent

    def _normalize(self, minute, second, cent):
        if minute >= self._config.period_duration:
            return self._config.period_duration, 0, 0
        else:
            return minute, second, cent

    def _invert(self, minute, second, cent):
        cent = (100 - cent) % 100
        second = (60 - second - (1 if cent > 0 else 0)) % 60
        minute = self._config.period_duration - minute - (
            1 if second > 0 or cent > 0 else 0)
        return minute , second, cent


class TimerWidget(StyledFrame):

    _INPUT_FORMAT = re.compile('^(\d{2}).([0-5]\d)$')
    _OUTPUT_FORMAT = '{:02}:{:02}'

    def __init__(self, root, timer, time_view, font):
        self._timer = timer
        self._time_view = time_view
        self._font = font
        self._was_running = self._timer.is_running()
        StyledFrame.__init__(self, root)

    def _create_widgets(self):
        self._time = ttk.Label(
            self._frame,
            font=self._font)
        self._time['foreground'] = Palette.RED
        self._start_stop_button = ttk.Button(
            self._frame, text=TIMER_START_BUTTON_LABEL)
        self._set_button = ttk.Button(
            self._frame, text=TIMER_SET_BUTTON_LABEL)
        self._reset_button = ttk.Button(
            self._frame, text=TIMER_RESET_BUTTON_LABEL)

    def _create_bindings(self):
        self._start_stop_button['command'] = self._on_start_stop
        self._set_button['command'] = self._on_set
        self._reset_button['command'] = self._on_reset

    def _define_layout(self):
        self._time.grid(row=0, column=0, columnspan=3, pady=(0, 5))
        self._start_stop_button.grid(row=1, column=0, stick=tk.E)
        self._set_button.grid(row=1, column=1, padx=5)
        self._reset_button.grid(row=1, column=2, stick=tk.W)

    def _on_start_stop(self, event=None):
        self._timer.start_stop()
        self._was_running = self._timer.is_running()
        self._update_buttons_state()

    def _on_set(self, event=None):
        if self._timer.is_running():
            return
        minute, second, _ = self._timer.peek()
        minute, second = self._time_view.adjust(minute, second)
        dialog = InputTimeDialog(
            self._root,
            SET_TIMER_VALUE,
            INPUT_TIMER_VALUE,
            self._OUTPUT_FORMAT.format(minute, second))
        new_time = dialog.value
        if not new_time:
            return
        result = self._INPUT_FORMAT.match(new_time)
        if not result:
            tkMessageBox.showerror(
                APP_NAME,
                INVALID_TIMER_VALUE.format(new_time))
            return
        minute = int(result.group(1))
        second = int(result.group(2))
        minute, second = self._time_view.adjust(minute, second)
        self._timer.set(minute, second)
        self.refresh()

    def _on_reset(self, event=None):
        if self._timer.is_running():
            return
        self._timer.reset()
        self.refresh()

    def _update_buttons_state(self):
        if self._timer.is_running():
            self._start_stop_button['text'] = TIMER_STOP_BUTTON_LABEL
            self._disable(self._set_button)
            self._disable(self._reset_button)
        else:
            self._start_stop_button['text'] = TIMER_START_BUTTON_LABEL
            self._enable(self._set_button)
            self._enable(self._reset_button)

    def refresh(self):
        label = self._time_view.peek_label(self._timer)
        if label != self._time['text']:
            self._time['text'] = label
        is_running = self._timer.is_running()
        if self._was_running != is_running:
            self._was_running = is_running
            self._update_buttons_state()
