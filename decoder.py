#!/usr/bin/env python3
# decode_frame.py
# Extracts and renders all stock photo frames from Mini Cam firmware to PNG
#
# Usage:
#   python3 decode_frame.py <firmware.bin>
#
# Output: ./frames/<frame_name>.png for each of the 6 frames

import sys, os, struct, zlib
from PIL import Image

TRANS_U = 128
TRANS_V = 128
TRANS_Y = 140

# Confirmed working offsets/names from resource index table
# Format: (tile_name_or_None, strip_index, hardcoded_offset_if_none)
FRAMES = {
    'film':       ['CP0001', 'CP0002', 'CP0003', 'CP0100'],
    'skateboard': ['CP0101', 'CP0102', 'CP0103', 'CP0200'],
    'neon_star':  ['CP0201', 'CP0202', 'CP0203', 'CP0300'],
    'flower':     ['CP0301', 'CP0302', 'CP0303', 'CP0400'],
    'smiley':     ['CP0401', 'CP0402', 'CP0403', 'CP0500'],
    'graffiti':   ['CP0501', 'CP0502', 'CP0503', None],
}

GRAFFITI_4TH_OFFSET = 0x0DFA00
BASE        = 0x07EC00
RES_TABLE   = 0x83400
ENTRY_SIZE  = 24

def find_offset(fw, name):
    target = (name + 'GPZP').encode('ascii')
    off = RES_TABLE
    while off < RES_TABLE + 0x800:
        entry = fw[off:off+16].rstrip(b'\x00')
        if entry == target:
            idx = struct.unpack_from('<I', fw, off+20)[0]
            return BASE + idx * 512
        off += ENTRY_SIZE
    return None

def yuv_to_rgb(y, u, v):
    u -= 128; v -= 128
    r = max(0, min(255, int(y + 1.402*v)))
    g = max(0, min(255, int(y - 0.344*u - 0.714*v)))
    b = max(0, min(255, int(y + 1.772*u)))
    return (r, g, b, 255)

def decode_tile(raw):
    """Decode a 640x120 UYVY tile to RGBA PIL image."""
    w, h = 640, 120
    pixels = []
    for i in range(0, min(w*h*2, len(raw)-3), 4):
        u, y0, v, y1 = raw[i], raw[i+1], raw[i+2], raw[i+3]
        if u == TRANS_U and v == TRANS_V and y0 == TRANS_Y:
            pixels.append((0, 0, 0, 0))
        else:
            pixels.append(yuv_to_rgb(y0, v, u))
        if u == TRANS_U and v == TRANS_V and y1 == TRANS_Y:
            pixels.append((0, 0, 0, 0))
        else:
            pixels.append(yuv_to_rgb(y1, v, u))
    while len(pixels) < w*h:
        pixels.append((0, 0, 0, 0))
    img = Image.new('RGBA', (w, h))
    img.putdata(pixels)
    return img

def decode_from_offset(fw, offset):
    chunk = fw[offset+4:offset+200000]
    raw = zlib.decompress(chunk, -15)
    return decode_tile(raw)

def decode_named(fw, name):
    off = find_offset(fw, name)
    if off is None:
        print(f'  WARNING: {name} not found in resource table')
        return Image.new('RGBA', (640, 120), (0, 0, 0, 0))
    return decode_from_offset(fw, off)

def main():
    fw_path = sys.argv[1] if len(sys.argv) > 1 else 'py25d16hb@sop8.bin'
    if not os.path.exists(fw_path):
        print(f'Firmware not found: {fw_path}')
        print('Usage: python3 decode_frame.py <firmware.bin>')
        sys.exit(1)

    fw = open(fw_path, 'rb').read()
    print(f'Loaded {fw_path} ({len(fw)} bytes)')

    os.makedirs('frames', exist_ok=True)

    for fname, tiles in FRAMES.items():
        full = Image.new('RGBA', (640, 480), (0, 0, 0, 0))
        for i, tile in enumerate(tiles):
            if tile is None:
                img = decode_from_offset(fw, GRAFFITI_4TH_OFFSET)
            else:
                img = decode_named(fw, tile)
            full.paste(img, (0, i*120), img)
            print(f'  {tile or f"0x{GRAFFITI_4TH_OFFSET:06X}"} -> y={i*120}')
        out = f'frames/{fname}.png'
        full.save(out)
        print(f'Saved {out}\n')

    print('Done. Check ./frames/')

if __name__ == '__main__':
    main()
