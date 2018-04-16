#!/usr/bin/python
# -*- coding: utf8 -*-

# TODO:
# if a dimissed player misses a penalty no warning is emitted
# penalties phase duration
# add/edit event (?)

try:
    # python 3.x
    from configparser import SafeConfigParser
    import tkinter as tk
    import tkinter.ttk as ttk
    from tkinter import filedialog as tkFileDialog
    from tkinter import messagebox as tkMessageBox
    from tkinter import simpledialog as tkSimpleDialog
except:
    # python 2.x
    from ConfigParser import SafeConfigParser
    import Tkinter as tk
    import ttk
    import tkFileDialog
    import tkMessageBox
    import tkSimpleDialog

import copy
import datetime
import itertools
import os
import re
import sys
import time

import chrono
from dialog import InputNumberDialog
import game
from palette import Palette
import scoreboard
import summary
import widget

TIMEOUT_DURATION = 1 # minutes
EXTRA_PERIOD_DURATION = 5

TIME_FONT = ('', 72, 'bold')
GAME_PHASE_FONT = ('', 36, 'bold')
GAME_TYPE_FONT = ('', 16, 'bold')
GAME_PERIOD_DURATION_FONT = ('', 12)
TITLE_FONT = ('', 12)
TITLE_COLOR = Palette.CYAN
REPORT_FONT_NAME = 'Courier'
MIN_REPORT_FONT_SIZE = 10
MAX_REPORT_FONT_SIZE = 14
REPORT_FONT = (REPORT_FONT_NAME, MIN_REPORT_FONT_SIZE)

# main window
APP_NAME = "Referto Gara"
APP_VERSION = "0.2" # see setup.py

STOP_TIME_DURING_PENALTIES_CHECKBOX_LABEL = \
    "Ferma il contaminuti durante i rigori"
GOAL_BUTTON_LABEL = "Goal"
TIMEOUT_CALL_BUTTON_LABEL = "Time Out"
TIMEOUT_END_BUTTON_LABEL = "Fine Time Out"
WARNING_BUTTON_LABEL = "Ammonizione"
SUSPENSION_BUTTON_LABEL = "2 Minuti"
DISMISS_BUTTON_LABEL = "Squalifica"
PENALTY_BUTTON_LABEL = "Rigore"
EXPORT_EVENTS_BUTTON_LABEL = "Salva..."
DELETE_EVENT_BUTTON_LABEL = "Cancella Evento"
SIREN_BUTTON_LABEL = "Sirena"
CONFIG_BUTTON_LABEL = "Configura"
QUIT_BUTTON_LABEL = "Esci"

# common buttons
OK_BUTTON_LABEL = "OK"
CANCEL_BUTTON_LABEL = "Annulla"

# team names
A_TEAM_BUTTON_LABEL = game.TEAM_A_ID
B_TEAM_BUTTON_LABEL = game.TEAM_B_ID

# game phase-related labels
GAME_PHASE_NAMES = {
    game.GamePhase.BEFORE_MATCH: "PREPARTITA",
    game.GamePhase.FIRST_PERIOD: "1° TEMPO",
    game.GamePhase.INTERVAL: "INTERVALLO",
    game.GamePhase.SECOND_PERIOD: "2° TEMPO",
    game.GamePhase.FIRST_EXTRA_PERIOD: "1° TEMPO SUPPL.",
    game.GamePhase.SECOND_EXTRA_PERIOD: "2° TEMPO SUPPL",
    game.GamePhase.PENALTIES: "RIGORI",
    game.GamePhase.AFTER_MATCH: "FINE PARTITA",
}

GAME_PHASE_ABBREVIATIONS = {
    game.GamePhase.BEFORE_MATCH: "-",
    game.GamePhase.FIRST_PERIOD: "1T",
    game.GamePhase.INTERVAL: "I",
    game.GamePhase.SECOND_PERIOD: "2T",
    game.GamePhase.FIRST_EXTRA_PERIOD: "1TS",
    game.GamePhase.SECOND_EXTRA_PERIOD: "2TS",
    game.GamePhase.PENALTIES: "R",
    game.GamePhase.AFTER_MATCH: "-",
}

PROGRESS_BUTTON_START_LIVE_PHASE_LABELS = {
    game.GamePhase.FIRST_PERIOD: \
        "Inizio 1° Tempo",
    game.GamePhase.SECOND_PERIOD: \
        "Inizio 2° Tempo",
    game.GamePhase.FIRST_EXTRA_PERIOD: \
        "Inizio 1° T.S.",
    game.GamePhase.SECOND_EXTRA_PERIOD: \
        "Inizio 2° T.S.",
    game.GamePhase.PENALTIES: \
        "Rigori",
}

PROGRESS_BUTTON_STOP_LIVE_PHASE_LABELS = {
    game.GamePhase.FIRST_PERIOD: \
        "Fine 1° Tempo",
    game.GamePhase.SECOND_PERIOD: \
        "Fine 2° Tempo",
    game.GamePhase.FIRST_EXTRA_PERIOD: \
        "Fine 1° T. S.",
    game.GamePhase.SECOND_EXTRA_PERIOD: \
        "Fine 2° T. S.",
    game.GamePhase.PENALTIES: \
        "Fine Partita",
}

# accelerators
GOAL_KEY = '<Key-g>'
TIMEOUT_KEY = '<Key-t>'
WARNING_KEY = '<Key-a>'
SUSPENSION_KEY = '<Key-2>'
DISMISS_KEY = '<Key-s>'
PENALTY_KEY = '<Key-r>'
PROGRESS_KEY = '<Key-p>'
DELETE_EVENT_KEY = '<Key-Delete>'

# main window labels
CHAMPIONSHIP_GAME_TITLE = "Partita di Campionato"
CHAMPIONSHIP_GAME_PERIOD_DURATION = " - tempi da {} minuti - "
KNOCKOUT_GAME_TITLE = "Partita ad Eliminazione"
KNOCKOUT_GAME_PERIOD_DURATION = \
    " - tempi regolamentari da {0} minuti, supplementari da {1} minuti - "
UNKNOWN_GAME_TITLE = "Gara "
TIMEOUT_LABEL = "TIMEOUT"
TEAM_REPORT_TITLE = "SQUADRA {}"
SUSPENSION_REPORTS_HEADING = "SOSPENSIONI IN CORSO"

GAME_INCONSISTENCIES_DIALOG_TITLE = "Elenco Incongruenze"
GAME_INCONSISTENCIES_DIALOG_MESSAGE = \
    "Sono state registrate le seguenti incongruenze:"

# team selection
SELECT_TEAM_CODE = "Seleziona una squadra:"

# player selection
INPUT_PLAYER_NUMBER = "Numero del giocatore:"
INVALID_PLAYER_CODE = "Il codice giocatore \"{}\" non è valido."

# info
RUNNING_WITHOUT_SCOREBOARD = \
    "La porta seriale cui dovrebbe essere collegato il dispositivo di " \
    "comunicazione con il tabellone non è stata specificata.\n\n" \
    "Il programma funzionerà normalmente, ma non invierà i comandi di " \
    "controllo del tabellone."

# errors
SCOREBOARD_CONNECTION_ERROR = \
    "Impossibile connettersi al tabellone attraverso la porta \"{}\" " \
    "a causa dell'errore:\n\n{}\n\n" \
    "Verificare che il dispositivo di comunicazione con il tabellone " \
    "sia connesso al computer alla presa USB corretta, " \
    "oppure indicare il nome della porta seriale associata " \
    "a quella cui è collegato in questo momento.\n\n" \
    "Se si indica la presa sbagliata il programma funzionerà normalmente, " \
    "ma non invierà i comandi di controllo del tabellone."

# warnings
GAME_INTERRUPTED = "Il gioco è momentaneamente sospeso."

PLAYER_ALREADY_WARNED = \
    "Il giocatore n. {1} della squadra \"{0}\" è già stato ammonito."

PLAYER_DISMISSED = \
    "Il giocatore n. {1} della squadra \"{0}\" risulta squalificato."

