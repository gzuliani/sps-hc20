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

import Queue
import re
import sys
import threading
import time

from common import InputTimeDialog
from palette import Palette
from widget import StyledFrame


# time-related labels
TIME_START_BUTTON_LABEL = "Avvia"
TIME_STOP_BUTTON_LABEL = "Pausa"
TIME_SET_BUTTON_LABEL = "Cambia"
TIME_RESET_BUTTON_LABEL = "Azzera"
SET_TIME_VALUE = "Impostazione Tempo"
INPUT_TIME_VALUE = "Immettere il nuovo orario (MM:SS):"
INVALID_TIME_VALUE = \
    "L'orario \"{}\" non è valido.\n\n" \
    "Minuti e secondi vanno specificati usando due cifre, " \
    "il numero di secondi dev'essere inferiore a 60 e i due " \
    "devono essere separati da un carattere qualunque."

class ThreadedClock(object):

    STOP = 1
    CONTINUE = 2

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
                        if self._observer.tick() == self.STOP:
                            self._should_stop = True
                            self._thread = None
                point_in_time = new_point_in_time


class Stopwatch(object):

    def __init__(self):
        self._resolution = -2 # set resolution to 1/100s
        self._clock = ThreadedClock(self._resolution)
        self._ticks_to_seconds = float(10 ** (-self._resolution))
        self._clock.register(self)
        self._is_running = False
        self._triggers = []
        self._observers = []
        self._set(0)

    def register_trigger(self, trigger):
        self._triggers.append(trigger)

    def register_observer(self, observer):
        self._observers.append(observer)

    def now(self):
        return self._time

    def is_running(self):
        return self._is_running

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
        self._set((minute * 60 + second) * self._ticks_to_seconds)
        for observer in self._observers:
            observer.time_changed(*self._time)

    def reset(self):
        self.set(0, 0)

    def tick(self):
        _time = self._ticks_to_time()
        if _time == (99, 59, 9):
            self._is_running = False
            return ThreadedClock.STOP
        self._ticks += 1
        _time = self._ticks_to_time()
        if _time != self._time:
            self._time = _time
            if any([t.should_stop(*self._time) for t in self._triggers]):
                self._is_running = False
                return ThreadedClock.STOP
        return ThreadedClock.CONTINUE

    def _set(self, ticks):
        self._ticks = ticks
        self._time = self._ticks_to_time()

    def _ticks_to_time(self):
        elapsed = self._ticks / self._ticks_to_seconds
        return (int(elapsed / 60), int(elapsed) % 60, int(10 * elapsed) % 10)


class Period(object):

    def __init__(self, stopwatch):
        self._stopwatch = stopwatch
        self._stopwatch.register_trigger(self)
        self._stopwatch.register_observer(self)
        self._duration = None
        self._expired_periods = []

    def is_last_minute(self):
        minute, _, _ = self._stopwatch.now()
        return self._elapsed_time(minute) % self._duration == self._duration - 1

    def set_duration(self, minutes, queue):
        self._duration = minutes
        self._queue = queue

    # Stopwatch's observer callback
    def time_changed(self, minute, second, tenth):
        self._expired_periods = [x for x in self._expired_periods if x < minute]

    # Stopwatch's trigger callback
    def should_stop(self, minute, second, tenth):
        if tenth == 0 and second == 0 and self._is_expired(minute):
            if self._queue:
                self._queue.put(minute)
            self._expired_periods.append(minute)
            return True
        return False

    def _is_expired(self, minute):
        return self._elapsed_time(minute) % self._duration == 0

    def _elapsed_time(self, minute):
        return minute - max(self._expired_periods or [0])


class Trigger(object):

    def __init__(self, stopwatch):
        self._stopwatch = stopwatch
        self._stopwatch.register_trigger(self)
        self._minute = None
        self._second = None
        self._queue = None

    def arm(self, minute, second, queue):
        self._minute, self._second = minute, second
        self._queue = queue

    # Stopwatch's trigger callback
    def should_stop(self, minute, second, tenth):
        if not self._queue:
            return False
        if minute == self._minute and second == self._second and tenth == 0:
            self._queue.put((minute, second))
        return False


class TimeViewConfig(object):

    def __init__(
        self,
        aggregate_time=False,
        leading_zero_in_minute=False,
        tenth_second_on_last_minute=True):
            self.aggregate_time = aggregate_time
            self.leading_zero_in_minute = leading_zero_in_minute
            self.tenth_second_on_last_minute = tenth_second_on_last_minute

    def to_aggregate_time(self, phase, minute, second, tenth):
        raise NotImplementedError

    def to_period_time(self, phase, minute, second, tenth):
        raise NotImplementedError


