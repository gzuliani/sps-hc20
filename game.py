#!/usr/bin/python
# -*- coding: utf8 -*-

import collections
import copy
import re
import unittest

# The term `game` refers to the structure of the sporting event, while `match`
# is the actual challenge (in other words, `match` is an instance of `game`).

# game course
class GamePhase(object):

    # game phases
    BEFORE_MATCH = 0
    FIRST_PERIOD = 1
    INTERVAL = 2
    SECOND_PERIOD = 3
    FIRST_EXTRA_PERIOD = 4
    SECOND_EXTRA_PERIOD = 5
    PENALTIES = 6
    AFTER_MATCH = 7

    def __init__(self, id, is_live):
        self.id = id
        self.is_live = is_live

    def can_be_suspended(self):
        return self.id in [self.FIRST_PERIOD, self.SECOND_PERIOD]


class LiveGamePhase(GamePhase):

    def __init__(self, id, duration):
        GamePhase.__init__(self, id, True)
        self.duration = duration


class Interval(GamePhase):

    def __init__(self, id):
        GamePhase.__init__(self, id, False)


class GameEnded(Exception):

    def __init__(self):
        Exception.__init__(self, 'game ended')


class GameCourse(object):

    def __init__(self, *args, **kwargs):
        self._phases = self._interleave_intervals(self._init(*args, **kwargs))
        for i, phase in enumerate(self._phases):
            phase.ordinal = i
        self._current_phase = 0

    def is_ended(self):
        return self._current_phase == len(self._phases) - 1

    def is_live(self):
        return self._phases[self._current_phase].is_live

    def current_phase(self):
        return self._phases[self._current_phase]

    def enter_next_phase(self, score):
        if self.is_ended():
            raise GameEnded()
        self._current_phase = self._next_phase(self._current_phase, score)

    def next_phase(self, score):
        return self._phases[self._next_phase(self._current_phase, score)]

    def next_scheduled_live_phase(self, current_phase):
        next_live_phases = [phase_ for phase_ in self
            if phase_.ordinal > current_phase.ordinal and phase_.is_live]
        return next_live_phases[0] if next_live_phases else None

    def _next_phase(self, current_phase, score):
        return current_phase + 1

    def _interleave_intervals(self, live_game_phases):
        intervals = [Interval(GamePhase.INTERVAL)] * len(live_game_phases)
        phase_interval_pairs = zip(live_game_phases, intervals)
        return \
            [ Interval(GamePhase.BEFORE_MATCH) ] \
            + [phase for pair in phase_interval_pairs for phase in pair][:-1] \
            + [ Interval(GamePhase.AFTER_MATCH) ]

    def __getitem__(self, index):
        if index < len(self._phases):
            return self._phases[index]
        else:
            raise IndexError


class ChampionshipGameCourse(GameCourse):

    def __init__(self, period_duration):
        GameCourse.__init__(self, period_duration)

    def _init(self, period_duration):
        return [
            LiveGamePhase(GamePhase.FIRST_PERIOD, period_duration),
            LiveGamePhase(GamePhase.SECOND_PERIOD, period_duration),
        ]


class KnockOutGameCourse(GameCourse):

    def __init__(self, period_duration, extra_period_duration):
        GameCourse.__init__(self, period_duration, extra_period_duration)

    def _init(self, period_duration, extra_period_duration):
        return [
            LiveGamePhase(GamePhase.FIRST_PERIOD, period_duration),
            LiveGamePhase(GamePhase.SECOND_PERIOD, period_duration),
            LiveGamePhase(GamePhase.FIRST_EXTRA_PERIOD, extra_period_duration),
            LiveGamePhase(GamePhase.SECOND_EXTRA_PERIOD, extra_period_duration),
            LiveGamePhase(GamePhase.PENALTIES, 0),
        ]

    def _next_phase(self, current_phase, score):
        if self._phases[current_phase].id == GamePhase.SECOND_PERIOD \
            or self._phases[current_phase].id == GamePhase.SECOND_EXTRA_PERIOD:
            if score[0] != score[1]:
                # game is over
                return len(self._phases) - 1
        return current_phase + 1


# teams
TEAM_A_ID = 'A'
TEAM_B_ID = 'B'


class Team(object):

    _MAX_TIMEOUTS_PER_MATCH = 3
    _MAX_TIMEOUTS_PER_PERIOD = 2

    def __init__(self, id):
        self.id = id
        self._called_timeouts = collections.defaultdict(int)

    def timeout(self, phase, observer):
        if not phase.can_be_suspended():
            if not observer.accept_unexpected_timeout(self, phase):
                return False
        period_timeouts = self._called_timeouts[phase]
        if period_timeouts >= self._MAX_TIMEOUTS_PER_PERIOD:
            if not observer.accept_additional_timeout_in_game_phase(
                    self, phase):
                return False
        total_timeouts = sum(self._called_timeouts.values())
        if total_timeouts >= self._MAX_TIMEOUTS_PER_MATCH:
            if not observer.accept_additional_timeout_in_game(self):
                return False
        self._called_timeouts[phase] += 1
        return True


# players
class InvalidPlayerCode(Exception):

    def __init__(self, code):
        Exception.__init__(self, 'invalid player code')
        self.code = code


class PlayerIsDismissed(Exception):

    def __init__(self, player):
        Exception.__init__(self, 'player dismissed')
        self.player = player


class PlayerAlreadyWarned(Exception):

    def __init__(self, player):
        Exception.__init__(self, 'player already warned')
        self.player = player


class Player(object):

    _ID = re.compile('^({}|{})\s*(\d+)$'.format(TEAM_A_ID, TEAM_B_ID))

    def __init__(self, code):
        result = self._ID.match(code)
        if not result:
            raise InvalidPlayerCode(code)
        self.team_id = result.group(1)
        self.number = int(result.group(2))
        self.goals = 0
        self.warned = False
        self.suspensions = 0
        self.dismissed = False

    def code(self):
        return self.team_id + str(self.number)

    def goal(self, observer):
        if self.dismissed:
            if not observer.accept_goal_by_dismissed_player(self):
                return False
        self.goals += 1
        return True

    def warning(self, observer):
        if self.dismissed:
            if not observer.accept_warning_for_dismissed_player(self):
                return False
        if self.warned:
            if not observer.accept_warning_for_warned_player(self):
                return False
        self.warned = True
        return True

    def suspension(self, observer):
        if self.dismissed:
            if not observer.accept_suspension_for_dismissed_player(self):
                return False
        self.suspensions += 1
        if self.suspensions == 3:
            self.dismiss(observer)
        return True

    def dismiss(self, observer):
        if self.dismissed:
            if not observer.accept_dismiss_for_dismissed_player(self):
                return False
        self.dismissed = True
        return True

    def _id(self):
        return (self.team_id, self.number)


# game events
GOAL_EVENT_CODE = ''
TIMEOUT_EVENT_CODE = 'TO'
PLAYER_WARNED_EVENT_CODE = 'AMM'
PLAYER_SUSPENDED_EVENT_CODE = '2M'
PLAYER_DISMISSED_EVENT_CODE = 'SQ'
PENALTY_SCORED_EVENT_CODE = '(R)'
PENALTY_MISSED_EVENT_CODE = 'R'