EXTRA_TIMEOUT_IN_GAME_PHASE = \
    "La squadra \"{}\" ha esaurito i suoi timeout per questa frazione di gioco."

EXTRA_TIMEOUT_IN_GAME = \
    "La squadra \"{}\" ha esaurito i suoi timeout per questa partita."

UNEXPECTED_TIMEOUT_CALL = \
    "Le squadre non possono chiamare un timeout durante questa fase di gioco."

ACCEPT_INVALID_TIMEOUT_CALL = \
    "Chiamata di timeout non valida della squadra {}"

ACCEPT_EXTRA_TIMEOUT_CALL = \
    "Chiamata di timeout extra della squadra {}"

ACCEPT_GOAL_BY_DISMISSED_PLAYER = \
    "Goal di {}{}, che risulta squalificato"

ACCEPT_WARNING_FOR_DISMISSED_PLAYER = \
    "Ammonizione per {}{}, che risulta squalificato"

ACCEPT_WARNING_FOR_WARNED_PLAYER = \
    "Ammonizione per {}{}, che risulta già ammonito"

ACCEPT_SUSPENSION_FOR_DISMISSED_PLAYER = \
    "Sospensione per {}{}, che risulta squalificato"

ACCEPT_DISMISS_FOR_DISMISSED_PLAYER = \
    "Squalifica per {}{}, che risulta squalificato"

ACCEPT_EVENT_DURING_NON_LIVE_PHASE = \
    "Evento al di fuori di una fazione di gioco"

# questions
CONFIRM_PENALTY_SCORED = "Il giocatore ha segnato il rigore?"

CONFIRM_ACCEPT_GOAL_BY_DISMISSED_PLAYER = \
    "Il giocatore n. {1} della squadra \"{0}\" risulta squalificato.\n\n" \
    "Mettere comunque a referto questo goal?"

CONFIRM_ACCEPT_EXTRA_TIMEOUT_IN_GAME_PHASE = \
    "La squadra \"{}\" ha già usato i timeout a sua disposizione" \
    " per questa frazione di gioco.\n\n" \
    "Mettere comunque a referto questa nuova chiamata?"

CONFIRM_ACCEPT_EXTRA_TIMEOUT_IN_GAME = \
    "La squadra \"{}\" ha già usato i timeout a sua disposizione" \
    " per questa partita.\n\n" \
    "Mettere comunque a referto questa nuova chiamata?"

CONFIRM_ACCEPT_UNEXPECTED_TIMEOUT = \
    "Le squadre non dovrebbero chiamare un timeout" \
    " durante questa frazione di gioco.\n\n" \
    "Mettere comunque a referto questa nuova chiamata?"

CONFIRM_ACCEPT_WARNING_FOR_DISMISSED_PLAYER = \
    "Il giocatore n. {1} della squadra \"{0}\" risulta squalificato.\n\n" \
    "Mettere comunque a referto questa ammonizione?"

CONFIRM_ACCEPT_WARNING_FOR_WARNED_PLAYER = \
    "Il giocatore n. {1} della squadra \"{0}\" risulta già ammonito.\n\n" \
    "Mettere comunque a referto questa nuova ammonizione?"

CONFIRM_ACCEPT_SUSPENSION_FOR_DISMISSED_PLAYER = \
    "Il giocatore n. {1} della squadra \"{0}\" risulta squalificato.\n\n" \
    "Mettere comunque a referto questa sospensione?"

CONFIRM_ACCEPT_DISMISS_FOR_DISMISSED_PLAYER = \
    "Il giocatore n. {1} della squadra \"{0}\" risulta squalificato.\n\n" \
    "Mettere comunque a referto questa nuova squalifica?"

CONFIRM_ACCEPT_EVENT_DURING_NON_LIVE_PHASE = \
    "Il gioco è momentaneamente sospeso.\n\n" \
    "Mettere comunque a referto questo evento?"

CONFIRM_DELETE_EVENT = "Vuoi davvero cancellare l'evento selezionato?"
CONFIRM_QUIT = "Vuoi davvero abbandonare la sessione?"

# event list
TXT_FILE_TYPE = "File di testo"
ANY_FILE_TYPE = "Tutti i file"
FILE_NAME_TEMPLATE = "partita-del-{}"

# configuration dialog labels
CONFIG_DIALOG_TITLE = "Configurazione Generale"
CONFIG_DIALOG_HEADING = "Definire la modalità di funzionamento preferita:"
CONFIG_DIALOG_GAME_TYPE_HEADING = "Tipo di partita"
CONFIG_DIALOG_GAME_TYPE_CHAMPIONSHIP = "Campionato (2 tempi regolamentari)"
CONFIG_DIALOG_GAME_TYPE_KNOKOUT = \
    "Eliminazione diretta (con tempi supplementari e rigori)"
CONFIG_DIALOG_PERIOD_DURATION_HEADING = "Durata di un tempo"
CONFIG_DIALOG_PERIOD_DURATION_TITLE = "Durata di un tempo"
CONFIG_DIALOG_PERIOD_DURATION_LABEL = "{} minuti"
CONFIG_DIALOG_PERIOD_DURATION_HINT = \
    "Specificare la durata di un tempo, in minuti:"
CONFIG_DIALOG_PERIOD_DURATION_BUTTON_LABEL = "Cambia"
CONFIG_DIALOG_OPTIONS_HEADING = "Opzioni"
CONFIG_DIALOG_SERIAL_PORT_HEADING = "Collegamento al tabellone"
CONFIG_DIALOG_SERIAL_PORT_LABEL = "Porta seriale:"
CONFIG_DIALOG_AGGREGATE_TIME_BUTTON_LABEL = "Mostra il tempo aggregato"
CONFIG_DIALOG_LEADING_ZERO_IN_MINUTE_BUTTON_LABEL = \
    "Mostra lo zero iniziale nei minuti"
CONFIG_DIALOG_TENTH_SECOND_ON_LAST_MINUTE_BUTTON_LABEL = \
    "Mostra i decimi di secondo nell'ultimo minuto"
CONFIG_DIALOG_PERIOD_EXPIRED_BLAST_BUTTON_LABEL = \
    "Suona la sirena di fine tempo"
CONFIG_DIALOG_TIMEOUT_HEADING = "Timeout"
CONFIG_DIALOG_SHOW_TIMEOUT_TIME_BUTTON_LABEL = \
    "Mostra il minuto di timeout sul tabellone"
CONFIG_DIALOG_TIMEOUT_CALLED_BLAST_BUTTON_LABEL = \
    "Suona la sirena di inizio timeout"
CONFIG_DIALOG_TIMEOUT_EXPIRING_BLAST_BUTTON_LABEL = \
    "Suona la sirena di imminente fine del timeout"
CONFIG_DIALOG_SHOW_TIMEOUT_CALLS_ON_SCOREBOARD_BUTTON_LABEL = \
    "Mostra le chiamate dei timeout sul tabellone"


