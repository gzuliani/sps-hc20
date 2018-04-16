import serial
import time

class Data(object):

    def __init__(
        self,
        timestamp=(0, 0),
        dot=False,
        leading_zero_in_minute=False,
        home_seventh_foul=False,
        home_first_timeout=False,
        home_second_timeout=False,
        home_set=0,
        home_score=0,
        guest_seventh_foul=False,
        guest_first_timeout=False,
        guest_second_timeout=False,
        guest_set=0,
        guest_score=0,
        siren=False):
        self.home_seventh_foul = home_seventh_foul
        self.home_first_timeout = home_first_timeout
        self.home_second_timeout = home_second_timeout
        self.home_set = home_set
        self.home_score = home_score
        self.timestamp = timestamp
        self.dot = dot
        self.leading_zero_in_minute = leading_zero_in_minute
        self.guest_seventh_foul = guest_seventh_foul
        self.guest_first_timeout = guest_first_timeout
        self.guest_second_timeout = guest_second_timeout
        self.guest_score = guest_score
        self.guest_set = guest_set
        self.siren = siren

    def __eq__(self, other):
        return other and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other


class Font(object):

    _FONT = [
        #
        # the most significant bit, which controls the display's dot, is always
        # off because it controls the siren; the characters that should have it
        # on are: ! % . ?
        #
        #      .gfedcba
        int('0b00000000', 2), # <empty space>
        int('0b00000110', 2), # !
        int('0b00100010', 2), # "
        int('0b01111110', 2), # #
        int('0b01101101', 2), # $
        int('0b01010010', 2), # %
        int('0b01000110', 2), # &
        int('0b00100000', 2), # '
        int('0b00101001', 2), # (
        int('0b00001011', 2), # )
        int('0b00100001', 2), # *
        int('0b01110000', 2), # +
        int('0b00010000', 2), # ,
        int('0b01000000', 2), # -
        int('0b00000000', 2), # .
        int('0b01010010', 2), # /
        int('0b00111111', 2), # 0
        int('0b00000110', 2), # 1
        int('0b01011011', 2), # 2
        int('0b01001111', 2), # 3
        int('0b01100110', 2), # 4
        int('0b01101101', 2), # 5
        int('0b01111101', 2), # 6
        int('0b00000111', 2), # 7
        int('0b01111111', 2), # 8
        int('0b01101111', 2), # 9
        int('0b00001001', 2), # :
        int('0b00001101', 2), # ;
        int('0b01100001', 2), # <
        int('0b01001000', 2), # =
        int('0b01000011', 2), # >
        int('0b01010011', 2), # ?
        int('0b01011111', 2), # @
        int('0b01110111', 2), # A
        int('0b01111111', 2), # B
        int('0b00111001', 2), # C
        int('0b00011111', 2), # D
        int('0b01111001', 2), # E
        int('0b01110001', 2), # F
        int('0b00111101', 2), # G
        int('0b01110110', 2), # H
        int('0b00110000', 2), # I
        int('0b00011110', 2), # J
        int('0b01111010', 2), # K
        int('0b00111000', 2), # L
        int('0b00010101', 2), # M
        int('0b00110111', 2), # N
        int('0b00111111', 2), # O
        int('0b01110011', 2), # P
        int('0b01101011', 2), # Q
        int('0b00110011', 2), # R
        int('0b01101101', 2), # S
        int('0b00000111', 2), # T
        int('0b00111110', 2), # U
        int('0b01110010', 2), # V
        int('0b01111110', 2), # W
        int('0b01100100', 2), # X
        int('0b01101110', 2), # Y
        int('0b01011011', 2), # Z
        int('0b00111001', 2), # [
        int('0b01100100', 2), # \
        int('0b00001111', 2), # ]
        int('0b00100011', 2), # ^
        int('0b00001000', 2), # _
        int('0b00000010', 2), # `
        int('0b01011111', 2), # a
        int('0b01111100', 2), # b
        int('0b01011000', 2), # c
        int('0b01011110', 2), # d
        int('0b01111011', 2), # e
        int('0b01110001', 2), # f
        int('0b01101111', 2), # g
        int('0b01110100', 2), # h
        int('0b00010000', 2), # i
        int('0b00001100', 2), # j
        int('0b01110101', 2), # k
        int('0b00110000', 2), # l
        int('0b00010100', 2), # m
        int('0b01010100', 2), # n
        int('0b01011100', 2), # o
        int('0b01110011', 2), # p
        int('0b01100111', 2), # q
        int('0b01010000', 2), # r
        int('0b01101101', 2), # s
        int('0b01111000', 2), # t
        int('0b00011100', 2), # u
        int('0b01100010', 2), # v
        int('0b00101010', 2), # w
        int('0b01010010', 2), # x
        int('0b01101110', 2), # y
        int('0b01011011', 2), # z
        int('0b01000110', 2), # {
        int('0b00110000', 2), # |
        int('0b01110000', 2), # }
        int('0b00000001', 2), # ~
    ]

    _BLANK = _FONT[0]

    def encode(self, text):
        if len(text) == 1:
            return self._encode(text[0])
        else:
            return bytearray(''.join([self._encode(i) for i in text]))

    def _encode(self, character):
        code = ord(character)
        return chr(self._FONT[code - 32]) if 31 < code < 128 else self._BLANK


