#!/usr/bin/env python3
"""Convert a raw STM32 application binary into a TinyUF2-compatible UF2."""

import argparse
import struct
from pathlib import Path

UF2_MAGIC_START_0 = 0x0A324655
UF2_MAGIC_START_1 = 0x9E5D5157
UF2_MAGIC_END = 0x0AB16F30
UF2_FLAG_FAMILY_ID = 0x2000
UF2_PAYLOAD_SIZE = 256
UF2_BLOCK_SIZE = 512


def convert_bin_to_uf2(data: bytes, base_address: int, family_id: int) -> bytes:
    padding = (-len(data)) % UF2_PAYLOAD_SIZE
    if padding:
        data += b"\xff" * padding

    block_count = len(data) // UF2_PAYLOAD_SIZE
    blocks = []
    for block_number in range(block_count):
        offset = block_number * UF2_PAYLOAD_SIZE
        payload = data[offset:offset + UF2_PAYLOAD_SIZE]
        header = struct.pack(
            "<IIIIIIII",
            UF2_MAGIC_START_0,
            UF2_MAGIC_START_1,
            UF2_FLAG_FAMILY_ID,
            base_address + offset,
            UF2_PAYLOAD_SIZE,
            block_number,
            block_count,
            family_id,
        )
        block = header + payload + b"\0" * (476 - UF2_PAYLOAD_SIZE)
        block += struct.pack("<I", UF2_MAGIC_END)
        if len(block) != UF2_BLOCK_SIZE:
            raise AssertionError("invalid UF2 block size")
        blocks.append(block)
    return b"".join(blocks)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-i", "--input", required=True, type=Path)
    parser.add_argument("-o", "--output", required=True, type=Path)
    parser.add_argument("-b", "--base", required=True, type=lambda value: int(value, 0))
    parser.add_argument("-f", "--family-id", required=True, type=lambda value: int(value, 0))
    args = parser.parse_args()

    input_data = args.input.read_bytes()
    output_data = convert_bin_to_uf2(input_data, args.base, args.family_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output_data)
    print(f"Converted: {args.input} -> {args.output}")
    print(f"  Input bytes: {len(input_data)}")
    print(f"  UF2 bytes: {len(output_data)}")
    print(f"  Base: 0x{args.base:08X}")
    print(f"  Family ID: 0x{args.family_id:08X}")
    print(f"  Blocks: {len(output_data) // UF2_BLOCK_SIZE}")


if __name__ == "__main__":
    main()
