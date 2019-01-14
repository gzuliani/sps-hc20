#!/usr/bin/python
# -*- coding: utf8 -*-

APP_NAME = "SPS HC20 - CONSOLLE"
APP_VERSION = "0.5" # see setup.py

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
from common import BulletinWindow
from common import InputNumberDialog
from palette import Palette
import scoreboard
import widget

# constants
TIMEOUT_DURATION = 1 # minutes

# font size
TIME_FONT = ('', 72, 'bold')
TEAM_TITLE_FONT_SIZE = 36
TEAM_TITLE_FONT = ('', TEAM_TITLE_FONT_SIZE, 'bold')
SET_TITLE_FONT_SIZE = 24
SET_TITLE_FONT = ('', SET_TITLE_FONT_SIZE)
SET_FONT = ('', 72, 'bold')
SCORE_TITLE_FONT_SIZE = 24
SCORE_TITLE_FONT = ('', SCORE_TITLE_FONT_SIZE)
SCORE_FONT_SIZE = 72
SCORE_FONT = ('', SCORE_FONT_SIZE, 'bold')
COMM_STATS_FONT_SIZE = 8
COMM_STATS_FONT = ('', COMM_STATS_FONT_SIZE)

# padding
BUTTON_PADDING = 10

# main window
SIREN_BUTTON_LABEL = "Sirena"
TIMEOUT_BUTTON_LABEL = "Timeout"
BULLETIN_BUTTON_LABEL = "Comunicato"
CONFIG_BUTTON_LABEL = "Configura"
QUIT_BUTTON_LABEL = "Esci"

# configuration dialog labels
CONFIG_DIALOG_TITLE = "Configurazione Consolle"
CONFIG_DIALOG_HEADING = "Definire la modalità di funzionamento preferita:"
CONFIG_DIALOG_PERIOD_DURATION_HEADING = "Durata di un tempo"
CONFIG_DIALOG_PERIOD_DURATION_TITLE = "Durata di un tempo"
CONFIG_DIALOG_PERIOD_DURATION_LABEL = "{} minuti"
CONFIG_DIALOG_PERIOD_DURATION_HINT = \
    "Specificare la durata di un tempo, in minuti:"
CONFIG_DIALOG_PERIOD_DURATION_BUTTON_LABEL = "Cambia"
CONFIG_DIALOG_OPTIONS_HEADING = "Opzioni"
CONFIG_DIALOG_SERIAL_PORT_HEADING = "Porta seriale"
CONFIG_DIALOG_SERIAL_PORT_LABEL = "Nome del dispositivo:"
CONFIG_DIALOG_LEADING_ZERO_IN_MINUTE_BUTTON_LABEL = \
    "Mostra lo zero iniziale nei minuti"
CONFIG_DIALOG_TENTH_SECOND_ON_LAST_MINUTE_BUTTON_LABEL = \
    "Mostra i decimi di secondo nell'ultimo minuto"
CONFIG_DIALOG_PERIOD_EXPIRED_BLAST_BUTTON_LABEL = \
    "Suona la sirena di fine tempo"
CONFIG_DIALOG_TIMEOUT_CALLED_BLAST_BUTTON_LABEL = \
    "Suona la sirena di inizio timeout"
CONFIG_DIALOG_TIMEOUT_EXPIRED_BLAST_BUTTON_LABEL = \
    "Suona la sirena di imminente fine timeout"
CONFIG_DIALOG_SHOW_COMM_STATS_LABEL = \
    "Mostra le statistiche di comunicazione"

OK_BUTTON_LABEL = "OK"
CANCEL_BUTTON_LABEL = "Annulla"

# main window labels
TIMEOUT_IN_PROGRESS = \
    "Timeout in corso!\n\n" \
    "Il tempo di gioco è fermo a {:02d}:{:02d}.\n\n" \
    "Premere OK alla ripresa del gioco."
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
COMM_STATS_SENT_PACKETS = "Pacchetti spediti: {:d}"
COMM_STATS_BAD_PACKETS = "Pacchetti rifiutati: {:d}"
COMM_STATS_LOST_PACKETS = "Pacchetti persi: {:d}"
COMM_STATS_UNEXPECTED_ERRORS = "Errori generici: {:d}"


