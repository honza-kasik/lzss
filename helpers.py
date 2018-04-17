import sys
import contextlib

class Reference():
    """Just a wrapper - no data validation"""

    def __init__(self, position: int, length: int):
        self._position = position
        self._length = length

    def get_length(self) -> int:
        return self._length

    def get_pos(self) -> int:
        return self._position

    def get_bits(self) -> int:
        # 12 bits for position = max pos is 4096
        # 4 bits for length = max match size is 16
        return self._position << 4 | self._length

    @staticmethod
    def from_bytes(bytes: bytes):
        assert len(bytes) == 2
        position = (bytes[0] << 4) | (bytes[1] & ~0b1111)
        length   = bytes[1] & 0b1111
        return Reference(position, length)

    def __str__(self):
        return "reference: {0}, {1}".format(self._position, self._length)

class CircularBuffer():

    def __init__(self, max_buffer_size: int):
        self._buffer = []
        self._max_buffer_size = max_buffer_size
        self._buffer_size = 0

    def put_byte(self, byte: int):
        self._buffer.append(byte)
        self._buffer_size += 1
        if (self._buffer_size > self._max_buffer_size):
            self._buffer.pop(0)

    def get_byte_at(self, pos: int) -> int:
        return self._buffer[pos]

    def get_match(self, start_pos: int, length: int) -> [int]:
        return self._buffer[start_pos : start_pos + length]

    def get_fill(self) -> int:
        return len(self._buffer)

    def get_longest_match(self, max_allowable_match_length: int, buffer) -> Reference:
        # walk it
        longest_match_length = 0
        longest_match_pos = -1
        for i in range(0, self.get_fill()):
            j = 0
            while(i + j < self.get_fill() and # is there still some symbols left to compare with?
                j < buffer.get_fill() and
                buffer.get_byte_at(j) == self.get_byte_at(i + j)): # if there are, check another
                j += 1
            if (j > longest_match_length):
                longest_match_length = j
                longest_match_pos = i
        return Reference(longest_match_pos, longest_match_length)

    def __str__(self):
        return str(self._buffer)

    def pop(self):
        """remove first element and return it"""
        return self._buffer.pop(0)


class SmartOpener():
    #https://stackoverflow.com/a/17603000

    @staticmethod
    @contextlib.contextmanager
    def smart_write(filename=None, mode='wb'):
        if filename and filename != '-':
            fh = open(file=filename, mode=mode)
        else:
            fh = sys.stdout.buffer

        try:
            yield fh
        finally:
            if fh is not sys.stdout:
                fh.close()

    @staticmethod
    @contextlib.contextmanager
    def smart_read(filename=None, mode='rb'):
        if filename and filename != '-':
            fh = open(file=filename, mode=mode)
        else:
            fh = sys.stdin.buffer

        try:
            yield fh
        finally:
            if fh is not sys.stdin.buffer:
                fh.close()