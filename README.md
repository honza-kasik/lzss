# LZSS

This is naive* implementation of [LZSS](https://en.wikipedia.org/wiki/Lempel%E2%80%93Ziv%E2%80%93Storer%E2%80%93Szymanski) compression algorithm

## How to run

To encode a file:

```
python3 main.py encode [--input <input>] [--output <output>]
```

To decode:

```
python3 main.py decode [--input <input>] [--output <output>]
```

When you omit any of optional arguments, `stdin` or `stdout` will be used instead...

## How LZSS works

As any other dictionary based `LZ.+` method, this one too uses already read symbols stashed in dictionary to compress data.

### During encoding, these steps are made:

1. Initialize data structures. We'll need dictionary containing already encoded symbols and lookahead buffer.
    * The dictionary is just an empty circular buffer on start
    * Buffer on the other hand will be initialized to the size of maximum allowable match and it will be filled with symbols from the beginning of stream (and is circular too).
1. Take a buffer and from first symbol from it try to find longest match of symbols in dictionary
1. If any match is found, compare its length to minimum size you want to encode as reference (reference takes two bytes, so there is no sense to encode one byte match)
1. If length of match is greater than minimum, then write encoded flag (I use one bit - `b1`) and then reference (I use 12 bits per position in dictionary and 4 bits per length). In case the match is shorter than minimum, write not encoded flag (`b0`) and original byte to output (first byte of buffer).
1. Add first byte of buffer to dictionary (it was already encoded either way)
1. Reference hides several bytes, so if you outputted reference in previous step, you must push new symbols to buffer from input stream length-times and add each byte to dictionary. Outputting raw byte takes only one space, so read just one byte.
1. Repeat steps from second until there are symbols to read...

### Decoding:

Decoding is much similar to encoding, but no searches for longest match are made. See code (`encoder.py`) for yourself.


### Resources:

* http://michael.dipperstein.com/lzss/
* https://web.archive.org/web/20150111160924/oldwww.rasip.fer.hr/research/compress/algorithms/fund/lz/lzss.html
* http://wiki.xentax.com/index.php/LZSS

---

\* naive approaches are used for both buffer and dictionary when organizing data. Also, the longest match search is implemented as linear search by comparing bytes one by one...