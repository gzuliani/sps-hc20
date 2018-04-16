import serial

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


class Scoreboard(object):

    _BAUDRATE = 57600
    _BYTESIZE = 8
    _PARITY = serial.PARITY_NONE
    _STOPBITS = serial.STOPBITS_ONE
    _TIMEOUT = 0.05 # 5ms

    _BLANK = int('0b00000000', 2) # empty space

    _DIGITS = [
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
    ]

    _STX = 0x02
    _ETX = 0x03
    _ACK = 0x06
    _NAK = 0x15
    _DATA_LENGTH = 12

    def __init__(self, device_name):
        self._device_name = device_name
        self.nacks = 0
        self.errors = 0
        self.timeouts = 0
        self._port = serial.Serial(
            port=self._device_name,
            baudrate=self._BAUDRATE,
            bytesize=self._BYTESIZE,
            parity=self._PARITY,
            stopbits=self._STOPBITS,
            timeout=self._TIMEOUT)
        self._last_transmitted_data = None
        self._last_transmitted_packet = bytearray(
            [self._STX] + [self._BLANK] * self._DATA_LENGTH + [self._ETX])
        self._data = Data()

    @property
    def device_name(self):
        return self._device_name

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
        self._port.write(self._last_transmitted_packet)
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
        return self._BLANK if value < 0 or value > 9 else self._DIGITS[value]