class AppConfig(object):

    def __init__(self):
        self.time_view_config = chrono.TimeViewConfig()
        self.knock_out_game = False
        self.period_expired_blast = False
        self.show_timeout_time = False
        self.timeout_called_blast = False
        self.timeout_expiring_blast = False
        self.show_timeout_calls_on_scoreboard = False
        self.device_name = ''
        self._match = None

    def clone(self):
        config = AppConfig()
        config.time_view_config = copy.copy(self.time_view_config)
        config.knock_out_game = self.knock_out_game
        config.period_expired_blast = self.period_expired_blast
        config.device_name = self.device_name
        config._match = self._match
        return config

    @property
    def aggregate_time(self):
        return self.time_view_config.aggregate_time

    @aggregate_time.setter
    def aggregate_time(self, value):
        self.time_view_config.aggregate_time = value

    @property
    def leading_zero_in_minute(self):
        return self.time_view_config.leading_zero_in_minute

    @leading_zero_in_minute.setter
    def leading_zero_in_minute(self, value):
        self.time_view_config.leading_zero_in_minute = value

    @property
    def tenth_second_on_last_minute(self):
        return self.time_view_config.tenth_second_on_last_minute

    @tenth_second_on_last_minute.setter
    def tenth_second_on_last_minute(self, value):
        self.time_view_config.tenth_second_on_last_minute = value

    def load(self, path):
        try:
            config = SafeConfigParser()
            config.read(path)
            self.period_duration = config.getint(
                'TimeView', 'period_duration')
            self.aggregate_time = config.getboolean(
                'TimeView', 'aggregate_time')
            self.leading_zero_in_minute = config.getboolean(
                'TimeView', 'leading_zero_in_minute')
            self.tenth_second_on_last_minute = config.getboolean(
                'TimeView', 'tenth_second_on_last_minute')
            self.period_expired_blast = config.getboolean(
                'Report', 'period_expired_blast')
            self.show_timeout_time = config.getboolean(
                'Report', 'show_timeout_time')
            self.timeout_called_blast = config.getboolean(
                'Report', 'timeout_called_blast')
            self.timeout_expiring_blast = config.getboolean(
                'Report', 'timeout_expiring_blast')
            self.show_timeout_calls_on_scoreboard = config.getboolean(
                'Report', 'show_timeout_calls_on_scoreboard')
            self.device_name = config.get(
                'Report', 'device_name')
        except:
            pass

    def save(self, path):
        config = SafeConfigParser()
        config.add_section('Report')
        config.set('Report', 'period_expired_blast',
            str(self.period_expired_blast))
        config.set('Report', 'show_timeout_time',
            str(self.show_timeout_time))
        config.set('Report', 'timeout_called_blast',
            str(self.timeout_called_blast))
        config.set('Report', 'timeout_expiring_blast',
            str(self.timeout_expiring_blast))
        config.set('Report', 'show_timeout_calls_on_scoreboard',
            str(self.show_timeout_calls_on_scoreboard))
        config.set('Report', 'device_name', self.device_name)
        config.add_section('TimeView')
        config.set('TimeView', 'period_duration', str(self.period_duration))
        config.set('TimeView', 'aggregate_time', str(self.aggregate_time))
        config.set('TimeView', 'leading_zero_in_minute',
            str(self.leading_zero_in_minute))
        config.set('TimeView', 'tenth_second_on_last_minute',
            str(self.tenth_second_on_last_minute))
        with open(path, 'w') as file:
            config.write(file)

    def match(self, match):
        self._match = match

    def to_aggregate_time(self, phase, minute, second, tenth):
        return minute + self._elapsed(phase), second, tenth

    def to_period_time(self, phase, minute, second, tenth):
        return minute - self._elapsed(phase), second, tenth

    def _elapsed(self, current_phase):
        self._last_elapsed = []
        if not self.aggregate_time:
            return 0
        if not self._match:
            return 0
        else:
            if not current_phase:
                current_phase = self._match.current_phase()
            phases = list(itertools.takewhile(
                lambda p: p != current_phase, self._match.phases()))
            return sum(p.duration for p in phases if p.is_live and p.is_expired)


class ConfigDialog(widget.BaseDialog):

    def __init__(self, master, config, is_initial_config):
        self._config = config
        self._is_initial_config = is_initial_config
        self._game_type = tk.IntVar()
        self._game_type.set(1 if self._config.knock_out_game else 0)
        self._period_duration = self._config.period_duration
        self._aggregate_time = tk.BooleanVar()
        self._aggregate_time.set(self._config.aggregate_time)
        self._leading_zero_in_minute = tk.BooleanVar()
        self._leading_zero_in_minute.set(self._config.leading_zero_in_minute)
        self._tenth_second_on_last_minute = tk.BooleanVar()
        self._tenth_second_on_last_minute.set(
            self._config.tenth_second_on_last_minute)
        self._period_expired_blast = tk.BooleanVar()
        self._period_expired_blast.set(self._config.period_expired_blast)
        self._show_timeout_time = tk.BooleanVar()
        self._show_timeout_time.set(self._config.show_timeout_time)
        self._timeout_called_blast = tk.BooleanVar()
        self._timeout_called_blast.set(self._config.timeout_called_blast)
        self._timeout_expiring_blast = tk.BooleanVar()
        self._timeout_expiring_blast.set(self._config.timeout_expiring_blast)
        self._show_timeout_calls_on_scoreboard = tk.BooleanVar()
        self._show_timeout_calls_on_scoreboard.set(
            self._config.show_timeout_calls_on_scoreboard)
        self._serial_port = tk.StringVar()
        self._serial_port.set(self._config.device_name)
        widget.BaseDialog.__init__(self, master, CONFIG_DIALOG_TITLE)

    def body(self, master):
        tk.Label(master, text=CONFIG_DIALOG_HEADING, justify=tk.LEFT).grid(
            row=0, column=0, columnspan=3, stick=tk.W, padx=5, pady=5)
        game_type = tk.LabelFrame(
                master, text=CONFIG_DIALOG_GAME_TYPE_HEADING)
        game_type.grid(
            row=1, column=0, columnspan=3, stick=tk.EW, padx=5, pady=(5, 0))
        tk.Radiobutton(
            game_type,
            text=CONFIG_DIALOG_GAME_TYPE_CHAMPIONSHIP,
            variable=self._game_type,
            value=0).grid(
                row=0, column=1, stick=tk.W, padx=5, pady=(5, 0))
        tk.Radiobutton(
            game_type,
            text=CONFIG_DIALOG_GAME_TYPE_KNOKOUT,
            variable=self._game_type,
            value=1).grid(
                row=1, column=1, stick=tk.W, padx=5, pady=(0, 5))
        period_duration = tk.LabelFrame(
                master, text=CONFIG_DIALOG_PERIOD_DURATION_HEADING)
        period_duration.grid(
            row=2, column=0, columnspan=3, stick=tk.EW, padx=5, pady=(5, 0))
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
            row=3, column=0, columnspan=3, stick=tk.EW, padx=5, pady=(5, 0))
        tk.Checkbutton(
            options,
            text=CONFIG_DIALOG_AGGREGATE_TIME_BUTTON_LABEL,
            variable=self._aggregate_time).grid(
                row=0, column=0, stick=tk.W, padx=5, pady=(10, 0))
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
                row=3, column=0, stick=tk.W, padx=5, pady=(5, 10))
        timeout = tk.LabelFrame(master, text=CONFIG_DIALOG_TIMEOUT_HEADING)
        timeout.grid(
            row=4, column=0, columnspan=3, stick=tk.EW, padx=5, pady=(5, 0))
        tk.Checkbutton(
            timeout,
            text=CONFIG_DIALOG_SHOW_TIMEOUT_TIME_BUTTON_LABEL,
            variable=self._show_timeout_time).grid(
                row=0, column=0, stick=tk.W, padx=5, pady=(10, 0))
        tk.Checkbutton(
            timeout,
            text=CONFIG_DIALOG_TIMEOUT_CALLED_BLAST_BUTTON_LABEL,
            variable=self._timeout_called_blast).grid(
                row=1, column=0, stick=tk.W, padx=5, pady=(5, 0))
        tk.Checkbutton(
            timeout,
            text=CONFIG_DIALOG_TIMEOUT_EXPIRING_BLAST_BUTTON_LABEL,
            variable=self._timeout_expiring_blast).grid(
                row=2, column=0, stick=tk.W, padx=5, pady=(5, 0))
        tk.Checkbutton(
            timeout,
            text=CONFIG_DIALOG_SHOW_TIMEOUT_CALLS_ON_SCOREBOARD_BUTTON_LABEL,
            variable=self._show_timeout_calls_on_scoreboard).grid(
                row=7, column=0, stick=tk.W, padx=5, pady=(5, 10))
        serial_port = tk.LabelFrame(
                master, text=CONFIG_DIALOG_SERIAL_PORT_HEADING)
        serial_port.grid(
            row=5, column=0, columnspan=3, stick=tk.EW, padx=5, pady=(5, 0))
        tk.Label(serial_port, text=CONFIG_DIALOG_SERIAL_PORT_LABEL).grid(
            row=0, column=0, stick=tk.W, padx=(5, 0), pady=5)
        ttk.Entry(serial_port, textvariable=self._serial_port).grid(
            row=0, column=1, stick=tk.W, padx=(5, 0), pady=5)
        ttk.Separator(master, orient='horizontal').grid(
            row=6, column=0, columnspan=3, stick=tk.EW, pady=(20, 5))
        ttk.Button(master, text=OK_BUTTON_LABEL, command=self.ok).grid(
            row=7, column=1, stick=tk.E, padx=(0, 5), pady=(20, 5))
        ttk.Button(master, text=CANCEL_BUTTON_LABEL, command=self.cancel).grid(
            row=7, column=2, stick=tk.E, padx=(0, 5), pady=(20, 5))
        master.grid_columnconfigure(0, weight=1)
        self.bind('<Escape>', self.cancel)
        self.bind('<Return>', self.ok)
        self._update()
        if not self._is_initial_config:
            for frame in [game_type, period_duration]:
                for child in frame.winfo_children():
                    child.configure(state=tk.DISABLED)

    def ok(self, event=None):
        self._config.period_duration = self._period_duration
        self._config.aggregate_time = self._aggregate_time.get()
        self._config.leading_zero_in_minute = self._leading_zero_in_minute.get()
        self._config.tenth_second_on_last_minute = \
            self._tenth_second_on_last_minute.get()
        self._config.knock_out_game = self._game_type.get() == 1
        self._config.period_expired_blast = self._period_expired_blast.get()
        self._config.show_timeout_time = self._show_timeout_time.get()
        self._config.timeout_called_blast = self._timeout_called_blast.get()
        self._config.timeout_expiring_blast = \
            self._timeout_expiring_blast.get()
        self._config.show_timeout_calls_on_scoreboard = \
            self._show_timeout_calls_on_scoreboard.get()
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


