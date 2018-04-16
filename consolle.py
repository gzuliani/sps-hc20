#!/usr/bin/python
# -*- coding: utf8 -*-

try:
    # python 3.x
    from configparser import SafeConfigParser
    import tkinter as tk
    import tkinter.ttk as ttk
    from tkinter import messagebox as tkMessageBox
except:
    # python 2.x
    from ConfigParser import SafeConfigParser
    import Tkinter as tk
    import ttk
    import tkMessageBox

import os
import sys
import time

import chrono
from dialog import InputNumberDialog
from palette import Palette
import scoreboard
import widget


# font size
TIMER_FONT = ('', 72, 'bold')
TEAM_TITLE_FONT_SIZE = 36
TEAM_TITLE_FONT = ('', TEAM_TITLE_FONT_SIZE, 'bold')
SET_TITLE_FONT_SIZE = 24
SET_TITLE_FONT = ('', SET_TITLE_FONT_SIZE)
SET_FONT = ('', 72, 'bold')
SCORE_TITLE_FONT_SIZE = 24
SCORE_TITLE_FONT = ('', SCORE_TITLE_FONT_SIZE)
SCORE_FONT_SIZE = 72
SCORE_FONT = ('', SCORE_FONT_SIZE, 'bold')

# padding
BUTTON_PADDING = 10

# main window
APP_NAME = "SPS HC20 - CONSOLLE"
APP_VERSION = "0.1"  # see setup.py

SIREN_BUTTON_LABEL = "Sirena"
CONFIG_BUTTON_LABEL = "Configura"
QUIT_BUTTON_LABEL = "Esci"

# configuration dialog labels
CONFIG_DIALOG_TITLE = "Configurazione Consolle"
CONFIG_DIALOG_HEADING = "Definire la modalità di funzionamento preferita:"
CONFIG_DIALOG_PERIOD_DURATION_HEADING = "Durata di un tempo"
CONFIG_DIALOG_OPTIONS_HEADING = "Opzioni"
CONFIG_DIALOG_SERIAL_PORT_HEADING = "Porta seriale"
CONFIG_DIALOG_SERIAL_PORT_LABEL = "Nome del dispositivo:"
COUNTDOWN_BUTTON_LABEL = "Esegui il conto alla rovescia"
LEADING_ZERO_IN_MINUTE_BUTTON_LABEL = "Mostra lo zero iniziale nei minuti"
HIRES_TIMER_ON_LAST_MINUTE_BUTTON_LABEL = \
    "Mostra i decimi di secondo nell'ultimo minuto"
END_OF_PERIOD_BLAST_BUTTON_LABEL = "Suona la sirena di fine tempo"
PERIOD_DURATION_LABEL = "{} minuti"
CHANGE_PERIOD_DURATION_TITLE = "Durata di un tempo"
CHANGE_PERIOD_DURATION_HEADING = "Specificare la durata di un tempo, in minuti:"
CHANGE_PERIOD_DURATION_BUTTON_LABEL = "Cambia"

OK_BUTTON_LABEL = "OK"
CANCEL_BUTTON_LABEL = "Annulla"

# main window labels
HOME_TEAM_TITLE = "LOCALI"
GUEST_TEAM_TITLE = "OSPITI"
SEVENTH_FOUL_BUTTON_LABEL = "7° FALLO"
FIRST_TIMEOUT_BUTTON_LABEL = "1° TIMEOUT"
SECOND_TIMEOUT_BUTTON_LABEL = "2° TIMEOUT"
SET_TITLE = "SET"
SCORE_TITLE = "PUNTI"
INCREMENT_SET_BUTTON_LABEL = "+1"
DECREMENT_SET_BUTTON_LABEL = "-1"
INCREMENT_SCORE_BUTTON_LABEL = "+1"
DECREMENT_SCORE_BUTTON_LABEL = "-1"
RUNNING_WITHOUT_SCOREBOARD = \
    "La porta seriale cui dovrebbe essere collegato il dispositivo di " \
    "comunicazione con il tabellone non è stata specificata.\n\n" \
    "Il programma funzionerà normalmente, ma non invierà i comandi di " \
    "controllo del tabellone."