class TimeView(object):

    def __init__(self, config=TimeViewConfig()):
        self.configure(config)

    def configure(self, config):
        self._config = config
        if self._config.leading_zero_in_minute:
            self._layout = '{:02d}:{:02d}'
        else:
            self._layout = '{: >2d}:{:02d}'

    def figures(self, stopwatch, period):
        minute, second, tenth = self._transform(*stopwatch.now())
        if self._config.tenth_second_on_last_minute and period.is_last_minute():
            left, right = second, tenth * 10
        else:
            left, right = minute, second
        return left, right

    def figures_as_text(self, stopwatch, period):
        return self._layout.format(*self.figures(stopwatch, period))

    def render(self, minute, second):
        minute, second, _ = self._transform(minute, second, 0)
        return minute, second

    def render_as_text(self, timestamp):
        minute, second, _ = self._transform(
            timestamp.minute, timestamp.second, 0, timestamp.phase)
        return self._layout.format(minute, second)

    def revert(self, minute, second):
        if self._config.aggregate_time:
            minute, second, _ = \
                self._config.to_period_time(None, minute, second, 0)
        return minute, second

    def _transform(self, minute, second, tenth, phase=None):
        if self._config.aggregate_time:
            return self._config.to_aggregate_time(phase, minute, second, tenth)
        else:
            return minute, second, tenth


class Timer(object):

    def __init__(self, config=TimeViewConfig()):
        self._stopwatch = Stopwatch()
        self._period = Period(self._stopwatch)
        self._period_queue = Queue.Queue()
        self._trigger = Trigger(self._stopwatch)
        self._trigger_queue = Queue.Queue()
        self._time_view = TimeView(config=config)

    def configure(self, config):
        self._time_view.configure(config)

    def set_period_duration(self, minutes):
        self._period.set_duration(minutes, self._period_queue)

    def arm_trigger(self, minute, second):
        self._trigger.arm(minute, second, self._trigger_queue)

    def is_running(self):
        return self._stopwatch.is_running()

    def is_expired(self):
        try:
            self._period_queue.get_nowait()
            return True
        except Queue.Empty:
            return False

    def is_triggered(self):
        try:
            self._trigger_queue.get_nowait()
            return True
        except Queue.Empty:
            return False

    def now(self):
        return self._stopwatch.now()

    def peek(self):
        minute, second, _ = self._stopwatch.now()
        return self._time_view.render(minute, second)

    def start(self):
        return self._stopwatch.start()

    def stop(self):
        return self._stopwatch.stop()

    def start_stop(self):
        return self._stopwatch.start_stop()

    def set(self, minute, second):
        self._stopwatch.set(*self._time_view.revert(minute, second))

    def reset(self):
        self._stopwatch.reset()

    def figures(self):
        return self._time_view.figures(self._stopwatch, self._period)

    def figures_as_text(self):
        return self._time_view.figures_as_text(self._stopwatch, self._period)


class TimerWidget(StyledFrame):

    _INPUT_FORMAT = re.compile('^(\d{2}).([0-5]\d)$')
    _OUTPUT_FORMAT = '{:02}:{:02}'

    def __init__(self, root, timer, font):
        self._timer = timer
        self._timer_font = font
        self._message_font = font[:1] + (font[1]/6,) + font[2:]
        print self._message_font
        self._was_running = self._timer.is_running()
        StyledFrame.__init__(self, root)

    def now(self):
        return self._timer.now()

    def figures(self):
        return self._timer.figures()

    def change_timer(self, timer):
        self._timer = timer

    def update(self):
        text = self._timer.figures_as_text()
        if text != self._time['text']:
            self._time['text'] = text
        is_running = self._timer.is_running()
        if self._was_running != is_running:
            self._was_running = is_running
            self._update_buttons_state()

    def _create_widgets(self):
        self._time = ttk.Label(self._frame, font=self._timer_font)
        self._time['foreground'] = Palette.RED
        self._start_stop_button = ttk.Button(
            self._frame, text=TIME_START_BUTTON_LABEL)
        self._set_button = ttk.Button(
            self._frame, text=TIME_SET_BUTTON_LABEL)
        self._reset_button = ttk.Button(
            self._frame, text=TIME_RESET_BUTTON_LABEL)
        self._message = ttk.Label(self._frame, font=self._message_font)
        self._message['foreground'] = Palette.RED
        self._message.configure(anchor='center')

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
        self.start_stop()

    def start_stop(self):
        self._timer.start_stop()
        self._was_running = self._timer.is_running()
        self._update_buttons_state()

    def _on_set(self, event=None):
        self.set()

    def set(self):
        if self._timer.is_running():
            return
        minute, second = self._timer.peek()
        dialog = InputTimeDialog(
            self._root,
            SET_TIME_VALUE,
            INPUT_TIME_VALUE,
            self._OUTPUT_FORMAT.format(minute, second))
        new_time = dialog.value
        if not new_time:
            return
        result = self._INPUT_FORMAT.match(new_time)
        if not result:
            tkMessageBox.showerror(
                SET_TIME_VALUE,
                INVALID_TIME_VALUE.format(new_time))
            return
        minute = int(result.group(1))
        second = int(result.group(2))
        self._timer.set(minute, second)
        self.update()

    def _on_reset(self, event=None):
        self.reset()

    def reset(self):
        if self._timer.is_running():
            return
        self._timer.reset()
        self.update()

    def hide_buttons(self, message):
        self._message.grid(row=1, column=0, columnspan=3, stick=tk.NSEW)
        self._message['text'] = message

    def show_buttons(self):
        self._message.grid_forget()

    def _update_buttons_state(self):
        if self._timer.is_running():
            self._start_stop_button['text'] = TIME_STOP_BUTTON_LABEL
            self._disable(self._set_button)
            self._disable(self._reset_button)
        else:
            self._start_stop_button['text'] = TIME_START_BUTTON_LABEL
            self._enable(self._set_button)
            self._enable(self._reset_button)