class GameEvent(object):

    def __init__(self, timestamp, code):
        self.timestamp = timestamp
        self.code = code


class PlayerEvent(GameEvent):

    def __init__(self, timestamp, code, player_code):
        GameEvent.__init__(self, timestamp, code)
        self.player_code = player_code


class PlayerScored(PlayerEvent):

    def __init__(self, timestamp, player_code):
        PlayerEvent.__init__(self, timestamp, GOAL_EVENT_CODE, player_code)

    def replay(self, match):
        match.player_scored(self.player_code, self.timestamp)


class Timeout(GameEvent):

    def __init__(self, timestamp, team_id):
        GameEvent.__init__(self, timestamp, TIMEOUT_EVENT_CODE)
        self.team_id = team_id

    def replay(self, match):
        match.timeout(self.team_id, self.timestamp)


class PlayerWarned(PlayerEvent):

    def __init__(self, timestamp, player_code):
        PlayerEvent.__init__(
            self, timestamp, PLAYER_WARNED_EVENT_CODE, player_code)

    def replay(self, match):
        match.player_warned(self.player_code, self.timestamp)


class PlayerSuspended(PlayerEvent):

    def __init__(self, timestamp, player_code):
        PlayerEvent.__init__(
            self, timestamp, PLAYER_SUSPENDED_EVENT_CODE, player_code)

    def replay(self, match):
        match.player_suspended(self.player_code, self.timestamp)


class PlayerDismissed(PlayerEvent):

    def __init__(self, timestamp, player_code):
        PlayerEvent.__init__(
            self, timestamp, PLAYER_DISMISSED_EVENT_CODE, player_code)

    def replay(self, match):
        match.player_dismissed(self.player_code, self.timestamp)


class PenaltyScored(PlayerEvent):

    def __init__(self, timestamp, player_code):
        PlayerEvent.__init__(
            self, timestamp, PENALTY_SCORED_EVENT_CODE, player_code)

    def replay(self, match):
        match.penalty_scored(self.player_code, self.timestamp)


class PenaltyMissed(PlayerEvent):

    def __init__(self, timestamp, player_code):
        PlayerEvent.__init__(
            self, timestamp, PENALTY_MISSED_EVENT_CODE, player_code)

    def replay(self, match):
        match.penalty_missed(self.player_code, self.timestamp)


class PhaseExpired(GameEvent):

    def __init__(self, timestamp, is_live):
        GameEvent.__init__(self, timestamp, '-')
        self.is_live = is_live

    def replay(self, match):
        match.phase_expired(self.timestamp)


class ExtraTimeoutInGamePhase(Exception):

    def __init__(self, team, phase):
        Exception.__init__(self, 'period timeouts already used')
        self.team = team
        self.phase = phase


class ExtraTimeoutInGame(Exception):

    def __init__(self, team):
        Exception.__init__(self, 'match timeouts already used')
        self.team = team


class UnexpectedTimeoutCall(Exception):

    def __init__(self, team, phase):
        Exception.__init__(self, 'timeout in extra time')
        self.team = team
        self.phase = phase


class GameInterrupted(Exception):

    def __init__(self):
        Exception.__init__(self, 'game suspended')


class ThrowingObserver(object):

    def accept_unexpected_timeout(self, team, phase):
        raise UnexpectedTimeoutCall(team, phase)

    def accept_additional_timeout_in_game_phase(self, team, phase):
        raise ExtraTimeoutInGamePhase(team, phase)

    def accept_additional_timeout_in_game(self, team):
        raise ExtraTimeoutInGame(team)

    def accept_goal_by_dismissed_player(self, player):
        raise PlayerIsDismissed(player)

    def accept_warning_for_dismissed_player(self, player):
        raise PlayerIsDismissed(player)

    def accept_warning_for_warned_player(self, player):
        raise PlayerAlreadyWarned(player)

    def accept_suspension_for_dismissed_player(self, player):
        raise PlayerIsDismissed(player)

    def accept_dismiss_for_dismissed_player(self, player):
        raise PlayerIsDismissed(player)

    def accept_event_during_non_live_phase(self):
        raise GameInterrupted()


class Timestamp(object):

    def __init__(self, phase, minute, second):
        self.phase = phase
        self.minute = minute
        self.second = second

    def __lt__(self, other):
        return self.phase.ordinal < other.phase.ordinal \
            or (self.phase.ordinal == other.phase.ordinal \
                and (self.minute < other.minute \
                    or (self.minute == other.minute \
                        and self.second < other.second)))


# suspensions
class Suspension(object):

    def __init__(self, player_code, start, expiration):
        self.player = Player(player_code)
        self.start = start
        self.expiration = expiration

    def is_expired(self, timestamp):
        return timestamp > self.expiration


class Suspensions(object):

    _SUSPENSION_DURATION = 2 # min

    def __init__(self, course):
        self._course = course
        self._suspensions = []

    def on_player_suspension(self, start, player):
        self._suspensions.append(
            Suspension(player, start, self._expiration_time(start)))

    def _expiration_time(self, start):
        expiring_minute = start.minute + self._SUSPENSION_DURATION
        curr_phase = start.phase
        phase_duration = curr_phase.duration
        if expiring_minute < phase_duration \
            or (expiring_minute == phase_duration and start.second == 0):
            return Timestamp(curr_phase, expiring_minute, start.second)
        else:
            next_phase = self._course.next_scheduled_live_phase(curr_phase)
            if next_phase:
                expiring_minute -= curr_phase.duration
                return Timestamp(next_phase, expiring_minute, start.second)
            else:
                return None

    def __len__(self):
        return len(self._suspensions)

    def __getitem__(self, index):
        if index < len(self._suspensions):
            return self._suspensions[index]
        else:
            raise IndexError