def catch_exceptions(method):
    def wrapper(*args, **keyargs):
        try:
            return method(*args, **keyargs)
        except game.InvalidPlayerCode:
            _, ex, _ = sys.exc_info()
            tkMessageBox.showerror(
                APP_NAME, INVALID_PLAYER_CODE.format(ex.code))
        except game.PlayerIsDismissed:
            _, ex, _ = sys.exc_info()
            tkMessageBox.showerror(
                APP_NAME, PLAYER_DISMISSED.format(
                    ex.player.team_id, ex.player.number))
        except game.PlayerAlreadyWarned:
            _, ex, _ = sys.exc_info()
            tkMessageBox.showerror(
                APP_NAME, PLAYER_ALREADY_WARNED.format(
                    ex.player.team_id, ex.player.number))
        except game.ExtraTimeoutInGamePhase:
            _, ex, _ = sys.exc_info()
            tkMessageBox.showerror(
                APP_NAME, EXTRA_TIMEOUT_IN_GAME_PHASE.format(ex.team.id))
        except game.ExtraTimeoutInGame:
            _, ex, _ = sys.exc_info()
            tkMessageBox.showerror(
                APP_NAME, EXTRA_TIMEOUT_IN_GAME.format(ex.team.id))
        except game.UnexpectedTimeoutCall:
            _, ex, _ = sys.exc_info()
            tkMessageBox.showerror(
                APP_NAME, UNEXPECTED_TIMEOUT_CALL.format(ex.team.id))
        except game.GameInterrupted:
            tkMessageBox.showerror(APP_NAME, GAME_INTERRUPTED)
    return wrapper


class GameObserver(object):

    def accept_unexpected_timeout(self, team, phase):
        return tkMessageBox.askyesno(
            APP_NAME, CONFIRM_ACCEPT_UNEXPECTED_TIMEOUT.format(team.id))

    def accept_additional_timeout_in_game_phase(self, team, phase):
        return tkMessageBox.askyesno(
            APP_NAME,
            CONFIRM_ACCEPT_EXTRA_TIMEOUT_IN_GAME_PHASE.format(team.id))

    def accept_additional_timeout_in_game(self, team):
        return tkMessageBox.askyesno(
            APP_NAME, CONFIRM_ACCEPT_EXTRA_TIMEOUT_IN_GAME.format(team.id))

    def accept_goal_by_dismissed_player(self, player):
        return tkMessageBox.askyesno(
            APP_NAME,
            CONFIRM_ACCEPT_GOAL_BY_DISMISSED_PLAYER.format(
                player.team_id, player.number))

    def accept_warning_for_dismissed_player(self, player):
        return tkMessageBox.askyesno(
            APP_NAME,
            CONFIRM_ACCEPT_WARNING_FOR_DISMISSED_PLAYER.format(
                player.team_id, player.number))

    def accept_warning_for_warned_player(self, player):
        return tkMessageBox.askyesno(
            APP_NAME,
            CONFIRM_ACCEPT_WARNING_FOR_WARNED_PLAYER.format(
                player.team_id, player.number))

    def accept_suspension_for_dismissed_player(self, player):
        return tkMessageBox.askyesno(
            APP_NAME,
            CONFIRM_ACCEPT_SUSPENSION_FOR_DISMISSED_PLAYER.format(
                player.team_id, player.number))

    def accept_dismiss_for_dismissed_player(self, player):
        return tkMessageBox.askyesno(
            APP_NAME,
            CONFIRM_ACCEPT_DISMISS_FOR_DISMISSED_PLAYER.format(
                player.team_id, player.number))

    def accept_event_during_non_live_phase(self):
        return tkMessageBox.askyesno(
            APP_NAME, CONFIRM_ACCEPT_EVENT_DURING_NON_LIVE_PHASE)


class DeleteEventObserver(object):

    def __init__(self):
        self.warnings = []

    def accept_unexpected_timeout(self, team, phase):
        self.warnings.append(ACCEPT_INVALID_TIMEOUT_CALL.format(team.id))
        return True

    def accept_additional_timeout_in_game_phase(self, team, phase):
        self.warnings.append(ACCEPT_EXTRA_TIMEOUT_CALL.format(team.id))
        return True

    def accept_additional_timeout_in_game(self, team):
        self.warnings.append(ACCEPT_EXTRA_TIMEOUT_CALL.format(team.id))
        return True

    def accept_goal_by_dismissed_player(self, player):
        self.warnings.append(ACCEPT_GOAL_BY_DISMISSED_PLAYER.format(
                player.team_id, player.number))
        return True

    def accept_warning_for_dismissed_player(self, player):
        self.warnings.append(WARNING_FOR_DISMISSED_PLAYER.format(
            player.team_id, player.number))
        return True

    def accept_warning_for_warned_player(self, player):
        self.warnings.append(WARNING_FOR_WARNED_PLAYER.format(
            player.team_id, player.number))
        return True

    def accept_suspension_for_dismissed_player(self, player):
        self.warnings.append(SUSPENSION_FOR_DISMISSED_PLAYER.format(
            player.team_id, player.number))
        return True

    def accept_dismiss_for_dismissed_player(self, player):
        self.warnings.append(DISMISS_FOR_DISMISSED_PLAYER.format(
            player.team_id, player.number))
        return True

    def accept_event_during_non_live_phase(self):
        self.warnings.append(ACCEPT_EVENT_DURING_NON_LIVE_PHASE)
        return True