class AppConfig(object):

    def __init__(self):
        self._time_view_config = chrono.TimeViewConfig()
        self.period_duration = 30
        self.period_expired_blast = False
        self.timeout_called_blast = False
        self.timeout_expired_blast = False
        self.show_comm_stats = False # for debug purposes only, won't be saved
        self.device_name = ''

    @property
    def aggregate_time(self):
        return self._time_view_config.aggregate_time

    @aggregate_time.setter
    def aggregate_time(self, value):
        self._time_view_config.aggregate_time = value

    @property
    def leading_zero_in_minute(self):
        return self._time_view_config.leading_zero_in_minute

    @leading_zero_in_minute.setter
    def leading_zero_in_minute(self, value):
        self._time_view_config.leading_zero_in_minute = value

    @property
    def tenth_second_on_last_minute(self):
        return self._time_view_config.tenth_second_on_last_minute

    @tenth_second_on_last_minute.setter
    def tenth_second_on_last_minute(self, value):
        self._time_view_config.tenth_second_on_last_minute = value

    def load(self, path):
        try:
            config = SafeConfigParser()
            config.read(path)
            self.period_duration = config.getint(
                'TimeView', 'period_duration')
            self.leading_zero_in_minute = config.getboolean(
                'TimeView', 'leading_zero_in_minute')
            self.tenth_second_on_last_minute = config.getboolean(
                'TimeView', 'tenth_second_on_last_minute')
            self.period_expired_blast = config.getboolean(
                'Consolle', 'period_expired_blast')
            self.timeout_called_blast = config.getboolean(
                'Consolle', 'timeout_called_blast')
            self.timeout_expired_blast = config.getboolean(
                'Consolle', 'timeout_expired_blast')
            self.device_name = config.get('Consolle', 'device_name')
        except:
            pass

    def save(self, path):
        config = SafeConfigParser()
        config.add_section('Consolle')
        config.set('Consolle', 'period_expired_blast',
            str(self.period_expired_blast))
        config.set('Consolle', 'timeout_called_blast',
            str(self.timeout_called_blast))
        config.set('Consolle', 'timeout_expired_blast',
            str(self.timeout_expired_blast))
        config.set('Consolle', 'device_name', self.device_name)
        config.add_section('TimeView')
        config.set('TimeView', 'period_duration', str(self.period_duration))
        config.set('TimeView', 'leading_zero_in_minute',
            str(self.leading_zero_in_minute))
        config.set('TimeView', 'tenth_second_on_last_minute',
            str(self.tenth_second_on_last_minute))
        with open(path, 'w') as file:
            config.write(file)


