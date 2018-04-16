#!/usr/bin/python
# -*- coding: utf8 -*-

import unittest

import game
import chrono


def render_timestamp(timestamp, config):
    config.period_duration = timestamp.phase.duration
    return chrono.TimeView(config).render(timestamp.minute, timestamp.second)


class EventList(object):

    _HEAD = "   # MIN/SEC  A    B   EVENTO     "
    _EVENT = ' {: >3d}  {}  {:^3s}  {:^3s}  {:<3s} {:02d}:{:02d}  '

    @classmethod
    def header(cls):
        return cls._HEAD

    def render_event(self, event, config):
        score_a, score_b = event.score
        if type(event) == game.PhaseExpired:
            return '/' * len(self._HEAD)
        else:
            if type(event) == game.Timeout:
                team = event.team_id
                subject = event.code
            else:
                player = game.Player(event.player_code)
                team = player.team_id
                subject = str(player.number)
            return self._EVENT.format(
                event.id,
                render_timestamp(event.timestamp, config),
                subject if team == game.TEAM_A_ID else '',
                subject if team == game.TEAM_B_ID else '',
                event.code,
                score_a,
                score_b)

    def render_game(self, match, config):
        return [self.render_event(event, config) for event in match]


class TeamStats(object):

    _HEAD = "  N   A   S S S   SQ  RETI "
    _PLAYER = ' {:>2d}   {}   {} {} {}    {}   {}  '

    @classmethod
    def header(cls):
        return cls._HEAD

    def render_team(self, team_id, match):
        player_list = match.players(team_id)
        player_list.sort(key = lambda p: p.number)
        return [self._render_player(p) for p in player_list]

    def _render_player(self, player):
        return self._PLAYER.format(
            player.number,
            'X' if player.warned else ' ',
            'X' if player.suspensions > 0 else ' ',
            'X' if player.suspensions > 1 else ' ',
            'X' if player.suspensions > 2 else ' ',
            'X' if player.dismissed else ' ',
            '{:>2d}'.format(player.goals) if player.goals > 0 else '  ')


class Suspensions(object):

    _HEAD = "  N   TERMINE"
    _SUSPENSION = ' {:>2d}   {} {}'

    @classmethod
    def header(cls):
        return cls._HEAD

    def __init__(self, game_phase_names):
        self._game_phase_names = game_phase_names

    def render(self, suspensions, config):
        return [self._render(s, config) for s in suspensions]

    def _render(self, suspension, config):
        return self._SUSPENSION.format(
            suspension.player.number,
            render_timestamp(suspension.expiration, config),
            self._game_phase_names[suspension.expiration.phase.id])