class GamePhaseWidget(widget.StyledFrame):

    def __init__(self, root, match):
        self._flashing_on = False
        if type(match._course) == game.ChampionshipGameCourse:
            self._game_type = CHAMPIONSHIP_GAME_TITLE
            self._period_duration = \
                CHAMPIONSHIP_GAME_PERIOD_DURATION.format(
                    match.period_duration())
        elif type(match._course) == game.KnockOutGameCourse:
            self._game_type = KNOCKOUT_GAME_TITLE
            self._period_duration = \
                KNOCKOUT_GAME_PERIOD_DURATION.format(
                    match.period_duration(), match.extra_period_duration())
        else:
            self._game_type = UNKNOWN_GAME_TITLE
            self._period_duration = ''
        widget.StyledFrame.__init__(self, root)

    def _create_widgets(self):
        self._game_phase = ttk.Label(
            self._frame, font=GAME_PHASE_FONT)
        self._game_description = ttk.Label(
            self._frame,
            text=self._game_type,
            font=GAME_TYPE_FONT)
        self._game_length = ttk.Label(
            self._frame,
            text=self._period_duration,
            font=GAME_PERIOD_DURATION_FONT)

    def _define_layout(self):
        self._game_phase.grid(row=0, column=0, pady=(50, 0))
        self._game_description.grid(row=1, column=0, pady=(32, 5))
        self._game_length.grid(row=2, column=0)

    def _apply_style(self):
        widget.StyledFrame._apply_style(self)
        self._game_phase['foreground'] = Palette.YELLOW
        self._game_description['foreground'] = Palette.VIOLET
        self._game_length['foreground'] = Palette.VIOLET
        self._foreground = self._game_phase['foreground']
        self._background = self._game_phase['background']

    def show(self, message):
        if self._flashing_on:
            self._stop_flash()
        self._game_phase['text'] = message

    def flash(self, message):
        self._game_phase['foreground'] = Palette.RED
        self._prev_message = self._game_phase['text']
        self._game_phase['text'] = message
        self._flashing_on = True
        self._flashing_cycle = 'on'
        self._do_flash()

    def restore(self):
        self._stop_flash()
        self._game_phase['text'] = self._prev_message

    def _do_flash(self):
        if not self._flashing_on:
            return
        if self._flashing_cycle == 'on':
            self._game_phase['foreground'] = Palette.RED
            self._flashing_cycle = 'off'
        else:
            self._game_phase['foreground'] = self._background
            self._flashing_cycle = 'on'
        self._game_phase.after(500, self._do_flash)

    def _stop_flash(self):
        self._flashing_on = False
        self._game_phase['foreground'] = self._foreground
        self._game_phase['background'] = self._background


class EventListWidget(widget.StyledFrame):

    def __init__(self, root, observer):
        self._observer = observer
        self._event_from_row = {}
        self._report = summary.EventList()
        widget.StyledFrame.__init__(self, root)

    def _create_widgets(self):
        self._header = ttk.Label(
            self._frame,
            font=REPORT_FONT,
            text=summary.EventList.header())
        self._list = tk.Listbox(
            self._frame,
            activestyle=tk.DOTBOX,
            font=REPORT_FONT,
            selectmode=tk.BROWSE)
        self._scrollbar = tk.Scrollbar(self._frame)
        self._export_button = ttk.Button(
            self._frame, text=EXPORT_EVENTS_BUTTON_LABEL)
        self._delete_button = ttk.Button(
            self._frame, text=DELETE_EVENT_BUTTON_LABEL)

    def _create_bindings(self):
        self._list['yscrollcommand'] = self._scrollbar.set
        self._scrollbar['command'] = self._list.yview
        self._export_button['command'] = self._on_export
        self._delete_button['command'] = self._on_delete
        # keyboard shortcuts
        self._root.bind(DELETE_EVENT_KEY, self._on_delete)

    def _define_layout(self):
        self._header.grid(row=0, column=0, columnspan=4, stick=tk.EW)
        self._list.grid(row=1, column=0, columnspan=3, stick=tk.NSEW, padx=0)
        self._scrollbar.grid(row=1, column=3, stick=tk.NS)
        self._export_button.grid(
            row=2,
            column=0,
            stick=tk.W,
            pady=(5, 0))
        self._delete_button.grid(
            row=2,
            column=2,
            stick=tk.E,
            pady=(5, 0))
        self._frame.grid_rowconfigure(1, weight=1)
        self._frame.grid_columnconfigure(0, weight=1)

    def _apply_style(self):
        widget.StyledFrame._apply_style(self)
        self._list['background'] = self._BACKGROUND_COLOR

    def set_font_size(self, size):
        self._header['font'] = (REPORT_FONT_NAME, size)
        self._list['font'] = (REPORT_FONT_NAME, size)

    def reload(self, events, config):
        self._clear()
        for event in events:
            self.append(event, config)

    def append(self, event, config):
        row = self._list.size()
        self._event_from_row[row] = event
        text = self._report.render_event(event, config)
        self._list.insert(tk.END, text)
        self._select_last_event()

    def focus_set(self):
        self._list.focus_set()

    def _on_export(self, event=None):
        file = tkFileDialog.asksaveasfile(
            mode='w',
            defaultextension='.txt',
            filetypes=[(TXT_FILE_TYPE, '*.txt'), (ANY_FILE_TYPE, '*.*')],
            initialfile=FILE_NAME_TEMPLATE.format(
                datetime.date.today().isoformat()),
            title=EXPORT_EVENTS_BUTTON_LABEL)
        if not file:
            return
        file.write(self._header['text'] + '\n')
        for event in self._list.get(0, tk.END):
            file.write(event + '\n')
        file.close()

    def _on_delete(self, event=None):
        selected_rows = list(map(int, self._list.curselection()))
        if len(selected_rows) != 1:
            return
        if not tkMessageBox.askyesno(APP_NAME, CONFIRM_DELETE_EVENT):
            return
        event_to_delete = self._event_from_row[selected_rows[0]]
        self._clear()
        self._observer.delete_event(event_to_delete)

    def _select_last_event(self):
        if self._list.size() == 0:
            return
        self._list.selection_clear(0, tk.END)
        self._list.selection_set(tk.END)
        self._list.see(tk.END)
        self._list.activate(tk.END)
        self._list.focus_set()

    def _clear(self):
        self._event_from_row = {}
        self._list.delete(0, tk.END)


class TeamStatsWidget(widget.StyledFrame):

    def __init__(self, root, team_id):
        self._team_id = team_id
        self._report = summary.TeamStats()
        widget.StyledFrame.__init__(self, root)

    def _create_widgets(self):
        self._title = ttk.Label(
            self._frame,
            font=TITLE_FONT,
            text=TEAM_REPORT_TITLE.format(self._team_id))
        self._header = ttk.Label(
            self._frame,
            font=REPORT_FONT,
            text=summary.TeamStats.header())
        self._stats = tk.Listbox(
            self._frame,
            activestyle=tk.DOTBOX,
            font=REPORT_FONT,
            selectmode=tk.BROWSE,
            height=15,
            width=len(self._report.header()))

    def _define_layout(self):
        self._title.grid(row=0, column=0, pady=(0, 10))
        self._header.grid(row=1, column=0, pady=(0, 5), stick=tk.W)
        self._stats.grid(row=2, column=0, stick=tk.NSEW)
        self._frame.grid_rowconfigure(2, weight=1)
        self._frame.grid_columnconfigure(0, weight=1)

    def _apply_style(self):
        widget.StyledFrame._apply_style(self)
        self._title['foreground'] = TITLE_COLOR
        self._stats['background'] = self._BACKGROUND_COLOR

    def set_font_size(self, size):
        self._header['font'] = (REPORT_FONT_NAME, size)
        self._stats['font'] = (REPORT_FONT_NAME, size)

    def update(self, match):
        self._stats.delete(0, tk.END)
        for row in self._report.render_team(self._team_id, match):
            self._stats.insert(tk.END, row)