SCOREBOARD_CONNECTION_ERROR = \
    "Impossibile connettersi al tabellone attraverso la porta \"{}\" " \
    "a causa dell'errore:\n\n{}\n\n" \
    "Verificare che il dispositivo di comunicazione con il tabellone " \
    "sia connesso al computer alla presa USB corretta, " \
    "oppure indicare il nome della porta seriale associata " \
    "a quella cui è collegato in questo momento.\n\n" \
    "Se si indica la presa sbagliata il programma funzionerà normalmente, " \
    "ma non invierà i comandi di controllo del tabellone."


class AppConfig(object):

    def __init__(self):
        self.time_view_config = chrono.TimeViewConfig()
        self.end_of_period_blast = False
        self.device_name = ''

    @property
    def period_duration(self):
        return self.time_view_config.period_duration

    @period_duration.setter
    def period_duration(self, value):
        self.time_view_config.period_duration = value

    @property
    def countdown(self):
        return self.time_view_config.countdown

    @countdown.setter
    def countdown(self, value):
        self.time_view_config.countdown = value

    @property
    def leading_zero_in_minute(self):
        return self.time_view_config.leading_zero_in_minute

    @leading_zero_in_minute.setter
    def leading_zero_in_minute(self, value):
        self.time_view_config.leading_zero_in_minute = value

    @property
    def hires_timer_on_last_minute(self):
        return self.time_view_config.hires_timer_on_last_minute

    @hires_timer_on_last_minute.setter
    def hires_timer_on_last_minute(self, value):
        self.time_view_config.hires_timer_on_last_minute = value

    def load(self, path):
        try:
            config = SafeConfigParser()
            config.read(path)
            self.period_duration = config.getint('TimeView', 'period_duration')
            self.countdown = config.getboolean('TimeView', 'countdown')
            self.leading_zero_in_minute = config.getboolean(
                'TimeView', 'leading_zero_in_minute')
            self.hires_timer_on_last_minute = config.getboolean(
                'TimeView', 'hires_timer_on_last_minute')
            self.end_of_period_blast = config.getboolean(
                'Consolle', 'end_of_period_blast')
            self.device_name = config.get('Consolle', 'device_name')
        except:
            pass

    def save(self, path):
        config = SafeConfigParser()
        config.add_section('Consolle')
        config.set('Consolle', 'end_of_period_blast',
            str(self.end_of_period_blast))
        config.set('Consolle', 'device_name', self.device_name)
        config.add_section('TimeView')
        config.set('TimeView', 'period_duration', str(self.period_duration))
        config.set('TimeView', 'countdown', str(self.countdown))
        config.set('TimeView', 'leading_zero_in_minute',
            str(self.leading_zero_in_minute))
        config.set('TimeView', 'hires_timer_on_last_minute',
            str(self.hires_timer_on_last_minute))
        with open(path, 'w') as file:
            config.write(file)