class ConfigDialog(widget.BaseDialog):

    def __init__(self, master, config):
        self._config = config
        self._period_duration = self._config.period_duration
        self._leading_zero_in_minute = tk.BooleanVar()
        self._leading_zero_in_minute.set(self._config.leading_zero_in_minute)
        self._tenth_second_on_last_minute = tk.BooleanVar()
        self._tenth_second_on_last_minute.set(
            self._config.tenth_second_on_last_minute)
        self._period_expired_blast = tk.BooleanVar()
        self._period_expired_blast.set(self._config.period_expired_blast)
        self._timeout_called_blast = tk.BooleanVar()
        self._timeout_called_blast.set(self._config.timeout_called_blast)
        self._timeout_expired_blast = tk.BooleanVar()
        self._timeout_expired_blast.set(self._config.timeout_expired_blast)
        self._show_comm_stats = tk.BooleanVar()
        self._show_comm_stats.set(self._config.show_comm_stats)
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
            text=CONFIG_DIALOG_PERIOD_DURATION_BUTTON_LABEL).grid(
                row=0, column=1, stick=tk.E, padx=5, pady=5)
        period_duration.grid_columnconfigure(1, weight=1)
        options = tk.LabelFrame(master, text=CONFIG_DIALOG_OPTIONS_HEADING)
        options.grid(
            row=2, column=0, columnspan=3, stick=tk.EW, padx=5, pady=(5, 0))
        tk.Checkbutton(
            options,
            text=CONFIG_DIALOG_LEADING_ZERO_IN_MINUTE_BUTTON_LABEL,
            variable=self._leading_zero_in_minute).grid(
                row=1, column=0, stick=tk.W, padx=5, pady=(5, 0))
        tk.Checkbutton(
            options,
            text=CONFIG_DIALOG_TENTH_SECOND_ON_LAST_MINUTE_BUTTON_LABEL,
            variable=self._tenth_second_on_last_minute).grid(
                row=2, column=0, stick=tk.W, padx=5, pady=(5, 0))
        tk.Checkbutton(
            options,
            text=CONFIG_DIALOG_PERIOD_EXPIRED_BLAST_BUTTON_LABEL,
            variable=self._period_expired_blast).grid(
                row=3, column=0, stick=tk.W, padx=5, pady=(5, 0))
        tk.Checkbutton(
            options,
            text=CONFIG_DIALOG_TIMEOUT_CALLED_BLAST_BUTTON_LABEL,
            variable=self._timeout_called_blast).grid(
                row=4, column=0, stick=tk.W, padx=5, pady=(5, 0))
        tk.Checkbutton(
            options,
            text=CONFIG_DIALOG_TIMEOUT_EXPIRED_BLAST_BUTTON_LABEL,
            variable=self._timeout_expired_blast).grid(
                row=5, column=0, stick=tk.W, padx=5, pady=(5, 0))
        tk.Checkbutton(
            options,
            text=CONFIG_DIALOG_SHOW_COMM_STATS_LABEL,
            variable=self._show_comm_stats).grid(
                row=6, column=0, stick=tk.W, padx=5, pady=(5, 10))
        serial_port = tk.LabelFrame(
                master, text=CONFIG_DIALOG_SERIAL_PORT_HEADING)
        serial_port.grid(
            row=3, column=0, columnspan=3, stick=tk.EW, padx=5, pady=(5, 0))
        tk.Label(serial_port, text=CONFIG_DIALOG_SERIAL_PORT_LABEL).grid(
            row=0, column=0, stick=tk.W, padx=(5, 0), pady=5)
        ttk.Entry(serial_port, textvariable=self._serial_port).grid(
            row=0, column=1, stick=tk.W, padx=(5, 0), pady=5)
        ttk.Button(master, text=OK_BUTTON_LABEL, command=self.ok).grid(
            row=4, column=1, stick=tk.E, padx=(0, 5), pady=(10, 5))
        ttk.Button(master, text=CANCEL_BUTTON_LABEL, command=self.cancel).grid(
            row=4, column=2, stick=tk.E, padx=(0, 5), pady=(10, 5))
        master.grid_columnconfigure(0, weight=1)
        self.bind("<Escape>", self.cancel)
        self.bind("<Return>", self.ok)
        self._update()

    def ok(self, event=None):
        self._config.period_duration = self._period_duration
        self._config.leading_zero_in_minute = self._leading_zero_in_minute.get()
        self._config.tenth_second_on_last_minute = \
            self._tenth_second_on_last_minute.get()
        self._config.period_expired_blast = self._period_expired_blast.get()
        self._config.timeout_called_blast = self._timeout_called_blast.get()
        self._config.timeout_expired_blast = self._timeout_expired_blast.get()
        self._config.show_comm_stats = self._show_comm_stats.get()
        self._config.device_name = self._serial_port.get()
        return widget.BaseDialog.ok(self, event)

    def _on_change_period_duration(self, event=None):
        dialog = InputNumberDialog(
            self,
            CONFIG_DIALOG_PERIOD_DURATION_TITLE,
            CONFIG_DIALOG_PERIOD_DURATION_HINT,
            self._period_duration)
        period_duration = dialog.value
        if period_duration:
            self._period_duration = int(period_duration)
            self._update()

    def _update(self):
        self._period_duration_label['text'] = \
            CONFIG_DIALOG_PERIOD_DURATION_LABEL.format(self._period_duration)


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
        self._update()

    def _on_increment_set(self, event=None):
        self.set = (self.set + 1) % (self._MAX_SET + 1)
        self._update()

    def _on_decrement_set(self, event=None):
        self.set = (self.set - 1) % (self._MAX_SET + 1)
        self._update()

    def _on_increment_score(self, event=None):
        self.score = (self.score + 1) % (self._MAX_SCORE + 1)
        self._update()

    def _on_decrement_score(self, event=None):
        self.score = (self.score - 1) % (self._MAX_SCORE + 1)
        self._update()

    def _update(self):
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