# game
class Game(object):

    def __init__(self, course, timer, observer=None):
        self._safe_copy_of_course = course
        self._timer = timer
        self._observer = observer if observer else ThrowingObserver()
        self._reset()

    def _reset(self):
        self._course = copy.copy(self._safe_copy_of_course)
        self._teams = dict([(id, Team(id)) for id in [TEAM_A_ID, TEAM_B_ID]])
        self._players = {}
        self._suspensions = Suspensions(self._course)
        self._events = [] # will contain (event, score) tuples

    def period_duration(self):
        for phase in self._course:
            if phase.id == GamePhase.FIRST_PERIOD:
                return phase.duration

    def extra_period_duration(self):
        for phase in self._course:
            if phase.id == GamePhase.FIRST_EXTRA_PERIOD:
                return phase.duration

    def score(self):
        return (
            self._score_for_team(TEAM_A_ID),
            self._score_for_team(TEAM_B_ID))

    def players(self, team_id):
        return self._players_in_team(team_id)

    @property
    def suspensions(self):
        return self._suspensions

    def _score_for_team(self, team_id):
        return sum([p.goals for p in self._players_in_team(team_id)])

    def _players_in_team(self, team_id):
        return [p for p in self._players.values() if p.team_id == team_id]

    def player_scored(self, player_code, timestamp=None):
        if self._assert_current_phase_is_live():
            if self._pick_player(player_code).goal(self._observer):
                return self._register_event(
                    PlayerScored(self._timestamp(timestamp), player_code))

    def timeout(self, team_id, timestamp=None):
        if self._assert_current_phase_is_live():
            if self._teams[team_id].timeout(
                    self.current_phase(), self._observer):
                return self._register_event(
                    Timeout(self._timestamp(timestamp), team_id))

    def player_warned(self, player_code, timestamp=None):
        if self._assert_current_phase_is_live():
            if self._pick_player(player_code).warning(self._observer):
                return self._register_event(
                    PlayerWarned(self._timestamp(timestamp), player_code))

    def player_suspended(self, player_code, timestamp=None):
        if self._assert_current_phase_is_live():
            if self._pick_player(player_code).suspension(self._observer):
                timestamp = self._timestamp(timestamp)
                self._suspensions.on_player_suspension(timestamp, player_code)
                return self._register_event(
                    PlayerSuspended(timestamp, player_code))

    def player_dismissed(self, player_code, timestamp=None):
        if self._assert_current_phase_is_live():
            if self._pick_player(player_code).dismiss(self._observer):
                return self._register_event(
                    PlayerDismissed(self._timestamp(timestamp), player_code))

    def penalty_scored(self, player_code, timestamp=None):
        if self._assert_current_phase_is_live():
            if self._pick_player(player_code).goal(self._observer):
                return self._register_event(
                    PenaltyScored(self._timestamp(timestamp), player_code))

    def penalty_missed(self, player_code, timestamp=None):
        if self._assert_current_phase_is_live():
            return self._register_event(
                PenaltyMissed(self._timestamp(timestamp), player_code))

    def phase_expired(self, timestamp=None):
        was_prior_phase_live = self.is_live()
        self._course.enter_next_phase(self.score())
        return self._register_event(
            PhaseExpired(self._timestamp(timestamp), was_prior_phase_live))

    def is_live(self):
        return self._course.is_live()

    def is_ended(self):
        return self._course.is_ended()

    def current_phase(self):
        return self._course.current_phase()

    def next_phase(self):
        return self._course.next_phase(self.score())

    def timestamp(self):
        minute, second, _ = self._timer.peek()
        return Timestamp(self.current_phase(), minute, second)

    def _timestamp(self, timestamp):
        return timestamp if timestamp else self.timestamp()

    # may change events' id
    def delete_event(self, event_id, observer=None):
        old_observer = self._observer
        if observer:
            self._observer = observer
        self._replay([e for e in self._events if e.id != event_id])
        self._observer = old_observer

    def __getitem__(self, index):
        if index < len(self._events):
            return self._events[index]
        else:
            raise IndexError

    def _register_event(self, event):
        event.id = len(self._events)
        event.score = self.score()
        self._events.append(event)
        self._events.sort(key=lambda e: e.timestamp)
        return event

    def _assert_current_phase_is_live(self):
        if not self._course.is_live():
            return self._observer.accept_event_during_non_live_phase()
        else:
            return True

    def _replay(self, events):
        self._reset()
        for e in events:
            e.replay(self)

    def _pick_player(self, player_code):
        if not player_code in self._players:
            self._players[player_code] = Player(player_code)
        return self._players[player_code]


class TestPlayer(unittest.TestCase):

    def setUp(self):
        self.observer = ThrowingObserver()

    def test_a_team_player(self):
        player = Player('A2')
        self.assertEqual(player.team_id, TEAM_A_ID)
        self.assertEqual(player.number, 2)

    def test_b_team_player(self):
        player = Player('B7')
        self.assertEqual(player.team_id, TEAM_B_ID)
        self.assertEqual(player.number, 7)

    def test_a_team_player_with_multidigit_number(self):
        player = Player('A99')
        self.assertEqual(player.team_id, TEAM_A_ID)
        self.assertEqual(player.number, 99)

    def test_reject_player_code_with_invalid_team_code(self):
        with self.assertRaises(InvalidPlayerCode) as _:
            player = Player('C7')
        with self.assertRaises(InvalidPlayerCode) as _:
            player = Player('12')
        with self.assertRaises(InvalidPlayerCode) as _:
            player = Player('AB3')
        with self.assertRaises(InvalidPlayerCode) as _:
            player = Player('?3')

    def test_reject_player_code_whit_invalid_player_number(self):
        with self.assertRaises(InvalidPlayerCode) as _:
            player = Player('A')
        with self.assertRaises(InvalidPlayerCode) as _:
            player = Player('ANN')
        with self.assertRaises(InvalidPlayerCode) as _:
            player = Player('A?')

    def test_player_initially_has_scored_no_goals(self):
        player = Player('A2')
        self.assertEqual(player.goals, 0)

    def test_player_with_one_goal_scored(self):
        player = Player('A2')
        player.goal(self.observer)
        self.assertEqual(player.goals, 1)

    def test_player_with_several_goals_scored(self):
        player = Player('A2')
        player.goal(self.observer)
        player.goal(self.observer)
        self.assertEqual(player.goals, 2)
        player.goal(self.observer)
        self.assertEqual(player.goals, 3)
        player.goal(self.observer)
        self.assertEqual(player.goals, 4)

    def test_player_initially_is_not_warned(self):
        player = Player('A2')
        self.assertEqual(player.warned, False)

    def test_player_can_be_warned(self):
        player = Player('A2')
        player.warning(self.observer)
        self.assertEqual(player.warned, True)

    def test_warned_player_cannot_be_warned_again(self):
        player = Player('A2')
        player.warning(self.observer)
        with self.assertRaises(PlayerAlreadyWarned) as _:
            player.warning(self.observer)

    def test_player_initially_has_never_been_suspended(self):
        player = Player('A2')
        self.assertEqual(player.suspensions, 0)

    def test_player_suspended_once(self):
        player = Player('A2')
        player.suspension(self.observer)
        self.assertEqual(player.suspensions, 1)

    def test_player_suspended_twice(self):
        player = Player('A2')
        player.suspension(self.observer)
        player.suspension(self.observer)
        self.assertEqual(player.suspensions, 2)

    def test_player_suspended_three_times_is_dismissed(self):
        player = Player('A2')
        player.suspension(self.observer)
        player.suspension(self.observer)
        self.assertEqual(player.dismissed, False)
        player.suspension(self.observer)
        self.assertEqual(player.suspensions, 3)
        self.assertEqual(player.dismissed, True)

    def test_player_initially_is_not_dismissed(self):
        player = Player('A2')
        self.assertEqual(player.dismissed, False)

    def test_player_can_be_dismissed(self):
        player = Player('A2')
        player.dismiss(self.observer)
        self.assertEqual(player.dismissed, True)

    def test_dismissed_players_cannot_score(self):
        player = Player('A2')
        player.dismiss(self.observer)
        with self.assertRaises(PlayerIsDismissed) as _:
            player.goal(self.observer)

    def test_dismissed_players_cannot_be_warned(self):
        player = Player('A2')
        player.dismiss(self.observer)
        with self.assertRaises(PlayerIsDismissed) as _:
            player.warning(self.observer)

    def test_dismissed_players_cannot_be_suspended(self):
        player = Player('A2')
        player.dismiss(self.observer)
        with self.assertRaises(PlayerIsDismissed) as _:
            player.suspension(self.observer)

    def test_dismissed_players_cannot_be_dismissed_again(self):
        player = Player('A2')
        player.dismiss(self.observer)
        with self.assertRaises(PlayerIsDismissed) as _:
            player.dismiss(self.observer)


