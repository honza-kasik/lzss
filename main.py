from encoder import Encoder
import argparse

def main():
    parser = argparse.ArgumentParser(description='LZSS encoder/decoder')
    parser.add_argument("mode", type=str, choices=["encode", "decode"],
                        help="set mode, encode for encoding, decode for decoding")
    parser.add_argument("input", type=str,
                        help="path to input file")
    parser.add_argument("output", type=str,
                        help="path to output file")

    args = parser.parse_args()

    encoder = Encoder()
    if args.mode == 'encode':
        encoder.encode(args.input, args.output)
    else:
        encoder.decode(args.input, args.output)


if __name__ == "__main__":
    main()