class ScrollingText(object):

    _DISPLAYS = [5, 6, 7, 8] # clock displays

    def __init__(self):
        self._font = Font()
        self._is_active = False
        self._window_length = len(self._DISPLAYS)
        self._padding = ' ' * self._window_length
        self._last_transform_time = 0

    def show(self, text, delay):
        self._text = self._font.encode('{0}{1}{0}'.format(self._padding, text))
        self._delay = delay
        self._window_pos = 0
        self._is_active = True

    def hide(self):
        self._is_active = False

    # Scoreboard's filter callback
    def transform(self, packet):
        if not self._is_active:
            return
        for i, display in enumerate(self._DISPLAYS):
            packet[display] = self._text[self._window_pos + i]
        current_millis = self._millis()
        if current_millis - self._last_transform_time > self._delay:
            self._window_pos += 1
            if len(self._text) - self._window_pos < self._window_length:
                self._window_pos = 0
            self._last_transform_time = current_millis

    def _millis(self):
        return int(round(time.time() * 1000))


class Scoreboard(object):

    _BAUDRATE = 57600
    _BYTESIZE = 8
    _PARITY = serial.PARITY_NONE
    _STOPBITS = serial.STOPBITS_ONE
    _TIMEOUT = 0.05 # 5ms

    _STX = 0x02
    _ETX = 0x03
    _ACK = 0x06
    _NAK = 0x15
    _DATA_LENGTH = 12

    def __init__(self, device_name):
        self._device_name = device_name
        self._scrolling_text = ScrollingText()
        self.nacks = 0
        self.errors = 0
        self.timeouts = 0
        self._font = Font()
        self._blank = self._font.encode(' ')
        self._digits = [self._font.encode(i) for i in '0123456789']
        self._port = serial.Serial(
            port=self._device_name,
            baudrate=self._BAUDRATE,
            bytesize=self._BYTESIZE,
            parity=self._PARITY,
            stopbits=self._STOPBITS,
            timeout=self._TIMEOUT)
        self._last_transmitted_data = None
        self._last_transmitted_packet = bytearray(
            [self._STX] + [self._blank] * self._DATA_LENGTH + [self._ETX])
        self._data = Data()

    @property
    def device_name(self):
        return self._device_name

    def show_scrolling_text(self, text, delay):
        self._scrolling_text.show(text, delay)

    def hide_scrolling_text(self):
        self._scrolling_text.hide()

    def update(self, data):
        if not self._last_transmitted_data \
            or self._last_transmitted_data != data:
            minute, second = data.timestamp
            buffer = self._last_transmitted_packet
            # set digits
            buffer[ 1] = self._encode_digit(self._units(data.home_set))
            buffer[ 2] = self._encode_digit(
                min(1, self._hundreds(data.home_score)))
            buffer[ 3] = self._encode_digit(self._tens(data.home_score))
            buffer[ 4] = self._encode_digit(self._units(data.home_score))
            tens_minute = self._tens(minute)
            if data.leading_zero_in_minute:
                tens_minute = max(0, tens_minute)
            buffer[ 5] = self._encode_digit(tens_minute)
            buffer[ 6] = self._encode_digit(self._units(minute))
            buffer[ 7] = self._encode_digit(max(0, self._tens(second)))
            buffer[ 8] = self._encode_digit(self._units(second))
            buffer[ 9] = self._encode_digit(
                min(1, self._hundreds(data.guest_score)))
            buffer[10] = self._encode_digit(self._tens(data.guest_score))
            buffer[11] = self._encode_digit(self._units(data.guest_score))
            buffer[12] = self._encode_digit(self._units(data.guest_set))
            # set other indicators
            buffer[2] = buffer[2] \
                | (0x40 if data.home_seventh_foul else 0x00) \
                | (0x20 if data.home_first_timeout else 0x00) \
                | (0x10 if data.home_second_timeout else 0x00)
            buffer[5] = buffer[5] | (0x80 if data.siren else 0x00)
            buffer[6] = buffer[6] | (0x80 if data.dot else 0x00)
            buffer[9] = buffer[9] \
                | (0x40 if data.guest_first_timeout else 0x00) \
                | (0x20 if data.guest_second_timeout else 0x00) \
                | (0x10 if data.guest_seventh_foul else 0x00)
        packet_to_transmit = self._last_transmitted_packet[:]
        self._scrolling_text.transform(packet_to_transmit)
        #~ print ' '.join(['{:02x}'.format(x) for x in packet_to_transmit])
        self._port.write(packet_to_transmit)
        response = self._port.read()
        if not response:
            self.timeouts += 1
        elif ord(response) == self._ACK:
            self._last_transmitted_data = data
        elif ord(response) == self._NAK:
            self.nacks += 1
        else:
            self.errors += 1

    def _units(self, value):
        return value % 10

    def _tens(self, value):
        return -1 if value < 10 else (value / 10) % 10

    def _hundreds(self, value):
        return -1 if value < 100 else (value / 100) % 10

    def _encode_digit(self, value):
        return self._blank if value < 0 or value > 9 else self._digits[value]