class TestChampionshipGameCourse(unittest.TestCase):

    def setUp(self):
        self.score = (0, 0)

    def test_championship_game_phase_sequence(self):
        course = ChampionshipGameCourse(25)
        self.assertFalse(course.is_ended())
        phase = course.current_phase()
        self.assertEqual(phase.id, GamePhase.BEFORE_MATCH)
        self.assertFalse(phase.is_live)
        self.assertFalse(course.is_live())
        self.assertFalse(course.is_ended())
        course.enter_next_phase(self.score)
        phase = course.current_phase()
        self.assertEqual(phase.id, GamePhase.FIRST_PERIOD)
        self.assertEqual(phase.duration, 25)
        self.assertTrue(phase.is_live)
        self.assertTrue(course.is_live())
        self.assertFalse(course.is_ended())
        course.enter_next_phase(self.score)
        phase = course.current_phase()
        self.assertEqual(phase.id, GamePhase.INTERVAL)
        self.assertFalse(phase.is_live)
        self.assertFalse(course.is_live())
        self.assertFalse(course.is_ended())
        course.enter_next_phase(self.score)
        phase = course.current_phase()
        self.assertEqual(phase.id, GamePhase.SECOND_PERIOD)
        self.assertEqual(phase.duration, 25)
        self.assertTrue(phase.is_live)
        self.assertTrue(course.is_live())
        self.assertFalse(course.is_ended())
        course.enter_next_phase(self.score)
        phase = course.current_phase()
        self.assertEqual(phase.id, GamePhase.AFTER_MATCH)
        self.assertFalse(phase.is_live)
        self.assertFalse(course.is_live())
        self.assertTrue(course.is_ended())
        self.assertRaises(GameEnded, course.enter_next_phase, self.score)


class TestNullObserver(object):

    def accept_goal_by_dismissed_player(self, player):
        return True


class TestCountingObserver(object):

    def __init__(self):
        self.unexpected_timeouts = 0
        self.additional_period_timeouts = 0
        self.additional_match_timeouts = 0
        self.goal_from_dismissed_player = 0
        self.events_during_non_live_phase = 0

    def accept_unexpected_timeout(self, team, phase):
        self.unexpected_timeouts += 1
        return True

    def accept_additional_timeout_in_game_phase(self, team, phase):
        self.additional_period_timeouts += 1
        return True

    def accept_additional_timeout_in_game(self, team):
        self.additional_game_timeouts += 1
        return True

    def accept_goal_by_dismissed_player(self, player):
        self.goal_from_dismissed_player += 1
        return True

    def accept_event_during_non_live_phase(self):
        self.events_during_non_live_phase += 1
        return True


class TestTimer(object):

    def __init__(self):
        self._minute = 0
        self._second = 0

    def peek(self):
        return (self._minute, self._second, 0)

    def set(self, minute, second):
        self._minute = minute
        self._second = second


