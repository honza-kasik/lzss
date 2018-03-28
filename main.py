#https://stackoverflow.com/a/10691412
class BitWriter(object):
    def __init__(self, f):
        self.accumulator = 0
        self.bcount = 0
        self.out = f

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.flush()

    def __del__(self):
        try:
            self.flush()
        except ValueError:   # I/O operation on closed file.
            pass

    def _writebit(self, bit):
        if self.bcount == 8:
            self.flush()
        if bit > 0:
            self.accumulator |= 1 << 7-self.bcount
        self.bcount += 1

    def writebits(self, bits, n):
        while n > 0:
            self._writebit(bits & 1 << n-1)
            n -= 1

    def flush(self):
        self.out.write(bytearray([self.accumulator]))
        self.accumulator = 0
        self.bcount = 0


class BitReader(object):
    def __init__(self, f):
        self.input = f
        self.accumulator = 0
        self.bcount = 0
        self.read = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def _readbit(self):
        if not self.bcount:
            a = self.input.read(1)
            if a:
                self.accumulator = ord(a)
            self.bcount = 8
            self.read = len(a)
        rv = (self.accumulator & (1 << self.bcount-1)) >> self.bcount-1
        self.bcount -= 1
        return rv

    def readbits(self, n):
        v = 0
        while n > 0:
            v = (v << 1) | self._readbit()
            n -= 1
        return v

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

class Encoder():

    DICTIONARY_SIZE = 4095 #12 bits for position pointer- max value is 4095
    MIN_MATCH_SIZE = 2
    MAX_MATCH_SIZE = 15 #4 bits for length - max value is 15
    ENCODED_FLAG = 0b1

    def __init__(self):
        pass

    def _byte2int(self, byte) -> int:
        assert len(byte) == 1
        return int.from_bytes(byte, byteorder="big")

    def _read_next(self, buffer: CircularBuffer, dictionary: CircularBuffer, infile) -> bool:
        """Read next to buffer, return false if there is nothing to read"""
        dictionary.put_byte(buffer.get_byte_at(0))
        last_byte = infile.read(1)
        if last_byte:
            buffer.put_byte(self._byte2int(last_byte))  # read another byte to buffer
            return True
        else: # EOF?
            buffer.pop()
            return buffer.get_fill() > 0

    def encode(self, inpath, outpath):
        dictionary = CircularBuffer(self.DICTIONARY_SIZE)
        buffer = CircularBuffer(self.MAX_MATCH_SIZE)
        with open(inpath, 'rb') as infile, open(outpath, 'wb') as outfile:
            with bitio.BitWriter(outfile) as writer:
                for i in range(0, self.MAX_MATCH_SIZE): #read max allowable match as initial buffer value
                    buffer.put_byte(self._byte2int(infile.read(1)))
                is_there_something_to_read = True
                while is_there_something_to_read:
                    longest_match_ref = dictionary.get_longest_match(self.MAX_MATCH_SIZE, buffer)
                    if (longest_match_ref.get_length() > self.MIN_MATCH_SIZE):
                        writer.writebits(self.ENCODED_FLAG, 1)
                        writer.writebits(longest_match_ref.get_bits(), 16)
                        #print("Writing ref: " + str(bin(longest_match_ref.get_bits())))
                        for i in range(0, longest_match_ref.get_length()):
                            # go forward since only match reference is written
                            is_there_something_to_read = self._read_next(buffer, dictionary, infile)
                    else:
                        writer.writebits(0, 1)
                        #print("Writing raw: " + str(bin(buffer.get_byte_at(0))))
                        writer.writebits(buffer.get_byte_at(0), 8) #write original byte
                        is_there_something_to_read = self._read_next(buffer, dictionary, infile)

    def decode(self, inpath, outpath):
        dictionary = CircularBuffer(self.DICTIONARY_SIZE)
        with open(inpath, 'rb') as infile, open(outpath, 'wb') as outfile:
            with bitio.BitReader(infile) as reader, bitio.BitWriter(outfile) as writer:
                while True:
                    bit = reader.readbits(1)
                    if (bit == self.ENCODED_FLAG):
                        reference_pos_bits = reader.readbits(12)
                        reference_length_bits = reader.readbits(4)
                        reference = Reference(reference_pos_bits, reference_length_bits)
                        if reference.get_length() <= self.MIN_MATCH_SIZE:
                            raise Exception("There should be no such reference: " + str(reference) + "pos: " + str(infile.tell()))
                        for byte in dictionary.get_match(reference.get_pos(), reference.get_length()):
                            dictionary.put_byte(byte)
                            writer.writebits(byte, 8)
                        if not reader.read:
                            break
                    else:
                        byte = reader.readbits(8)
                        if not reader.read:
                            break
                        dictionary.put_byte(byte)
                        writer.writebits(byte, 8)

if __name__ == '__main__':
    import os
    import sys
    # Determine this module's name from it's file name and import it.
    module_name = os.path.splitext(os.path.basename(__file__))[0]
    bitio = __import__(module_name)

    encoder = Encoder()
    encoder.encode("in.txt", "out.bin")
    encoder.decode("out.bin", "re.txt")