class CommStatWidget(object):

    def __init__(self, root, template):
        self._template = template
        self._label = ttk.Label(
            root,
            font=COMM_STATS_FONT,
            foreground=Palette.BASE0,
            text=template)
        self.update(0)

    def grid(self, *args, **kwargs):
        self._label.grid(*args, **kwargs)

    def grid_forget(self):
        self._label.grid_forget()

    def update(self, count):
        self._label['text'] = self._template.format(count)


class CommStatsWidget(widget.StyledFrame):

    def __init__(self, root):
        widget.StyledFrame.__init__(self, root)

    def _create_widgets(self):
        self._comm_stats = [
            CommStatWidget(
                self._frame, template) for template in [
                    COMM_STATS_SENT_PACKETS,
                    COMM_STATS_BAD_PACKETS,
                    COMM_STATS_LOST_PACKETS,
                    COMM_STATS_UNEXPECTED_ERRORS,
                ]
        ]

    def _define_layout(self):
        for i, comm_stat in enumerate(self._comm_stats):
            comm_stat.grid(row=i, column=0, stick=tk.W)

    def update(self, scoreboard):
        self._comm_stats[0].update(scoreboard.sent_packet_count)
        self._comm_stats[1].update(scoreboard.bad_packet_count)
        self._comm_stats[2].update(scoreboard.lost_packet_count)
        self._comm_stats[3].update(scoreboard.unexpected_error_count)