class TestGame(unittest.TestCase):

    def setUp(self):
        self.timer = TestTimer()
        self.match = Game(ChampionshipGameCourse(25), self.timer)

    def test_initial_score_is_null(self):
        self.assertEqual(self.match.score(), (0, 0))

    def test_game_accept_events_on_live_course_only(self):
        # match is not started yet!
        self.assertRaises(GameInterrupted, self.match.player_scored, 'A1')
        self.assertRaises(GameInterrupted, self.match.timeout, 'A')
        self.assertRaises(GameInterrupted, self.match.player_warned, 'A')
        self.assertRaises(GameInterrupted, self.match.player_suspended, 'A')
        self.assertRaises(GameInterrupted, self.match.player_dismissed, 'A')
        self.assertRaises(GameInterrupted, self.match.penalty_scored, 'A')
        self.assertRaises(GameInterrupted, self.match.penalty_missed, 'A')
        self.match.phase_expired() # entering first period
        self.match.player_scored('A1')
        self.match.phase_expired() # entering interval
        self.assertRaises(GameInterrupted,
            self.match.player_scored, 'A1')
        self.match.phase_expired() # entering second period
        self.match.player_scored('A1')
        self.match.phase_expired() # entering after match
        self.assertRaises(GameInterrupted, self.match.player_scored, 'A1')

    def test_game_traces_score(self):
        self.match.phase_expired() # entering first period
        self.match.player_scored('A1')
        self.assertEqual(self.match.score(), (1, 0))
        self.match.player_scored('A1')
        self.assertEqual(self.match.score(), (2, 0))
        self.match.player_scored('B1')
        self.assertEqual(self.match.score(), (2, 1))
        self.match.player_scored('A1')
        self.match.player_scored('A1')
        self.match.player_scored('B1')
        self.match.player_scored('A1')
        self.assertEqual(self.match.score(), (5, 2))

    def test_penalties_count_as_goals(self):
        self.match.phase_expired() # entering first period
        self.match.player_scored('A1')
        self.assertEqual(self.match.score(), (1, 0))
        self.match.penalty_scored('A1')
        self.assertEqual(self.match.score(), (2, 0))
        self.match.player_scored('B1')
        self.assertEqual(self.match.score(), (2, 1))
        self.match.penalty_scored('A1')
        self.match.player_scored('A1')
        self.match.penalty_scored('B1')
        self.match.player_scored('A1')
        self.assertEqual(self.match.score(), (5, 2))

    def test_events_other_than_goal_or_penalty_do_not_change_the_score(self):
        self.match.phase_expired() # entering first period
        self.match.player_warned('A1')
        self.assertEqual(self.match.score(), (0, 0))
        self.match.player_scored('A1')
        self.match.player_suspended('A1')
        self.assertEqual(self.match.score(), (1, 0))
        self.match.player_scored('A1')
        self.match.penalty_missed('B2')
        self.match.timeout('B')
        self.match.player_dismissed('B3')
        self.assertEqual(self.match.score(), (2, 0))
        self.match.player_scored('B2')
        self.assertEqual(self.match.score(), (2, 1))
        self.match.phase_expired() # entering interval
        self.match.phase_expired() # entering second period
        self.match.player_scored('A1')
        self.match.player_suspended('A1')
        self.match.player_scored('A1')
        self.match.penalty_missed('A1')
        self.match.timeout('A')
        self.match.player_warned('B2')
        self.match.player_suspended('B2')
        self.match.player_scored('B2')
        self.match.player_scored('A1')
        self.assertEqual(self.match.score(), (5, 2))

    def test_game_course(self):
        self.assertFalse(self.match.is_ended())
        phase = self.match.current_phase()
        self.assertEqual(phase.id, GamePhase.BEFORE_MATCH)
        self.assertFalse(self.match.is_live())
        self.assertFalse(self.match.is_ended())
        self.match.phase_expired() # entering first period
        phase = self.match.current_phase()
        self.assertEqual(phase.id, GamePhase.FIRST_PERIOD)
        self.assertTrue(self.match.is_live())
        self.assertFalse(self.match.is_ended())
        self.match.phase_expired() # entering interval
        phase = self.match.current_phase()
        self.assertEqual(phase.id, GamePhase.INTERVAL)
        self.assertFalse(self.match.is_live())
        self.assertFalse(self.match.is_ended())
        self.match.phase_expired() # entering second period
        phase = self.match.current_phase()
        self.assertEqual(phase.id, GamePhase.SECOND_PERIOD)
        self.assertTrue(self.match.is_live())
        self.assertFalse(self.match.is_ended())
        self.match.phase_expired() # entering after match
        phase = self.match.current_phase()
        self.assertEqual(phase.id, GamePhase.AFTER_MATCH)
        self.assertFalse(self.match.is_live())
        self.assertTrue(self.match.is_ended())
        self.assertRaises(GameEnded, self.match.phase_expired)

    def test_team_can_call_a_timeout_twice_in_the_first_period(self):
        self.match.phase_expired() # enter first period
        self.match.timeout('A')
        self.match.timeout('A')
        with self.assertRaises(ExtraTimeoutInGamePhase) as _:
            self.match.timeout('A')
        self.match.timeout('B')
        self.match.timeout('B')
        with self.assertRaises(ExtraTimeoutInGamePhase) as _:
            self.match.timeout('B')

    def test_team_can_call_a_timeout_twice_in_the_second_period(self):
        self.match.phase_expired() # enter first period
        self.match.phase_expired() # entering interval
        self.match.phase_expired() # entering second period
        self.match.timeout('A')
        self.match.timeout('A')
        with self.assertRaises(ExtraTimeoutInGamePhase) as _:
            self.match.timeout('A')
        self.match.timeout('B')
        self.match.timeout('B')
        with self.assertRaises(ExtraTimeoutInGamePhase) as _:
            self.match.timeout('B')

    def test_team_can_call_at_most_three_timeouts_in_a_game(self):
        self.match.phase_expired() # enter first period
        self.match.timeout('A')
        self.match.timeout('B')
        self.match.phase_expired() # entering interval
        self.match.phase_expired() # entering second period
        self.match.timeout('A')
        self.match.timeout('A')
        self.match.timeout('B')
        self.match.timeout('B')

    def test_team_cannot_call_more_than_three_timeouts_in_a_game(self):
        self.match.phase_expired() # enter first period
        self.match.timeout('A')
        self.match.timeout('A')
        self.match.timeout('B')
        self.match.timeout('B')
        self.match.phase_expired() # entering interval
        self.match.phase_expired() # entering second period
        self.match.timeout('A')
        with self.assertRaises(ExtraTimeoutInGame) as _:
            self.match.timeout('A')
        self.match.timeout('B')
        with self.assertRaises(ExtraTimeoutInGame) as _:
            self.match.timeout('B')

    def test_team_cannot_call_a_timeout_during_extra_times(self):
        match = Game(KnockOutGameCourse(25, 5), self.timer)
        match.phase_expired() # enter first period
        match.phase_expired() # entering interval
        match.phase_expired() # entering second period
        match.phase_expired() # entering interval
        match.phase_expired() # enter first extra period
        with self.assertRaises(UnexpectedTimeoutCall) as _:
            match.timeout('A')
        with self.assertRaises(UnexpectedTimeoutCall) as _:
            match.timeout('B')
        match.phase_expired() # entering interval
        match.phase_expired() # enter second extra period
        with self.assertRaises(UnexpectedTimeoutCall) as _:
            match.timeout('A')
        with self.assertRaises(UnexpectedTimeoutCall) as _:
            match.timeout('B')

    def test_game_traces_players(self):
        self.match.phase_expired() # enter first period
        self.assertEqual(len(self.match.players('A')), 0)
        self.assertEqual(len(self.match.players('B')), 0)
        self.match.player_suspended('B2')
        self.match.player_warned('A1')
        self.match.player_scored('A2')
        self.match.player_suspended('A2')
        self.match.player_scored('B2')
        self.match.timeout('A')
        self.match.player_suspended('A2')
        self.match.player_scored('A3')
        self.match.player_suspended('B2')
        self.match.player_scored('B4')
        self.match.phase_expired() # entering interval
        self.match.phase_expired() # entering second period
        self.match.player_suspended('A3')
        self.match.player_scored('B2')
        self.match.player_dismissed('B1')
        self.match.player_scored('B4')
        self.match.timeout('B')
        self.match.player_scored('B3')
        self.match.timeout('A')
        self.match.player_scored('B2')
        self.match.player_scored('A2')
        self.match.player_warned('B4')
        self.match.player_warned('A2')
        self.match.player_scored('B2')
        self.match.player_suspended('B2')

        team_a = self.match.players('A')
        team_a.sort(key=lambda p: p.number)

        self.assertEqual(len(team_a), 3)
        player_a1 = team_a[0]
        self.assertEqual(player_a1.code(), 'A1')
        self.assertEqual(player_a1.goals, 0)
        self.assertEqual(player_a1.warned, True)
        self.assertEqual(player_a1.suspensions, 0)
        self.assertEqual(player_a1.dismissed, False)
        player_a2 = team_a[1]
        self.assertEqual(player_a2.code(), 'A2')
        self.assertEqual(player_a2.goals, 2)
        self.assertEqual(player_a2.warned, True)
        self.assertEqual(player_a2.suspensions, 2)
        self.assertEqual(player_a2.dismissed, False)
        player_a3 = team_a[2]
        self.assertEqual(player_a3.code(), 'A3')
        self.assertEqual(player_a3.goals, 1)
        self.assertEqual(player_a3.warned, False)
        self.assertEqual(player_a3.suspensions, 1)
        self.assertEqual(player_a3.dismissed, False)

        team_b = self.match.players('B')
        team_b.sort(key=lambda p: p.number)

        self.assertEqual(len(team_b), 4)
        player_b1 = team_b[0]
        self.assertEqual(player_b1.code(), 'B1')
        self.assertEqual(player_b1.goals, 0)
        self.assertEqual(player_b1.warned, False)
        self.assertEqual(player_b1.suspensions, 0)
        self.assertEqual(player_b1.dismissed, True)
        player_b2 = team_b[1]
        self.assertEqual(player_b2.code(), 'B2')
        self.assertEqual(player_b2.goals, 4)
        self.assertEqual(player_b2.warned, False)
        self.assertEqual(player_b2.suspensions, 3)
        self.assertEqual(player_b2.dismissed, True)
        player_b3 = team_b[2]
        self.assertEqual(player_b3.code(), 'B3')
        self.assertEqual(player_b3.goals, 1)
        self.assertEqual(player_b3.warned, False)
        self.assertEqual(player_b3.suspensions, 0)
        self.assertEqual(player_b3.dismissed, False)
        player_b4 = team_b[3]
        self.assertEqual(player_b4.code(), 'B4')
        self.assertEqual(player_b4.goals, 2)
        self.assertEqual(player_b4.warned, True)
        self.assertEqual(player_b4.suspensions, 0)
        self.assertEqual(player_b4.dismissed, False)

    def test_game_events_are_sorted_by_increasing_phase_and_time(self):
        self.timer.set(0, 0)
        self.match.phase_expired(self.match.timestamp()) # entering first period
        self.timer.set(7, 12)
        self.match.player_scored('A1')
        self.timer.set(2, 59)
        self.match.player_warned('A2')
        self.timer.set(14, 6)
        self.match.penalty_missed('A3')
        self.timer.set(0, 43)
        self.match.player_suspended('A4')
        self.timer.set(25, 0)
        self.match.phase_expired() # entering interval
        self.timer.set(0, 0)
        self.match.phase_expired() # entering second period
        self.timer.set(10, 23)
        self.match.player_warned('A5')
        self.timer.set(1, 50)
        self.match.timeout('A')
        self.timer.set(8, 35)
        self.match.penalty_scored('A6')
        self.timer.set(25, 0)
        self.match.phase_expired() # entering after match

        events = [e for e in self.match]
        self.assertEqual(len(events), 11)
        self.assertEqual(type(events[ 0]), PhaseExpired)
        self.assertEqual(type(events[ 1]), PlayerSuspended)
        self.assertEqual(type(events[ 2]), PlayerWarned)
        self.assertEqual(type(events[ 3]), PlayerScored)
        self.assertEqual(type(events[ 4]), PenaltyMissed)
        self.assertEqual(type(events[ 5]), PhaseExpired)
        self.assertEqual(type(events[ 7]), Timeout)
        self.assertEqual(type(events[ 8]), PenaltyScored)
        self.assertEqual(type(events[ 9]), PlayerWarned)
        self.assertEqual(type(events[10]), PhaseExpired)

        self.assertEqual(events[ 0].id, 0)
        self.assertEqual(events[ 1].id, 4)
        self.assertEqual(events[ 2].id, 2)
        self.assertEqual(events[ 3].id, 1)
        self.assertEqual(events[ 4].id, 3)
        self.assertEqual(events[ 5].id, 5)
        self.assertEqual(events[ 6].id, 6)
        self.assertEqual(events[ 7].id, 8)
        self.assertEqual(events[ 8].id, 9)
        self.assertEqual(events[ 9].id, 7)
        self.assertEqual(events[10].id, 10)

    def test_game_events_can_be_deleted(self):
        self.match.phase_expired() # entering first period
        self.match.player_scored('A1')
        self.match.player_scored('A2')
        self.match.player_warned('B1')
        self.match.player_scored('B1')
        self.match.penalty_scored('A2')
        self.match.player_warned('A2')
        self.match.player_suspended('A2')
        self.match.player_dismissed('B1')
        self.match.player_scored('B2')
        self.match.timeout('B')
        self.match.phase_expired() # entering interval
        self.match.phase_expired() # entering second period
        self.match.penalty_missed('A1')
        self.match.penalty_scored('A2')
        self.match.player_scored('A1')

        self.assertEqual(self.match.score(), (5, 2))

        team_a = self.match.players('A')
        team_a.sort(key=lambda p: p.number)

        self.assertEqual(len(team_a), 2)
        player_a1 = team_a[0]
        self.assertEqual(player_a1.code(), 'A1')
        self.assertEqual(player_a1.goals, 2)
        self.assertEqual(player_a1.warned, False)
        self.assertEqual(player_a1.suspensions, 0)
        self.assertEqual(player_a1.dismissed, False)
        player_a2 = team_a[1]
        self.assertEqual(player_a2.code(), 'A2')
        self.assertEqual(player_a2.goals, 3)
        self.assertEqual(player_a2.warned, True)
        self.assertEqual(player_a2.suspensions, 1)
        self.assertEqual(player_a2.dismissed, False)

        team_b = self.match.players('B')
        team_b.sort(key=lambda p: p.number)

        self.assertEqual(len(team_b), 2)
        player_b1 = team_b[0]
        self.assertEqual(player_b1.code(), 'B1')
        self.assertEqual(player_b1.goals, 1)
        self.assertEqual(player_b1.warned, True)
        self.assertEqual(player_b1.suspensions, 0)
        self.assertEqual(player_b1.dismissed, True)
        player_b2 = team_b[1]
        self.assertEqual(player_b2.code(), 'B2')
        self.assertEqual(player_b2.goals, 1)
        self.assertEqual(player_b2.warned, False)
        self.assertEqual(player_b2.suspensions, 0)
        self.assertEqual(player_b2.dismissed, False)

        self.match.delete_event(7) # player_suspended 'A2'
        self.match.delete_event(8) # player_scored 'B2'
        self.match.delete_event(12) # penalty_scored 'A2'

        self.assertEqual(self.match.score(), (4, 1))

        team_a = self.match.players('A')
        self.assertEqual(len(team_a), 2)
        player_a1 = team_a[0]
        self.assertEqual(player_a1.code(), 'A1')
        self.assertEqual(player_a1.goals, 2)
        self.assertEqual(player_a1.warned, False)
        self.assertEqual(player_a1.suspensions, 0)
        self.assertEqual(player_a1.dismissed, False)
        player_a2 = team_a[1]
        self.assertEqual(player_a2.code(), 'A2')
        self.assertEqual(player_a2.goals, 2)
        self.assertEqual(player_a2.warned, True)
        self.assertEqual(player_a2.suspensions, 0)
        self.assertEqual(player_a2.dismissed, False)

        team_b = self.match.players('B')
        self.assertEqual(len(team_b), 1)
        player_b1 = team_b[0]
        self.assertEqual(player_b1.code(), 'B1')
        self.assertEqual(player_b1.goals, 1)
        self.assertEqual(player_b1.warned, True)
        self.assertEqual(player_b1.suspensions, 0)
        self.assertEqual(player_b1.dismissed, True)

    def test_deleting_game_events_can_cause_inconsistencies(self):
        observer = TestCountingObserver()
        match = Game(ChampionshipGameCourse(25), self.timer, observer)
        self.assertEqual(observer.additional_period_timeouts, 0)
        self.assertEqual(observer.goal_from_dismissed_player, 0)
        self.assertEqual(observer.events_during_non_live_phase, 0)

        match.phase_expired() # entering first period
        match.timeout('A')
        match.player_dismissed('A1')
        match.player_scored('A1') # prior inconsistency
        match.timeout('A')
        match.phase_expired() # entering interval
        match.phase_expired() # entering second period
        match.timeout('A')

        self.assertEqual(observer.additional_period_timeouts, 0)
        self.assertEqual(observer.goal_from_dismissed_player, 1)
        self.assertEqual(observer.events_during_non_live_phase, 0)

        match.delete_event(6) # entering second period

        self.assertEqual(observer.additional_period_timeouts, 0)
        self.assertEqual(observer.goal_from_dismissed_player, 2)
        self.assertEqual(observer.events_during_non_live_phase, 1)

        match.delete_event(5) # entering interval

        self.assertEqual(observer.additional_period_timeouts, 1)
        self.assertEqual(observer.goal_from_dismissed_player, 3)
        self.assertEqual(observer.events_during_non_live_phase, 1)

    def test_deleting_game_events_with_custom_observer(self):
        match = Game(ChampionshipGameCourse(25), self.timer, TestNullObserver())

        match.phase_expired() # entering first period
        match.timeout('A')
        match.player_dismissed('A1')
        match.player_scored('A1') # prior inconsistency
        match.timeout('A')
        match.phase_expired() # entering interval
        match.phase_expired() # entering second period
        match.timeout('A')

        observer = TestCountingObserver()
        match.delete_event(6, observer) # entering second period

        self.assertEqual(observer.additional_period_timeouts, 0)
        self.assertEqual(observer.goal_from_dismissed_player, 1)
        self.assertEqual(observer.events_during_non_live_phase, 1)

        match.delete_event(5, observer) # entering interval

        self.assertEqual(observer.additional_period_timeouts, 1)
        self.assertEqual(observer.goal_from_dismissed_player, 2)
        self.assertEqual(observer.events_during_non_live_phase, 1)


    def test_knockout_game_end_with_penalties(self):
        match = Game(KnockOutGameCourse(25, 5), self.timer)
        self.assertEqual(match.current_phase().id, GamePhase.BEFORE_MATCH)
        match.phase_expired()
        self.assertEqual(match.current_phase().id, GamePhase.FIRST_PERIOD)
        match.player_scored('A1')
        match.player_scored('B1')
        match.player_scored('A2')
        match.phase_expired()
        self.assertEqual(match.current_phase().id, GamePhase.INTERVAL)
        match.phase_expired()
        self.assertEqual(match.current_phase().id,GamePhase.SECOND_PERIOD)
        match.penalty_scored('B2')
        match.phase_expired()
        self.assertEqual(match.current_phase().id, GamePhase.INTERVAL)
        match.phase_expired()
        self.assertEqual(
            match.current_phase().id, GamePhase.FIRST_EXTRA_PERIOD)
        match.player_scored('B3')
        match.phase_expired()
        self.assertEqual(match.current_phase().id, GamePhase.INTERVAL)
        match.phase_expired()
        self.assertEqual(
            match.current_phase().id, GamePhase.SECOND_EXTRA_PERIOD)
        match.penalty_scored('A3')
        match.phase_expired()
        self.assertEqual(match.current_phase().id, GamePhase.INTERVAL)
        match.phase_expired()
        self.assertEqual(match.current_phase().id, GamePhase.PENALTIES)
        match.penalty_scored('A4')
        match.penalty_missed('B4')
        match.phase_expired()
        self.assertEqual(match.current_phase().id, GamePhase.AFTER_MATCH)

    def test_knockout_game_end_at_extra_times(self):
        match = Game(KnockOutGameCourse(25, 5), self.timer)
        self.assertEqual(match.current_phase().id, GamePhase.BEFORE_MATCH)
        match.phase_expired()
        self.assertEqual(match.current_phase().id, GamePhase.FIRST_PERIOD)
        match.player_scored('A1')
        match.player_scored('B1')
        match.player_scored('A2')
        match.phase_expired()
        self.assertEqual(match.current_phase().id, GamePhase.INTERVAL)
        match.phase_expired()
        self.assertEqual(match.current_phase().id, GamePhase.SECOND_PERIOD)
        match.penalty_scored('B2')
        match.phase_expired()
        self.assertEqual(match.current_phase().id, GamePhase.INTERVAL)
        match.phase_expired()
        self.assertEqual(
            match.current_phase().id, GamePhase.FIRST_EXTRA_PERIOD)
        match.player_scored('B3')
        match.phase_expired()
        self.assertEqual(match.current_phase().id, GamePhase.INTERVAL)
        match.phase_expired()
        self.assertEqual(
            match.current_phase().id, GamePhase.SECOND_EXTRA_PERIOD)
        match.penalty_scored('A3')
        match.player_scored('B4')
        match.phase_expired()
        self.assertEqual(match.current_phase().id, GamePhase.AFTER_MATCH)

    def test_knockout_game_end_on_regular_times(self):
        match = Game(KnockOutGameCourse(25, 5), self.timer)
        self.assertEqual(match.current_phase().id, GamePhase.BEFORE_MATCH)
        match.phase_expired()
        self.assertEqual(match.current_phase().id, GamePhase.FIRST_PERIOD)
        match.player_scored('A1')
        match.player_scored('B1')
        match.player_scored('A2')
        match.phase_expired()
        self.assertEqual(match.current_phase().id, GamePhase.INTERVAL)
        match.phase_expired()
        self.assertEqual(match.current_phase().id, GamePhase.SECOND_PERIOD)
        match.penalty_scored('B2')
        match.penalty_scored('B2')
        match.phase_expired()
        self.assertEqual(match.current_phase().id, GamePhase.AFTER_MATCH)