class ConfigDialog(widget.BaseDialog):

    def __init__(self, master, config):
        self._config = config
        self._period_duration = self._config.period_duration
        self._countdown = tk.BooleanVar()
        self._countdown.set(self._config.countdown)
        self._leading_zero_in_minute = tk.BooleanVar()
        self._leading_zero_in_minute.set(self._config.leading_zero_in_minute)
        self._hires_timer_on_last_minute = tk.BooleanVar()
        self._hires_timer_on_last_minute.set(
            self._config.hires_timer_on_last_minute)
        self._end_of_period_blast = tk.BooleanVar()
        self._end_of_period_blast.set(self._config.end_of_period_blast)
        self._serial_port = tk.StringVar()
        self._serial_port.set(self._config.device_name)
        widget.BaseDialog.__init__(self, master, CONFIG_DIALOG_TITLE)

    def body(self, master):
        tk.Label(master, text=CONFIG_DIALOG_HEADING, justify=tk.LEFT).grid(
            row=0, column=0, columnspan=3, stick=tk.W, padx=5, pady=5)
        period_duration = tk.LabelFrame(
                master, text=CONFIG_DIALOG_PERIOD_DURATION_HEADING)
        period_duration.grid(
            row=1, column=0, columnspan=3, stick=tk.EW, padx=5, pady=(5, 0))
        self._period_duration_label = tk.Label(period_duration, text='-')
        self._period_duration_label.grid(
            row=0, column=0, stick=tk.W, padx=(5, 0), pady=5)
        ttk.Button(
            period_duration,
            command=self._on_change_period_duration,
            text=CHANGE_PERIOD_DURATION_BUTTON_LABEL).grid(
                row=0, column=1, stick=tk.E, padx=5, pady=5)
        period_duration.grid_columnconfigure(1, weight=1)
        options = tk.LabelFrame(master, text=CONFIG_DIALOG_OPTIONS_HEADING)
        options.grid(
            row=2, column=0, columnspan=3, stick=tk.EW, padx=5, pady=(5, 0))
        tk.Checkbutton(
            options,
            text=COUNTDOWN_BUTTON_LABEL,
            variable=self._countdown).grid(
                row=0, column=0, stick=tk.W, padx=5, pady=(10, 0))
        tk.Checkbutton(
            options,
            text=LEADING_ZERO_IN_MINUTE_BUTTON_LABEL,
            variable=self._leading_zero_in_minute).grid(
                row=1, column=0, stick=tk.W, padx=5, pady=(5, 0))
        tk.Checkbutton(
            options,
            text=HIRES_TIMER_ON_LAST_MINUTE_BUTTON_LABEL,
            variable=self._hires_timer_on_last_minute).grid(
                row=2, column=0, stick=tk.W, padx=5, pady=(5, 0))
        tk.Checkbutton(
            options,
            text=END_OF_PERIOD_BLAST_BUTTON_LABEL,
            variable=self._end_of_period_blast).grid(
                row=3, column=0, stick=tk.W, padx=5, pady=(5, 10))
        serial_port = tk.LabelFrame(
                master, text=CONFIG_DIALOG_SERIAL_PORT_HEADING)
        serial_port.grid(
            row=3, column=0, columnspan=3, stick=tk.EW, padx=5, pady=(5, 0))
        tk.Label(serial_port, text=CONFIG_DIALOG_SERIAL_PORT_LABEL).grid(
            row=0, column=0, stick=tk.W, padx=(5, 0), pady=5)
        ttk.Entry(serial_port, textvariable=self._serial_port).grid(
            row=0, column=1, stick=tk.W, padx=(5, 0), pady=5)
        ttk.Separator(master, orient='horizontal').grid(
            row=4, column=0, columnspan=3, stick=tk.EW, pady=(20, 5))
        ttk.Button(master, text=OK_BUTTON_LABEL, command=self.ok).grid(
            row=5, column=1, stick=tk.E, padx=(0, 5), pady=(20, 5))
        ttk.Button(master, text=CANCEL_BUTTON_LABEL, command=self.cancel).grid(
            row=5, column=2, stick=tk.E, padx=(0, 5), pady=(20, 5))
        master.grid_columnconfigure(0, weight=1)
        self.bind("<Escape>", self.cancel)
        self.bind("<Return>", self.ok)
        self._update()

    def ok(self, event=None):
        self._config.period_duration = self._period_duration
        self._config.countdown = self._countdown.get()
        self._config.leading_zero_in_minute = self._leading_zero_in_minute.get()
        self._config.hires_timer_on_last_minute = \
            self._hires_timer_on_last_minute.get()
        self._config.end_of_period_blast = self._end_of_period_blast.get()
        self._config.device_name = self._serial_port.get()
        return widget.BaseDialog.ok(self, event)

    def _on_change_period_duration(self, event=None):
        dialog = InputNumberDialog(
            self,
            CHANGE_PERIOD_DURATION_TITLE,
            CHANGE_PERIOD_DURATION_HEADING,
            self._period_duration)
        period_duration = dialog.value
        if period_duration:
            self._period_duration = int(period_duration)
            self._update()

    def _update(self):
        self._period_duration_label['text'] = \
            PERIOD_DURATION_LABEL.format(self._period_duration)