class TestEventList(unittest.TestCase):

    def test_report_default(self):
        self.assertEqual(EventList().render_game(
            match, chrono.TimeViewConfig()), [
            '//////////////////////////////////',
            '   1   0:15   1            01:00  ',
            '   2   0:47  12            02:00  ',
            '   3   1:04        9   2M  02:00  ',
            '   4   1:58        3       02:01  ',
            '   5   3:35   6        AMM 02:01  ',
            '   6   5:41   6        R   02:01  ',
            '   7   6:12        8       02:02  ',
            '   8   7:41   3            03:02  ',
            '   9   9:05   2            04:02  ',
            '  10  11:05  TO        TO  04:02  ',
            '  11  12:59       10   SQ  04:02  ',
            '  12  14:23       TO   TO  04:02  ',
            '  13  16:15   5            05:02  ',
            '  14  17:59        9       05:03  ',
            '  15  19:14        9   (R) 05:04  ',
            '  16  21:31        9   2M  05:04  ',
            '  17  21:40  11        (R) 06:04  ',
            '  18  23:34        9   R   06:04  ',
            '//////////////////////////////////',
            '//////////////////////////////////',
            '  21   2:18        9   2M  06:04  ',
            '  22   3:06   3        AMM 06:04  ',
            '  23   4:17   4            07:04  ',
            '  24   5:11   4        R   07:04  ',
            '  25   6:52        6       07:05  ',
            '  26   8:18        6       07:06  ',
            '  27   9:29       TO   TO  07:06  ',
            '  28  10:02        7       07:07  ',
            '  29  10:39   9        AMM 07:07  ',
            '  30  13:08   3        2M  07:07  ',
            '  31  15:10  TO        TO  07:07  ',
            '  32  15:18   2        AMM 07:07  ',
            '  33  16:06        7       07:08  ',
            '  34  18:43        7       07:09  ',
            '  35  20:20        7   R   07:09  ',
            '  36  22:36   2            08:09  ',
            '  37  23:15   5            09:09  ',
            '  38  24:10   7            10:09  ',
            '//////////////////////////////////',
        ])

    def test_report_leading_zero(self):
        self.assertEqual(EventList().render_game(
            match, chrono.TimeViewConfig(leading_zero_in_minute=True)), [
            '//////////////////////////////////',
            '   1  00:15   1            01:00  ',
            '   2  00:47  12            02:00  ',
            '   3  01:04        9   2M  02:00  ',
            '   4  01:58        3       02:01  ',
            '   5  03:35   6        AMM 02:01  ',
            '   6  05:41   6        R   02:01  ',
            '   7  06:12        8       02:02  ',
            '   8  07:41   3            03:02  ',
            '   9  09:05   2            04:02  ',
            '  10  11:05  TO        TO  04:02  ',
            '  11  12:59       10   SQ  04:02  ',
            '  12  14:23       TO   TO  04:02  ',
            '  13  16:15   5            05:02  ',
            '  14  17:59        9       05:03  ',
            '  15  19:14        9   (R) 05:04  ',
            '  16  21:31        9   2M  05:04  ',
            '  17  21:40  11        (R) 06:04  ',
            '  18  23:34        9   R   06:04  ',
            '//////////////////////////////////',
            '//////////////////////////////////',
            '  21  02:18        9   2M  06:04  ',
            '  22  03:06   3        AMM 06:04  ',
            '  23  04:17   4            07:04  ',
            '  24  05:11   4        R   07:04  ',
            '  25  06:52        6       07:05  ',
            '  26  08:18        6       07:06  ',
            '  27  09:29       TO   TO  07:06  ',
            '  28  10:02        7       07:07  ',
            '  29  10:39   9        AMM 07:07  ',
            '  30  13:08   3        2M  07:07  ',
            '  31  15:10  TO        TO  07:07  ',
            '  32  15:18   2        AMM 07:07  ',
            '  33  16:06        7       07:08  ',
            '  34  18:43        7       07:09  ',
            '  35  20:20        7   R   07:09  ',
            '  36  22:36   2            08:09  ',
            '  37  23:15   5            09:09  ',
            '  38  24:10   7            10:09  ',
            '//////////////////////////////////',
        ])

    def test_report_countdown(self):
        self.assertEqual(EventList().render_game(
            match, chrono.TimeViewConfig(countdown=True)), [
            '//////////////////////////////////',
            '   1  24:45   1            01:00  ',
            '   2  24:13  12            02:00  ',
            '   3  23:56        9   2M  02:00  ',
            '   4  23:02        3       02:01  ',
            '   5  21:25   6        AMM 02:01  ',
            '   6  19:19   6        R   02:01  ',
            '   7  18:48        8       02:02  ',
            '   8  17:19   3            03:02  ',
            '   9  15:55   2            04:02  ',
            '  10  13:55  TO        TO  04:02  ',
            '  11  12:01       10   SQ  04:02  ',
            '  12  10:37       TO   TO  04:02  ',
            '  13   8:45   5            05:02  ',
            '  14   7:01        9       05:03  ',
            '  15   5:46        9   (R) 05:04  ',
            '  16   3:29        9   2M  05:04  ',
            '  17   3:20  11        (R) 06:04  ',
            '  18   1:26        9   R   06:04  ',
            '//////////////////////////////////',
            '//////////////////////////////////',
            '  21  22:42        9   2M  06:04  ',
            '  22  21:54   3        AMM 06:04  ',
            '  23  20:43   4            07:04  ',
            '  24  19:49   4        R   07:04  ',
            '  25  18:08        6       07:05  ',
            '  26  16:42        6       07:06  ',
            '  27  15:31       TO   TO  07:06  ',
            '  28  14:58        7       07:07  ',
            '  29  14:21   9        AMM 07:07  ',
            '  30  11:52   3        2M  07:07  ',
            '  31   9:50  TO        TO  07:07  ',
            '  32   9:42   2        AMM 07:07  ',
            '  33   8:54        7       07:08  ',
            '  34   6:17        7       07:09  ',
            '  35   4:40        7   R   07:09  ',
            '  36   2:24   2            08:09  ',
            '  37   1:45   5            09:09  ',
            '  38   0:50   7            10:09  ',
            '//////////////////////////////////',
        ])