class SuspensionsWidget(widget.StyledFrame):

    def __init__(self, root, team_id):
        self._team_id = team_id
        self._report = summary.Suspensions(GAME_PHASE_ABBREVIATIONS)
        self._prev_suspensions = None
        widget.StyledFrame.__init__(self, root)

    def _create_widgets(self):
        self._header = ttk.Label(
            self._frame,
            font=REPORT_FONT,
            text=summary.Suspensions.header())
        self._suspensions = tk.Listbox(
            self._frame,
            activestyle=tk.DOTBOX,
            font=REPORT_FONT,
            selectmode=tk.BROWSE,
            height=3)

    def _define_layout(self):
        self._header.grid(row=0, column=0, pady=(0, 5), stick=tk.W)
        self._suspensions.grid(row=1, column=0, stick=tk.NSEW)
        self._frame.grid_rowconfigure(1, weight=1)
        self._frame.grid_columnconfigure(0, weight=1)

    def _apply_style(self):
        widget.StyledFrame._apply_style(self)
        self._suspensions['background'] = self._BACKGROUND_COLOR

    def set_font_size(self, size):
        self._header['font'] = (REPORT_FONT_NAME, size)
        self._suspensions['font'] = (REPORT_FONT_NAME, size)

    def clear(self):
        self._prev_suspensions = []
        self._suspensions.delete(0, tk.END)

    def update(self, suspensions, config):
        team_suspensions = [
            s for s in suspensions if s.player.team_id == self._team_id]
        if self._prev_suspensions == team_suspensions:
            return
        self._prev_suspensions = team_suspensions
        self._suspensions.delete(0, tk.END)
        for row in self._report.render(team_suspensions, config):
            self._suspensions.insert(tk.END, row)


class SelectTeamDialog(widget.BaseDialog):

    def __init__(self, parent, title):
        widget.BaseDialog.__init__(self, parent, title)

    def body(self, master):
        self.team = ''
        ttk.Label(master, text=SELECT_TEAM_CODE) \
            .grid(row=0, column=0, columnspan=2, padx=5, pady=5)
        ttk.Button(master, text=A_TEAM_BUTTON_LABEL, command=self._on_a) \
            .grid(row=2, column=0, stick=tk.E, padx=20, pady=(20, 5))
        ttk.Button(master, text=B_TEAM_BUTTON_LABEL, command=self._on_b) \
            .grid(row=2, column=1, stick=tk.W, padx=20, pady=(20, 5))
        ttk.Separator(master, orient='horizontal') \
            .grid(row=3, column=0, columnspan=2, stick=tk.EW, pady=(20, 5))
        ttk.Button(master, text=CANCEL_BUTTON_LABEL, command=self.cancel) \
            .grid(row=4, column=1, stick=tk.E, padx=5, pady=(20, 5))
        if len(game.TEAM_A_ID) == 1:
            self.bind('<Key-{}>'.format(game.TEAM_A_ID.lower()), self._on_a)
        if len(game.TEAM_B_ID) == 1:
            self.bind('<Key-{}>'.format(game.TEAM_B_ID.lower()), self._on_b)
        self.bind('<Escape>', self.cancel)

    def _on_a(self, event=None):
        self.team = game.TEAM_A_ID
        self.ok()

    def _on_b(self, event=None):
        self.team = game.TEAM_B_ID
        self.ok()


class GameInconsistenciesDialog(widget.BaseDialog):

    def __init__(self, parent, title, message, inconsistencies):
        self._message = message
        self._inconsistencies = inconsistencies
        widget.BaseDialog.__init__(self, parent, title)

    def body(self, master):
        # create widgets
        listbox = tk.Listbox(
            master,
            activestyle=tk.DOTBOX,
            selectmode=tk.BROWSE,
            height=20,
            width=max([len(x) for x in self._inconsistencies]))
        scrollbar = tk.Scrollbar(master)
        # define layout
        ttk.Label(master, text=self._message).grid(
            row=0, column=0, columnspan=2, padx=5, pady=(20, 15), stick=tk.W)
        listbox.grid(
            row=1,
            column=0,
            columnspan=2,
            padx=(5, 0),
            pady=(0, 5),
            stick=tk.EW)
        scrollbar.grid(row=1, column=2, padx=(0, 5), pady=(0, 5), stick=tk.NS)
        ttk.Button(master, text=OK_BUTTON_LABEL, command=self.ok).grid(
            row=2, column=1, columnspan=2, stick=tk.E, padx=5, pady=5)
        # create bindings
        listbox['yscrollcommand'] = scrollbar.set
        scrollbar['command'] = listbox.yview
        self.bind('<Return>', self.ok)
        # load data
        for inconsistency in self._inconsistencies:
            listbox.insert(tk.END, inconsistency)