class TeamWidget(widget.StyledFrame):

    _MAX_SET = 9
    _MAX_SCORE = 199

    def __init__(self, root, title, mirror=False):
        self.title = title
        self._mirror = mirror
        self.set = 0
        self.score = 0
        self._seventh_foul = tk.BooleanVar()
        self._first_timeout = tk.BooleanVar()
        self._second_timeout = tk.BooleanVar()
        widget.StyledFrame.__init__(self, root)

    def _create_widgets(self):
        self._title = ttk.Label(
            self._frame,
            font=TEAM_TITLE_FONT, text=self.title)
        # fouls & timeouts
        self._seventh_foul_button = ttk.Checkbutton(
            self._frame,
            text=SEVENTH_FOUL_BUTTON_LABEL,
            variable=self._seventh_foul)
        self._first_timeout_button = ttk.Checkbutton(
            self._frame,
            text=FIRST_TIMEOUT_BUTTON_LABEL,
            variable = self._first_timeout)
        self._second_timeout_button = ttk.Checkbutton(
            self._frame,
            text=SECOND_TIMEOUT_BUTTON_LABEL,
            variable = self._second_timeout)
        self._increment_set_button = ttk.Button(
            self._frame, text=INCREMENT_SET_BUTTON_LABEL)
        # set
        self._set_title = ttk.Label(
            self._frame, font=SET_TITLE_FONT, text=SET_TITLE)
        self._set = ttk.Label(self._frame, font=SET_FONT)
        self._set['foreground'] = Palette.YELLOW
        self._increment_set_button = ttk.Button(
            self._frame, text=INCREMENT_SET_BUTTON_LABEL)
        self._decrement_set_button = ttk.Button(
            self._frame, text=DECREMENT_SET_BUTTON_LABEL)
        # score
        self._score_title = ttk.Label(
            self._frame, font=SCORE_TITLE_FONT, text=SCORE_TITLE)
        self._score = ttk.Label(self._frame, font=SCORE_FONT)
        self._score['foreground'] = Palette.GREEN
        self._increment_score_button = ttk.Button(
            self._frame, text=INCREMENT_SCORE_BUTTON_LABEL)
        self._decrement_score_button = ttk.Button(
            self._frame, text=DECREMENT_SCORE_BUTTON_LABEL)

    def _create_bindings(self):
        self._increment_set_button['command'] = self._on_increment_set
        self._decrement_set_button['command'] = self._on_decrement_set
        self._increment_score_button['command'] = self._on_increment_score
        self._decrement_score_button['command'] = self._on_decrement_score

    def _define_layout(self):
        self._title.grid(
            row=0, column=0, columnspan=5, pady=TEAM_TITLE_FONT_SIZE)
        self._seventh_foul_button.grid(row=1, column=0)
        self._first_timeout_button.grid(row=1, column=1, columnspan=3)
        self._second_timeout_button.grid(row=1, column=4)
        # set
        set_col, score_col = (0, 3) if not self._mirror else (3, 0)
        self._set_title.grid(
            row=2,
            column=set_col,
            columnspan=2,
            pady=SET_TITLE_FONT_SIZE)
        self._set.grid(row=3, column=set_col, columnspan=2)
        self._increment_set_button.grid(row=4, column=set_col, padx=5)
        self._decrement_set_button.grid(row=4, column=set_col + 1, padx=5)
        # score
        self._score_title.grid(
            row=2,
            column=score_col,
            columnspan=2,
            pady=SCORE_TITLE_FONT_SIZE)
        self._score.grid(row=3, column=score_col, columnspan=2)
        self._increment_score_button.grid(row=4, column=score_col, padx=5)
        self._decrement_score_button.grid(row=4, column=score_col + 1, padx=5)
        self._frame.grid_columnconfigure(0, weight=1)
        self._frame.grid_columnconfigure(1, weight=1)
        self._frame.grid_columnconfigure(2, minsize=SCORE_TITLE_FONT_SIZE)
        self._frame.grid_rowconfigure(0, weight=1)
        self._frame.grid_rowconfigure(1, weight=1)
        self._frame.grid_rowconfigure(2, weight=1)
        self._frame.grid_rowconfigure(3, weight=1)
        self._frame.grid_rowconfigure(4, weight=1)
        self._refresh()

    def _on_increment_set(self, event=None):
        self.set = (self.set + 1) % (self._MAX_SET + 1)
        self._refresh()

    def _on_decrement_set(self, event=None):
        self.set = (self.set - 1) % (self._MAX_SET + 1)
        self._refresh()

    def _on_increment_score(self, event=None):
        self.score = (self.score + 1) % (self._MAX_SCORE + 1)
        self._refresh()

    def _on_decrement_score(self, event=None):
        self.score = (self.score - 1) % (self._MAX_SCORE + 1)
        self._refresh()

    def _refresh(self):
        self._set['text'] = '{:d}'.format(self.set)
        self._score['text'] = '{:d}'.format(self.score)

    @property
    def seventh_foul(self):
        return self._seventh_foul.get()

    @property
    def first_timeout(self):
        return self._first_timeout.get()

    @property
    def second_timeout(self):
        return self._second_timeout.get()