class TestSuspensions(unittest.TestCase):

    def setUp(self):
        self.timer = TestTimer()
        self.match = Game(ChampionshipGameCourse(25), self.timer)

    def test_game_without_suspensions(self):
        self.assertEqual(len(self.match.suspensions), 0)
        self.match.phase_expired((0, 0)) # entering first half
        self.assertEqual(len(self.match.suspensions), 0)
        self.match.phase_expired((25, 0)) # entering interval
        self.assertEqual(len(self.match.suspensions), 0)
        self.match.phase_expired((0, 0)) # entering second period
        self.assertEqual(len(self.match.suspensions), 0)
        self.match.phase_expired((25, 0)) # entering after match
        self.assertEqual(len(self.match.suspensions), 0)

    def test_suspension_in_the_first_period(self):
        self.timer.set(0, 0)
        self.match.phase_expired() # entering first period
        self.timer.set(12, 34)
        self.match.player_suspended('A1')
        self.assertEqual(len(self.match.suspensions), 1)
        suspension = self.match.suspensions[0]
        self.assertEqual(suspension.player.team_id, 'A')
        self.assertEqual(suspension.player.number, 1)
        self.assertEqual(
            suspension.expiration.phase.id, GamePhase.FIRST_PERIOD)
        self.assertEqual(suspension.start.minute, 12)
        self.assertEqual(suspension.start.second, 34)
        self.assertEqual(
            suspension.expiration.phase.id, GamePhase.FIRST_PERIOD)
        self.assertEqual(suspension.expiration.minute, 14)
        self.assertEqual(suspension.expiration.second, 34)

    def test_suspension_at_the_very_end_of_the_first_period(self):
        self.timer.set(0, 0)
        self.match.phase_expired() # entering first period
        self.timer.set(23, 0)
        self.match.player_suspended('A1')
        self.assertEqual(len(self.match.suspensions), 1)
        suspension = self.match.suspensions[0]
        self.assertEqual(
            suspension.expiration.phase.id, GamePhase.FIRST_PERIOD)
        self.assertEqual(suspension.expiration.minute, 25)
        self.assertEqual(suspension.expiration.second, 0)

    def test_suspension_overlapping_the_first_two_periods(self):
        self.timer.set(0, 0)
        self.match.phase_expired() # entering first period
        self.timer.set(23, 1)
        self.match.player_suspended('A1')
        self.assertEqual(len(self.match.suspensions), 1)
        suspension = self.match.suspensions[0]
        self.assertEqual(
            suspension.expiration.phase.id, GamePhase.SECOND_PERIOD)
        self.assertEqual(suspension.expiration.minute, 0)
        self.assertEqual(suspension.expiration.second, 1)

    def test_suspension_that_expires_past_the_end_of_the_game(self):
        self.timer.set(0, 0)
        self.match.phase_expired() # entering first period
        self.match.phase_expired() # entering interval
        self.match.phase_expired() # entering second period
        self.timer.set(23, 1)
        self.match.player_suspended('A1')
        self.assertEqual(len(self.match.suspensions), 1)
        suspension = self.match.suspensions[0]
        self.assertEqual(suspension.expiration, None)

    def test_suspension_at_the_very_end_of_the_second_period(self):
        match = Game(KnockOutGameCourse(25, 5), self.timer)
        self.timer.set(0, 0)
        match.phase_expired() # entering first period
        match.phase_expired() # entering interval
        match.phase_expired() # entering second period
        self.timer.set(23, 1)
        match.player_suspended('A1')
        self.assertEqual(len(match.suspensions), 1)
        suspension = match.suspensions[0]
        self.assertEqual(
            suspension.expiration.phase.id, GamePhase.FIRST_EXTRA_PERIOD)
        self.assertEqual(suspension.expiration.minute, 0)
        self.assertEqual(suspension.expiration.second, 1)

    def test_game_with_several_suspensions(self):
        self.timer.set(0, 0)
        self.match.phase_expired() # entering first period
        self.timer.set(7, 43)
        self.match.player_suspended('A1')
        self.timer.set(16, 12)
        self.match.player_suspended('B1')
        self.timer.set(24, 52)
        self.match.player_suspended('A2')
        self.timer.set(0, 0)
        self.match.phase_expired() # entering interval
        self.timer.set(0, 0)
        self.match.phase_expired() # entering second period
        self.timer.set(9, 38)
        self.match.player_suspended('B2')
        self.timer.set(23, 1)
        self.match.player_suspended('A1')
        self.assertEqual(len(self.match.suspensions), 5)
        suspension = self.match.suspensions[0]
        self.assertEqual(
            suspension.expiration.phase.id, GamePhase.FIRST_PERIOD)
        self.assertEqual(suspension.expiration.minute, 9)
        self.assertEqual(suspension.expiration.second, 43)
        suspension = self.match.suspensions[1]
        self.assertEqual(
            suspension.expiration.phase.id, GamePhase.FIRST_PERIOD)
        self.assertEqual(suspension.expiration.minute, 18)
        self.assertEqual(suspension.expiration.second, 12)
        suspension = self.match.suspensions[2]
        self.assertEqual(
            suspension.expiration.phase.id, GamePhase.SECOND_PERIOD)
        self.assertEqual(suspension.expiration.minute, 1)
        self.assertEqual(suspension.expiration.second, 52)
        suspension = self.match.suspensions[3]
        self.assertEqual(
            suspension.expiration.phase.id, GamePhase.SECOND_PERIOD)
        self.assertEqual(suspension.expiration.minute, 11)
        self.assertEqual(suspension.expiration.second, 38)
        suspension = self.match.suspensions[4]
        self.assertEqual(suspension.expiration, None)

    def test_suspensions_support_event_deletion(self):
        self.timer.set(0, 0)
        self.match.phase_expired() # entering first period
        self.timer.set(7, 43)
        self.match.player_suspended('A1')
        self.timer.set(16, 12)
        self.match.player_suspended('B1')
        self.timer.set(24, 52)
        self.match.player_suspended('A2')
        self.timer.set(0, 0)
        self.match.phase_expired() # entering interval
        self.match.phase_expired() # entering second period
        self.timer.set(9, 38)
        self.match.player_suspended('B2')
        self.timer.set(23, 1)
        self.match.player_suspended('A1')

        self.match.delete_event(2)

        self.assertEqual(len(self.match.suspensions), 4)
        suspension = self.match.suspensions[0]
        self.assertEqual(
            suspension.expiration.phase.id, GamePhase.FIRST_PERIOD)
        self.assertEqual(suspension.expiration.minute, 9)
        self.assertEqual(suspension.expiration.second, 43)
        suspension = self.match.suspensions[1]
        self.assertEqual(
            suspension.expiration.phase.id, GamePhase.SECOND_PERIOD)
        self.assertEqual(suspension.expiration.minute, 1)
        self.assertEqual(suspension.expiration.second, 52)
        suspension = self.match.suspensions[2]
        self.assertEqual(
            suspension.expiration.phase.id, GamePhase.SECOND_PERIOD)
        self.assertEqual(suspension.expiration.minute, 11)
        self.assertEqual(suspension.expiration.second, 38)
        suspension = self.match.suspensions[3]
        self.assertEqual(suspension.expiration, None)

    def test_is_expired_predicate(self):
        match = Game(KnockOutGameCourse(25, 5), self.timer)
        self.timer.set(0, 0)
        match.phase_expired() # entering first period
        self.timer.set(20, 15)
        pre_suspension_timestamp_1 = match.timestamp()
        self.timer.set(0, 0)
        match.phase_expired() # entering interval
        match.phase_expired() # entering second period
        self.timer.set(12, 33)
        pre_suspension_timestamp_2 = match.timestamp()
        self.timer.set(12, 34)
        match.player_suspended('A1')
        in_suspension_timestamp_1 = match.timestamp()
        self.timer.set(13, 46)
        in_suspension_timestamp_2 = match.timestamp()
        self.timer.set(14, 34)
        in_suspension_timestamp_3 = match.timestamp()
        self.timer.set(14, 35)
        post_suspension_timestamp_1 = match.timestamp()
        self.timer.set(0, 0)
        match.phase_expired() # entering interval
        match.phase_expired() # entering first extra period
        self.timer.set(1, 23)
        post_suspension_timestamp_2 = match.timestamp()
        self.timer.set(0, 0)
        match.phase_expired() # entering interval
        match.phase_expired() # entering second extra period
        self.timer.set(4, 56)
        post_suspension_timestamp_3 = match.timestamp()

        self.assertTrue(len(match.suspensions), 1)
        suspension = match.suspensions[0]
        self.assertFalse(suspension.is_expired(pre_suspension_timestamp_1))
        self.assertFalse(suspension.is_expired(pre_suspension_timestamp_2))
        self.assertFalse(suspension.is_expired(in_suspension_timestamp_1))
        self.assertFalse(suspension.is_expired(in_suspension_timestamp_2))
        self.assertFalse(suspension.is_expired(in_suspension_timestamp_3))
        self.assertTrue(suspension.is_expired(post_suspension_timestamp_1))
        self.assertTrue(suspension.is_expired(post_suspension_timestamp_2))
        self.assertTrue(suspension.is_expired(post_suspension_timestamp_3))


if __name__ == '__main__':
    unittest.main()