class Application(widget.StyledWidget):

    def __init__(self, root, title):
        self._root = root
        # hide the main window as soon as possible
        self._root.withdraw()
        self._title = title
        self._root.title(self._title)
        self._icon = tk.PhotoImage(file = 'report.gif')
        self._root.tk.call('wm', 'iconphoto', self._root._w, self._icon)
        # timers
        self._period_timer = chrono.Timer()
        self._timeout_timer_config = chrono.TimeViewConfig()
        self._timeout_timer_config.tenth_second_on_last_minute = False
        self._timeout_timer = chrono.Timer()
        self._timeout_timer.configure(self._timeout_timer_config)
        self._timeout_timer.set_period_duration(TIMEOUT_DURATION)
        # flags
        self._stop_time_during_penalties = tk.BooleanVar()
        self._stop_time_during_penalties.set(False)
        self._in_timeout = False
        # enable styling
        style = ttk.Style()
        style.configure('TButton', padding=10)
        style.configure('TCheckbutton', background=self._BACKGROUND_COLOR)
        style.map(
            'TCheckbutton', background=[('active', self._BACKGROUND_COLOR)])
        # initial configuration
        self._siren_on = False
        self._scoreboard = None
        self._config = AppConfig()
        self._config_file_path = os.path.expanduser(
            '~/.jolly-handball_report.cfg')
        self._config.load(self._config_file_path)
        self._change_config(True) # initial config
        if self._config.knock_out_game:
            course = game.KnockOutGameCourse(
                self._config.period_duration, EXTRA_PERIOD_DURATION)
        else:
            course = game.ChampionshipGameCourse(self._config.period_duration)
        self._match = game.Game(course, self._period_timer, GameObserver())
        self._config.match(self._match)
        # prepare the main window
        widget.StyledWidget.__init__(self, self._root)
        self._root.deiconify()
        self._set_initial_size()
        self._update()
        self._update_game_phase()
        self._update_progress_button_label()
        if self._match.is_live():
            self._enable_buttons()
        else:
            self._disable_buttons()

    def _create_widgets(self):
        # buttons
        self._progress_button = ttk.Button(
            self._root,
            width=max(len(l) for l in
                list(PROGRESS_BUTTON_START_LIVE_PHASE_LABELS.values()) +
                list(PROGRESS_BUTTON_STOP_LIVE_PHASE_LABELS.values())))
        self._goal_button = ttk.Button(
            self._root, text=GOAL_BUTTON_LABEL)
        self._timeout_button = ttk.Button(
            self._root, text=TIMEOUT_CALL_BUTTON_LABEL)
        self._warning_button = ttk.Button(
            self._root, text=WARNING_BUTTON_LABEL)
        self._suspension_button = ttk.Button(
            self._root, text=SUSPENSION_BUTTON_LABEL)
        self._dismiss_button = ttk.Button(
            self._root, text=DISMISS_BUTTON_LABEL)
        self._penalty_button = ttk.Button(
            self._root, text=PENALTY_BUTTON_LABEL)
        # time
        self._timer_widget = chrono.TimerWidget(
            self._root, self._period_timer, TIME_FONT)
        self._stop_time_during_penalties_button = ttk.Checkbutton(
            self._root,
            text=STOP_TIME_DURING_PENALTIES_CHECKBOX_LABEL,
            variable=self._stop_time_during_penalties)
        # game phase
        self._game_phase_widget = GamePhaseWidget(self._root, self._match)
        # game events
        self._event_list = EventListWidget(self._root, self)
        # team stats
        self._team_a_stats = TeamStatsWidget(self._root, game.TEAM_A_ID)
        self._team_b_stats = TeamStatsWidget(self._root, game.TEAM_B_ID)
        # suspensions
        self._suspension_reports_heading = tk.Label(
            self._root, font=TITLE_FONT, text=SUSPENSION_REPORTS_HEADING)
        self._team_a_suspensions = SuspensionsWidget(
            self._root, game.TEAM_A_ID)
        self._team_b_suspensions = SuspensionsWidget(
            self._root, game.TEAM_B_ID)
        # main window buttons
        self._siren_button = ttk.Button(self._root, text=SIREN_BUTTON_LABEL)
        self._config_button = ttk.Button(self._root, text=CONFIG_BUTTON_LABEL)
        self._quit_button = ttk.Button(self._root, text=QUIT_BUTTON_LABEL)

    def _define_layout(self):
        # buttons
        self._progress_button.grid(row=4, column=1, stick=tk.EW, padx=5)
        self._goal_button.grid(
            row=6, column=1, stick=tk.EW, padx=5, pady=(5, 0))
        self._timeout_button.grid(
            row=7, column=1, stick=tk.EW, padx=5, pady=(5, 0))
        self._warning_button.grid(
            row=8, column=1, stick=tk.EW, padx=5, pady=(5, 0))
        self._suspension_button.grid(
            row=9, column=1, stick=tk.EW, padx=5, pady=(5, 0))
        self._dismiss_button.grid(
            row=10, column=1, stick=tk.EW, padx=5, pady=(5, 0))
        self._penalty_button.grid(
            row=11, column=1, stick=tk.EW, padx=5, pady=(5, 0))
        # time
        self._timer_widget.grid(row=0, column=2)
        self._stop_time_during_penalties_button.grid(
            row=3, column=2, pady=(15, 5))
        # game phase
        self._game_phase_widget.grid(row=0, column=3, rowspan=4, columnspan=4)
        # game events
        self._event_list.grid(
            row=4,
            column=2,
            rowspan=10,
            stick=tk.NSEW,
            padx=5,
            pady=(20, 0))
        # team stats
        self._team_a_stats.grid(
            row=5, column=3, rowspan=7, stick=tk.NSEW, padx=5)
        self._team_b_stats.grid(
            row=5,
            column=4,
            rowspan=7,
            columnspan=3,
            stick=tk.NSEW,
            padx=5)
        # suspensions
        self._suspension_reports_heading.grid(
            row=12,
            column=3,
            columnspan=4,
            pady=(15, 0))
        self._team_a_suspensions.grid(
            row=13,
            column=3,
            stick=tk.NSEW,
            padx=(0, 5),
            pady=(5, 0))
        self._team_b_suspensions.grid(
            row=13,
            column=4,
            columnspan=3,
            stick=tk.NSEW,
            padx=(0, 5),
            pady=(5, 0))
        # main window buttons
        self._siren_button.grid(
            row=14, column=1, stick=tk.EW, padx=5, pady=5)
        self._config_button.grid(
            row=14, column=5, stick=tk.EW, padx=5, pady=5)
        self._quit_button.grid(
            row=14, column=6, stick=tk.EW, padx=(0, 5), pady=5)
        # main grid
        self._root.grid_rowconfigure(5, weight=5)
        self._root.grid_rowconfigure(13, weight=1)
        self._root.grid_columnconfigure(0, weight=1)
        self._root.grid_columnconfigure(4, minsize=72)
        self._root.grid_columnconfigure(7, weight=1)

    def _create_bindings(self):
        # actions
        self._goal_button['command'] = self._on_goal
        self._timeout_button['command'] = self._on_timeout
        self._warning_button['command'] = self._on_warning
        self._suspension_button['command'] = self._on_suspension
        self._dismiss_button['command'] = self._on_dismiss
        self._penalty_button['command'] = self._on_penalty
        self._progress_button['command'] = self._on_progress
        # main window buttons
        self._siren_button.bind('<Button-1>', self._on_siren_on)
        self._siren_button.bind('<ButtonRelease-1>', self._on_siren_off)
        self._config_button['command'] = self._on_config
        self._quit_button['command'] = self._on_quit
        # keyboard shortcuts
        self._root.bind(GOAL_KEY, self._on_goal)
        self._root.bind(TIMEOUT_KEY, self._on_timeout)
        self._root.bind(WARNING_KEY, self._on_warning)
        self._root.bind(SUSPENSION_KEY, self._on_suspension)
        self._root.bind(DISMISS_KEY, self._on_dismiss)
        self._root.bind(PENALTY_KEY, self._on_penalty)
        self._root.bind(PROGRESS_KEY, self._on_progress)
        # main window events
        self._root.protocol('WM_DELETE_WINDOW', self._on_delete_window)

    def _apply_style(self):
        widget.StyledWidget._apply_style(self)
        self._suspension_reports_heading['foreground'] = TITLE_COLOR
        self._suspension_reports_heading['background'] = self._BACKGROUND_COLOR

    def _create_event_list_configuration(self):
        event_list_config = self._config.clone()
        # force min/sec format
        event_list_config.tenth_second_on_last_minute = False
        return event_list_config

    def _change_config(self, is_initial_config):
        dialog = ConfigDialog(self._root, self._config, is_initial_config)
        self._config.save(self._config_file_path)
        # timer configuration
        if is_initial_config:
            self._period_timer.set_period_duration(self._config.period_duration)
        else:
            if self._config.show_timeout_time and self._in_timeout:
                self._timer_widget.change_timer(self._timeout_timer)
            else:
                self._timer_widget.change_timer(self._period_timer)
        self._period_timer.configure(self._config)
        # scoreboard configuration
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
        # report reload
        if not is_initial_config:
            self._event_list.reload(
                [event for event in self._match],
                self._create_event_list_configuration())
            self._reload_suspension_panels()

    def _set_initial_size(self):
        screen_width = self._root.winfo_screenwidth()
        screen_height = self._root.winfo_screenheight()
        report_font_size = MAX_REPORT_FONT_SIZE
        while report_font_size > MIN_REPORT_FONT_SIZE:
            self._event_list.set_font_size(report_font_size)
            self._team_a_stats.set_font_size(report_font_size)
            self._team_b_stats.set_font_size(report_font_size)
            self._team_a_suspensions.set_font_size(report_font_size)
            self._team_b_suspensions.set_font_size(report_font_size)
            self._root.update_idletasks()
            width = self._root.winfo_reqwidth()
            height = self._root.winfo_reqheight()
            if width < screen_width and height < screen_height:
                break
            report_font_size -= 1

    def _update(self):
        self._root.after(20, self._update)
        self._timer_widget.update()
        self._update_suspension_panels()
        if self._timeout_timer.is_triggered():
            self._timeout_expiring()
        elif self._timeout_timer.is_expired():
            self._timeout_expired()
        if self._scoreboard:
            _, _, tenth = self._period_timer.now()
            home_score, guest_score = self._match.score()
            if self._config.show_timeout_calls_on_scoreboard:
                team_a_timeouts = self._match.called_timeouts(game.TEAM_A_ID)
                team_b_timeouts = self._match.called_timeouts(game.TEAM_B_ID)
                home_first_timeout = (team_a_timeouts & 0x01) > 0
                home_second_timeout = (team_a_timeouts & 0x02) > 0
                guest_first_timeout = (team_b_timeouts & 0x01) > 0
                guest_second_timeout = (team_b_timeouts & 0x02) > 0
            else:
                home_first_timeout = False
                home_second_timeout = False
                guest_first_timeout = False
                guest_second_timeout = False

            self._scoreboard.update(
                scoreboard.Data(
                    timestamp=self._period_timer.figures(),
                    dot=tenth < 5,
                    leading_zero_in_minute = \
                        self._config.leading_zero_in_minute,
                    home_seventh_foul=False,
                    home_first_timeout=home_first_timeout,
                    home_second_timeout=home_second_timeout,
                    home_set=0,
                    home_score=home_score,
                    guest_seventh_foul=False,
                    guest_first_timeout=guest_first_timeout,
                    guest_second_timeout=guest_second_timeout,
                    guest_set=0,
                    guest_score=guest_score,
                    siren=self._siren_on))

    def _update_game_phase(self):
        self._game_phase_widget.show(
            GAME_PHASE_NAMES[self._match.current_phase().id])

    def _update_progress_button_label(self):
        if not self._match.is_ended():
            game_phase = self._match.current_phase()
            if game_phase.is_live:
                labels = PROGRESS_BUTTON_STOP_LIVE_PHASE_LABELS
            else:
                game_phase = self._match.next_phase()
                labels = PROGRESS_BUTTON_START_LIVE_PHASE_LABELS
            self._progress_button['text'] = labels[game_phase.id]
            self._enable(self._progress_button)
        else:
            self._disable(self._progress_button)

    def _reload_suspension_panels(self):
        self._team_a_suspensions.clear()
        self._team_b_suspensions.clear()
        self._update_suspension_panels()

    def _update_suspension_panels(self):
        now = self._match.timestamp()
        active_suspensions = [
            s for s in self._match.suspensions if not s.is_expired(now)]
        self._team_a_suspensions.update(active_suspensions, self._config)
        self._team_b_suspensions.update(active_suspensions, self._config)

    def _enable_buttons(self):
        self._set_buttons_state(tk.NORMAL)

    def _disable_buttons(self):
        self._set_buttons_state(tk.DISABLED)

    def _set_buttons_state(self, state):
        self._goal_button['state'] = state
        self._timeout_button['state'] = state
        self._warning_button['state'] = state
        self._suspension_button['state'] = state
        self._dismiss_button['state'] = state
        self._penalty_button['state'] = state

    @catch_exceptions
    def _on_goal(self, event=None):
        if self._is_disabled(self._goal_button):
            return
        timestamp = self._match.timestamp()
        player = self._ask_for_player(GOAL_BUTTON_LABEL)
        if player:
            self._log_event(self._match.player_scored(player, timestamp))

    @catch_exceptions
    def _on_timeout(self, event=None):
        if self._is_disabled(self._timeout_button):
            return
        if self._in_timeout:
            # timeout ended
            self._timeout_timer.stop()
            self._timer_widget.change_timer(self._period_timer)
            self._period_timer.start()
            self._game_phase_widget.restore()
            self._timeout_button['text'] = TIMEOUT_CALL_BUTTON_LABEL
            button_state = tk.NORMAL
        else:
            # timeout just called
            team = self._ask_for_team(TIMEOUT_CALL_BUTTON_LABEL)
            if not team:
                return
            timestamp = self._match.timestamp()
            event = self._match.timeout(team, timestamp)
            if not event:
                return
            self._log_event(event)
            self._period_timer.stop()
            if self._config.timeout_called_blast:
                self._activate_siren()
            self._timeout_timer.reset()
            self._timeout_timer.arm_trigger(0, 50)
            if self._config.show_timeout_time:
                self._timer_widget.change_timer(self._timeout_timer)
            self._timeout_timer.start()
            self._game_phase_widget.flash(TIMEOUT_LABEL)
            self._timeout_button['text'] = TIMEOUT_END_BUTTON_LABEL
            button_state = tk.DISABLED
        self._in_timeout = not self._in_timeout
        self._set_widget_state(self._goal_button, button_state)
        self._set_widget_state(self._warning_button, button_state)
        self._set_widget_state(self._suspension_button, button_state)
        self._set_widget_state(self._dismiss_button, button_state)
        self._set_widget_state(self._penalty_button, button_state)
        self._set_widget_state(self._progress_button, button_state)

    @catch_exceptions
    def _on_warning(self, event=None):
        if self._is_disabled(self._warning_button):
            return
        timestamp = self._match.timestamp()
        player = self._ask_for_player(WARNING_BUTTON_LABEL)
        if player:
            self._log_event(self._match.player_warned(player, timestamp))

    @catch_exceptions
    def _on_suspension(self, event=None):
        if self._is_disabled(self._suspension_button):
            return
        timestamp = self._match.timestamp()
        player = self._ask_for_player(SUSPENSION_BUTTON_LABEL)
        if player:
            self._log_event(self._match.player_suspended(player, timestamp))

    @catch_exceptions
    def _on_dismiss(self, event=None):
        if self._is_disabled(self._dismiss_button):
            return
        timestamp = self._match.timestamp()
        player = self._ask_for_player(DISMISS_BUTTON_LABEL)
        if player:
            self._log_event(self._match.player_dismissed(player, timestamp))

    @catch_exceptions
    def _on_penalty(self, event=None):
        if self._is_disabled(self._penalty_button):
            return
        timestamp = self._match.timestamp()
        time_was_running = self._period_timer.is_running()
        if self._stop_time_during_penalties.get():
            self._period_timer.stop()
        player = self._ask_for_player(PENALTY_BUTTON_LABEL)
        if player:
            if tkMessageBox.askyesno(APP_NAME, CONFIRM_PENALTY_SCORED):
                self._log_event(self._match.penalty_scored(player, timestamp))
            else:
                self._log_event(self._match.penalty_missed(player, timestamp))
        if self._stop_time_during_penalties.get() and time_was_running:
            self._period_timer.start()

    @catch_exceptions
    def _on_progress(self, event=None):
        if self._is_disabled(self._progress_button):
            return
        timestamp = self._match.timestamp()
        next_phase = self._match.next_phase()
        if next_phase.is_live:
            if self._period_timer.is_running():
                self._period_timer.stop()
            self._period_timer.reset()
            self._period_timer.set_period_duration(next_phase.duration)
            timestamp = self._match.timestamp()
            self._period_timer.start()
            self._enable_buttons()
        else:
            self._disable_buttons()
            if self._config.aggregate_time:
                self._period_timer.reset()
        self._log_event(self._match.phase_expired(timestamp))
        self._update_game_phase()
        self._update_progress_button_label()

    @catch_exceptions
    def delete_event(self, event):
        observer = DeleteEventObserver()
        self._match.delete_event(event.id, observer)
        for event in self._match:
            self._log_event(event)
        if self._match.current_phase().is_live:
            self._period_timer.start()
            self._enable_buttons()
        else:
            self._period_timer.stop()
            self._disable_buttons()
        self._update_game_phase()
        self._update_progress_button_label()
        self._update_team_stats()
        if observer.warnings:
            GameInconsistenciesDialog(
                self._root,
                GAME_INCONSISTENCIES_DIALOG_TITLE,
                GAME_INCONSISTENCIES_DIALOG_MESSAGE,
                observer.warnings)
            self._event_list.focus_set()

    def _on_siren_on(self, event=None):
        self._siren_on = True

    def _on_siren_off(self, event=None):
        self._siren_on = False

    def _on_config(self, event=None):
        self._change_config(False) # not the initial config

    def _on_quit(self, event=None):
        self._terminate()

    def _on_delete_window(self):
        self._terminate()

    def _terminate(self):
        if tkMessageBox.askyesno(APP_NAME, CONFIRM_QUIT):
            self._period_timer.stop()
            self._timeout_timer.stop()
            self._root.destroy()

    def _log_event(self, event):
        if not event:
            return
        self._event_list.append(event, self._config)
        self._update_team_stats()

    def _update_team_stats(self):
        self._team_a_stats.update(self._match)
        self._team_b_stats.update(self._match)

    def _ask_for_team(self, title):
        return SelectTeamDialog(self._root, title).team

    def _ask_for_player(self, title):
        team = self._ask_for_team(title)
        if not team:
            return
        player = InputNumberDialog(
            self._root, title, INPUT_PLAYER_NUMBER, '').value
        if not player:
            return ''
        return '{}{}'.format(team, player)

    def _period_expired(self, minute):
        if self._config.period_expired_blast:
            self._activate_siren()

    def _timeout_expiring(self):
        if self._config.timeout_expiring_blast:
            self._activate_siren()

    def _timeout_expired(self):
        self._timer_widget.change_timer(self._period_timer)

    def _activate_siren(self):
        self._root.after(0, self._on_siren_on)
        self._root.after(1000, self._on_siren_off)


root_ = tk.Tk()
app = Application(root_, '{} - v. {}'.format(APP_NAME, APP_VERSION))
root_.mainloop()
