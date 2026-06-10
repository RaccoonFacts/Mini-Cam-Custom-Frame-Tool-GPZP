#!/usr/bin/env python3
# encode_frame.py
# Usage: python3 encode_frame.py myframe.png
# Input: 640x480 RGBA PNG (transparent where photo shows through)
# Output: 4x GPZP tiles ready to flash (strip0.bin - strip3.bin)

from PIL import Image
import struct, zlib, sys, os

TRANS_U = 128
TRANS_V = 128
TRANS_Y = 140

def rgb_to_yuv(r, g, b):
    y =  0.299*r + 0.587*g + 0.114*b
    u = -0.169*r - 0.331*g + 0.500*b + 128
    v =  0.500*r - 0.419*g - 0.081*b + 128
    return int(y), int(u), int(v)

def encode_strip(img_strip):
    """Convert 640x120 RGBA image to GPZP bytes."""
    w, h = 640, 120
    assert img_strip.size == (w, h), f"Strip must be 640x120, got {img_strip.size}"
    pixels = list(img_strip.getdata())
    raw = bytearray()

    for i in range(0, w*h, 2):
        r0,g0,b0,a0 = pixels[i]
        r1,g1,b1,a1 = pixels[i+1]

        if a0 < 128:  # transparent
            u, y0, v = TRANS_U, TRANS_Y, TRANS_V
        else:
            y0, u, v = rgb_to_yuv(r0, g0, b0)
            u  = max(0, min(255, u))
            v  = max(0, min(255, v))
            y0 = max(0, min(255, y0))

        if a1 < 128:  # transparent
            y1 = TRANS_Y
        else:
            y1, _, _ = rgb_to_yuv(r1, g1, b1)
            y1 = max(0, min(255, y1))

        # UYVY packing
        raw += bytes([u, y0, v, y1])

    # Raw deflate compress
    compressed = zlib.compress(bytes(raw), level=9)[2:-4]  # strip zlib header/checksum

    # GPZP header (4 bytes) - use same magic as original
    header = b'GPZP'
    return header + compressed

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 encode_frame.py myframe.png [output_dir]")
        sys.exit(1)

    src = sys.argv[1]
    outdir = sys.argv[2] if len(sys.argv) > 2 else '.'

    img = Image.open(src).convert('RGBA')
    if img.size != (640, 480):
        print(f"Resizing from {img.size} to 640x480...")
        img = img.resize((640, 480), Image.LANCZOS)

    os.makedirs(outdir, exist_ok=True)

    for i in range(4):
        strip = img.crop((0, i*120, 640, (i+1)*120))
        gpzp = encode_strip(strip)
        outpath = os.path.join(outdir, f'strip{i}.bin')
        open(outpath, 'wb').write(gpzp)
        print(f'strip{i}.bin -> {len(gpzp)} bytes')

    print(f'\nDone. Map strips to frame tiles:')
    print(f'  strip0.bin -> CP0X01 (y=0)')
    print(f'  strip1.bin -> CP0X02 (y=120)')
    print(f'  strip2.bin -> CP0X03 (y=240)')
    print(f'  strip3.bin -> CP0X00 (y=360)')

if __name__ == '__main__':
    main()