class Application(widget.StyledWidget):

    def __init__(self, root, title):
        self._root = root
        self._title = title
        self._root.title(self._title)
        self._icon = tk.PhotoImage(file = 'consolle.gif')
        self._root.tk.call('wm', 'iconphoto', self._root._w, self._icon)
        # hide the main window as soon as possible
        self._root.withdraw()
        # timers
        self._timer = chrono.Timer()
        self._timeout_timer_config = chrono.TimeViewConfig()
        self._timeout_timer_config.tenth_second_on_last_minute = False
        self._timeout_timer = chrono.Timer()
        self._timeout_timer.set_period_duration(TIMEOUT_DURATION)
        # bulletin window
        self._bulletin_window = None
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
        # scoreboard
        self._siren_on = False
        self._scoreboard = None
        # load the last used configuration
        self._config = AppConfig()
        self._config_file_path = os.path.expanduser(
            '~/.sps-hc20_consolle.cfg')
        self._config.load(self._config_file_path)
        # prepare the main window
        widget.StyledWidget.__init__(self, self._root)
        self._root.deiconify()
        self._set_initial_size()
        widget.center_window(self._root)
        # show current configuration to the user
        self._change_config()
        self._update()

    def _create_widgets(self):
        # time
        self._timer_widget = chrono.TimerWidget(
            self._root, self._timer, TIME_FONT)
        # scores
        self._home_team_widget = TeamWidget(self._root, HOME_TEAM_TITLE)
        self._guest_team_widget = TeamWidget(self._root, GUEST_TEAM_TITLE, True)
        # communication stats
        self._comm_stats_widget = CommStatsWidget(self._root)
        # main window buttons
        self._siren_button = ttk.Button(self._root, text=SIREN_BUTTON_LABEL)
        self._timeout_button = ttk.Button(
            self._root, text=TIMEOUT_BUTTON_LABEL)
        self._bulletin_button = ttk.Button(
            self._root, text=BULLETIN_BUTTON_LABEL)
        self._config_button = ttk.Button(self._root, text=CONFIG_BUTTON_LABEL)
        self._quit_button = ttk.Button(self._root, text=QUIT_BUTTON_LABEL)

    def _define_layout(self):
        # time
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
            row=1, column=0, stick=tk.E, padx=5, pady=(10, 5))
        self._timeout_button.grid(
            row=1, column=2, stick=tk.W, padx=5, pady=(10, 5))
        ttk.Separator(self._root, orient='horizontal').grid(
            row=4, column=0, columnspan=5, stick=tk.S + tk.EW, padx=5, pady=5)
        self._bulletin_button.grid(
            row=5, column=0, stick=tk.SW, padx=5, pady=5)
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
        self._timeout_button['command'] = self._on_timeout
        self._bulletin_button['command'] = self._on_bulletin
        self._config_button['command'] = self._on_config
        self._quit_button['command'] = self._on_quit
        # keyboard shortcuts
        self._root.bind('<Key-t>', self._on_timeout)
        self._root.bind('<Key-T>', self._on_timeout)
        # main window events
        self._root.protocol('WM_DELETE_WINDOW', self._on_delete_window)

    def _show_comm_stats(self):
        self._comm_stats_widget.grid(
            row=0, column=0, padx=5, pady=5, stick=tk.NW)

    def _hide_comm_stats(self):
        self._comm_stats_widget.grid_forget()

    def _on_siren_on(self, event=None):
        self._siren_on = True

    def _on_siren_off(self, event=None):
        self._siren_on = False

    def _on_timeout(self, event=None):
        if not self._timer.is_running():
            return
        self._timer.stop()
        minute, second, _ = self._timer_widget.now()
        if self._config.timeout_called_blast:
            self._activate_siren()
        self._timeout_timer.reset()
        self._timeout_timer.arm_trigger(0, 50)
        self._timer_widget.change_timer(self._timeout_timer)
        self._timeout_timer.start()
        tkMessageBox.showinfo(
            APP_NAME, TIMEOUT_IN_PROGRESS.format(minute, second))
        self._timeout_timer.stop()
        self._timer_widget.change_timer(self._timer)
        self._timer.start()

    def _bulletin_window_closed(self):
        self._bulletin_window = None

    def _on_bulletin(self, event=None):
        if not self._bulletin_window:
            self._bulletin_window = BulletinWindow(
                self._root, self._scoreboard, self._bulletin_window_closed)
        else:
            self._bulletin_window.lift()

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
        self._root.after(20, self._update)
        self._timer_widget.update()
        if self._timer.is_expired():
            self._period_expired()
        if self._timeout_timer.is_triggered():
            self._timeout_about_to_expire()
        elif self._timeout_timer.is_expired():
            self._timeout_expired()
        if self._timer.is_running():
            self._enable(self._timeout_button)
        else:
            self._disable(self._timeout_button)
        if self._scoreboard:
            _, _, tenth = self._timer_widget.now()
            self._scoreboard.update(
                scoreboard.Data(
                    timestamp=self._timer_widget.figures(),
                    dot=tenth < 5,
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
            self._comm_stats_widget.update(self._scoreboard)

    def _change_config(self):
        dialog = ConfigDialog(self._root, self._config)
        self._config.save(self._config_file_path)
        self._timer.set_period_duration(self._config.period_duration)
        self._timer.configure(self._config)
        self._timeout_timer_config.leading_zero_in_minute = \
            self._config.leading_zero_in_minute
        self._timeout_timer.configure(self._timeout_timer_config)
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
        if self._config.show_comm_stats:
            self._show_comm_stats()
        else:
            self._hide_comm_stats()

    def _terminate(self):
        self._timer.stop()
        self._root.destroy()

    def _period_expired(self):
        if self._config.period_expired_blast:
            self._activate_siren()

    def _timeout_about_to_expire(self):
        if self._config.timeout_expired_blast:
            self._disable(self._timeout_button)
            self._activate_siren()

    def _timeout_expired(self):
        self._timer_widget.change_timer(self._timer)

    def _activate_siren(self):
        self._root.after(0, self._on_siren_on)
        self._root.after(1000, self._on_siren_off)

    # TimerWidget's callback
    def timer_started(self):
        self._enable(self._timeout_button)

    # TimerWidget's callback
    def timer_stopped(self):
        self._disable(self._timeout_button)


root_ = tk.Tk()
app = Application(root_, '{} - v. {}'.format(APP_NAME, APP_VERSION))
root_.mainloop()