class TestTeamStats(unittest.TestCase):

    def test_a_team_stats(self):
        report = TeamStats()
        self.assertEqual(report.render_team('A', match), [
            '  1                     1  ',
            '  2   X                 2  ',
            '  3   X   X             1  ',
            '  4                     1  ',
            '  5                     2  ',
            '  6   X                    ',
            '  7                     1  ',
            '  9   X                    ',
            ' 11                     1  ',
            ' 12                     1  '])
        self.assertEqual(report.render_team('B', match), [
            '  3                     1  ',
            '  6                     2  ',
            '  7                     3  ',
            '  8                     1  ',
            '  9       X X X    X    2  ',
            ' 10                X       '])


class TestTimer(object):

    def __init__(self):
        self._minute = 0
        self._second = 0

    def peek(self):
        return self._minute, self._second, 0

    def set(self, minute, second):
        self._minute = minute
        self._second = second


if __name__ == '__main__':
    timer = TestTimer()
    match = game.Game(game.ChampionshipGameCourse(25), timer)
    timer.set(0, 0)
    match.phase_expired() # entering first half
    timer.set(0, 15)
    match.player_scored('A1')
    timer.set(0, 47)
    match.player_scored('A12')
    timer.set(1, 4)
    match.player_suspended('B9')
    timer.set(1, 58)
    match.player_scored('B3')
    timer.set(3, 35)
    match.player_warned('A6')
    timer.set(5, 41)
    match.penalty_missed('A6')
    timer.set(6, 12)
    match.player_scored('B8')
    timer.set(7, 41)
    match.player_scored('A3')
    timer.set(9, 5)
    match.player_scored('A2')
    timer.set(11, 5)
    match.timeout('A')
    timer.set(12, 59)
    match.player_dismissed('B10')
    timer.set(14, 23)
    match.timeout('B')
    timer.set(16, 15)
    match.player_scored('A5')
    timer.set(17, 59)
    match.player_scored('B9')
    timer.set(19, 14)
    match.penalty_scored('B9')
    timer.set(21, 31)
    match.player_suspended('B9')
    timer.set(21, 40)
    match.penalty_scored('A11')
    timer.set(23, 34)
    match.penalty_missed('B9')
    timer.set(25, 0)
    match.phase_expired() # entering interval
    timer.set(0, 0)
    match.phase_expired() # entering second period
    timer.set(2, 18)
    match.player_suspended('B9')
    timer.set(3, 6)
    match.player_warned('A3')
    timer.set(4, 17)
    match.player_scored('A4')
    timer.set(5, 11)
    match.penalty_missed('A4')
    timer.set(6, 52)
    match.player_scored('B6')
    timer.set(8, 18)
    match.player_scored('B6')
    timer.set(9, 29)
    match.timeout('B')
    timer.set(10, 2)
    match.player_scored('B7')
    timer.set(10, 39)
    match.player_warned('A9')
    timer.set(13, 8)
    match.player_suspended('A3')
    timer.set(15, 10)
    match.timeout('A')
    timer.set(15, 18)
    match.player_warned('A2')
    timer.set(16, 6)
    match.player_scored('B7')
    timer.set(18, 43)
    match.player_scored('B7')
    timer.set(20, 20)
    match.penalty_missed('B7')
    timer.set(22, 36)
    match.player_scored('A2')
    timer.set(23, 15)
    match.player_scored('A5')
    timer.set(24, 10)
    match.player_scored('A7')
    timer.set(25, 0)
    match.phase_expired() # entering after match

    unittest.main()