class Application(widget.StyledWidget):

    def __init__(self, root, title):
        self._root = root
        self._title = title
        self._root.title(self._title)
        self._icon = tk.PhotoImage(file = 'consolle.gif')
        self._root.tk.call('wm', 'iconphoto', self._root._w, self._icon)
        # hide the main window as soon as possible
        self._root.withdraw()
        # instantiate the timer
        self._timer = chrono.Timer()
        self._stop_watch = chrono.StopWatch(self._timer, self)
        self._time_view = chrono.TimeView()
        # enable styling
        style = ttk.Style()
        style.configure("TLabel", foreground=self._FOREGROUND_COLOR)
        style.configure("TButton", padding=BUTTON_PADDING)
        style.configure(
            "TCheckbutton",
            foreground=self._FOREGROUND_COLOR,
            background=self._BACKGROUND_COLOR,
            padding=BUTTON_PADDING)
        style.map(
            'TCheckbutton',
            background=[('active', self._BACKGROUND_COLOR)])
        # initial configuration
        self._siren_on = False
        self._scoreboard = None
        self._config = AppConfig()
        self._config_file_path = os.path.expanduser(
            '~/.jolly-handball_consolle.cfg')
        self._config.load(self._config_file_path)
        self._change_config()
        # prepare the main window
        widget.StyledWidget.__init__(self, self._root)
        self._root.deiconify()
        self._set_initial_size()
        self._update()

    def _create_widgets(self):
        # timer
        self._timer_widget = chrono.TimerWidget(
            self._root, self._timer, self._time_view, TIMER_FONT)
        # scores
        self._home_team_widget = TeamWidget(self._root, HOME_TEAM_TITLE)
        self._guest_team_widget = TeamWidget(self._root, GUEST_TEAM_TITLE, True)
        # main window buttons
        self._siren_button = ttk.Button(self._root, text=SIREN_BUTTON_LABEL)
        self._config_button = ttk.Button(self._root, text=CONFIG_BUTTON_LABEL)
        self._quit_button = ttk.Button(self._root, text=QUIT_BUTTON_LABEL)

    def _define_layout(self):
        # timer
        self._timer_widget.grid(row=0, column=0, columnspan=5)
        # scores
        self._home_team_widget.grid(
            row=3, column=0, padx=(0, 5), pady=(5, 0))
        ttk.Separator(self._root, orient='vertical').grid(
            row=3, column=1, stick=tk.NS, pady=(5, 0))
        self._guest_team_widget.grid(
            row=3, column=2, columnspan=3, padx=(5, 0), pady=(5, 0))
        # main window buttons
        self._siren_button.grid(
            row=1, column=0, columnspan=5, pady=5)
        ttk.Separator(self._root, orient='horizontal').grid(
            row=4, column=0, columnspan=5, stick=tk.S + tk.EW, padx=5, pady=5)
        self._config_button.grid(
            row=5, column=3, stick=tk.SE, padx=5, pady=5)
        self._quit_button.grid(
            row=5, column=4, stick=tk.SE, padx=(0, 5), pady=5)
        self._root.grid_columnconfigure(0, weight=1)
        self._root.grid_columnconfigure(2, weight=1)
        self._root.grid_rowconfigure(3, weight=1)

    def _create_bindings(self):
        # main window buttons
        self._siren_button.bind('<Button-1>', self._on_siren_on)
        self._siren_button.bind('<ButtonRelease-1>', self._on_siren_off)
        self._config_button['command'] = self._on_config
        self._quit_button['command'] = self._on_quit
        # main window events
        self._root.protocol('WM_DELETE_WINDOW', self._on_delete_window)

    def _on_siren_on(self, event=None):
        self._siren_on = True

    def _on_siren_off(self, event=None):
        self._siren_on = False

    def _on_config(self, event=None):
        self._change_config()

    def _on_quit(self, event=None):
        self._terminate()

    def _on_delete_window(self):
        self._terminate()

    def _set_initial_size(self):
        self._root.update()
        # force the ttk.Checkbutton styling on windows
        width = self._root.winfo_width()
        height = self._root.winfo_height() + 1
        self._root.geometry('{}x{}'.format(width, height))

    def _update(self):
        self._stop_watch.tick()
        self._timer_widget.refresh()
        self._root.after(20, self._update)
        if self._scoreboard:
            _, _, cent = self._timer.peek()
            self._scoreboard.update(
                scoreboard.Data(
                    timer=self._time_view.peek_figures(self._timer),
                    dot=cent < 50,
                    leading_zero_in_minute = \
                        self._config.leading_zero_in_minute,
                    home_seventh_foul=self._home_team_widget.seventh_foul,
                    home_first_timeout=self._home_team_widget.first_timeout,
                    home_second_timeout=self._home_team_widget.second_timeout,
                    home_set=self._home_team_widget.set,
                    home_score=self._home_team_widget.score,
                    guest_seventh_foul=self._guest_team_widget.seventh_foul,
                    guest_first_timeout=self._guest_team_widget.first_timeout,
                    guest_second_timeout=self._guest_team_widget.second_timeout,
                    guest_set=self._guest_team_widget.set,
                    guest_score=self._guest_team_widget.score,
                    siren=self._siren_on))

    def _change_config(self):
        dialog = ConfigDialog(self._root, self._config)
        self._config.save(self._config_file_path)
        self._stop_watch.stop_at_minute(self._config.period_duration)
        self._time_view.configure(self._config)
        device_name = self._config.device_name
        if not device_name:
            tkMessageBox.showinfo(APP_NAME, RUNNING_WITHOUT_SCOREBOARD)
        else:
            if not self._scoreboard \
                or self._scoreboard.device_name != device_name:
                try:
                    self._scoreboard = scoreboard.Scoreboard(device_name)
                except:
                    self._scoreboard = None
                    _, error, _ = sys.exc_info()
                    tkMessageBox.showerror(
                        APP_NAME,
                        SCOREBOARD_CONNECTION_ERROR.format(device_name, error))

    def _terminate(self):
        self._timer.stop()
        self._root.destroy()

    # StopWatch callback
    def on_stop(self):
        if self._config.end_of_period_blast:
            self._siren_on = True
            self._root.after(1000, self._on_siren_off)


root_ = tk.Tk()
app = Application(root_, '{} - v. {}'.format(APP_NAME, APP_VERSION))
root_.mainloop()
