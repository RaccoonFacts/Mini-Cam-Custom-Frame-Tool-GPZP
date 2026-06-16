#!/usr/bin/env python3
# frame_encoder.py
# Converts a 640x480 RGBA PNG into 4 GPZP strip files ready for patching
#
# Usage: python3 frame_encoder.py <input.png> <output_dir>

import sys, os, zlib, ctypes, ctypes.util
from PIL import Image

TRANS_U, TRANS_V, TRANS_Y = 128, 128, 140

libz = ctypes.CDLL(ctypes.util.find_library('z'))

class z_stream(ctypes.Structure):
    _fields_ = [
        ('next_in',   ctypes.c_char_p),
        ('avail_in',  ctypes.c_uint),
        ('total_in',  ctypes.c_ulong),
        ('next_out',  ctypes.c_char_p),
        ('avail_out', ctypes.c_uint),
        ('total_out', ctypes.c_ulong),
        ('msg',       ctypes.c_char_p),
        ('state',     ctypes.c_void_p),
        ('zalloc',    ctypes.c_void_p),
        ('zfree',     ctypes.c_void_p),
        ('opaque',    ctypes.c_void_p),
        ('data_type', ctypes.c_int),
        ('adler',     ctypes.c_ulong),
        ('reserved',  ctypes.c_ulong),
    ]

def compress_fixed(data):
    """Compress using fixed Huffman deflate (BTYPE=1) — required by camera."""
    Z_FIXED, Z_DEFLATED, Z_FINISH = 4, 8, 4
    zst = z_stream()
    zst.next_in = ctypes.c_char_p(data)
    zst.avail_in = len(data)
    out_buf = (ctypes.c_char * 500000)()
    zst.next_out = ctypes.cast(out_buf, ctypes.c_char_p)
    zst.avail_out = 500000
    libz.deflateInit2_(ctypes.byref(zst), 6, Z_DEFLATED, -15, 8, Z_FIXED, b'1.2.11', ctypes.sizeof(zst))
    libz.deflate(ctypes.byref(zst), Z_FINISH)
    size = 500000 - zst.avail_out
    libz.deflateEnd(ctypes.byref(zst))
    return bytes(out_buf[:size])

def rgb_to_yuv(r, g, b):
    y = max(0, min(255, int( 0.299*r + 0.587*g + 0.114*b)))
    u = max(0, min(255, int(-0.169*r - 0.331*g + 0.500*b + 128)))
    v = max(0, min(255, int( 0.500*r - 0.419*g - 0.081*b + 128)))
    return y, u, v

def encode_strip(img_strip):
    """Convert 640x120 RGBA image to GPZP bytes using fixed Huffman deflate."""
    w, h = 640, 120
    pixels = list(img_strip.getdata())
    raw = bytearray()
    for i in range(0, w*h, 2):
        r0,g0,b0,a0 = pixels[i]
        r1,g1,b1,a1 = pixels[i+1]
        if a0 < 128:
            v, y0, u = TRANS_V, TRANS_Y, TRANS_U
        else:
            y0, u, v = rgb_to_yuv(r0, g0, b0)
        y1 = TRANS_Y if a1 < 128 else rgb_to_yuv(r1, g1, b1)[0]
        raw += bytes([v, y0, u, y1])  # VYUY — U/V swapped per camera hardware
    return b'GPZP' + compress_fixed(bytes(raw))

def main():
    if len(sys.argv) < 3:
        print('Usage: python3 frame_encoder.py <input.png> <output_dir>')
        sys.exit(1)
    img = Image.open(sys.argv[1]).convert('RGBA')
    if img.size != (640, 480):
        print(f'Resizing {img.size} -> 640x480')
        img = img.resize((640, 480), Image.LANCZOS)
    os.makedirs(sys.argv[2], exist_ok=True)
    for i in range(4):
        strip = img.crop((0, i*120, 640, (i+1)*120))
        data = encode_strip(strip)
        path = os.path.join(sys.argv[2], f'strip{i}.bin')
        open(path, 'wb').write(data)
        print(f'strip{i}.bin -> {len(data)} bytes')
    print('\nDone. Run strip_compressor.py to fit strips to firmware tile sizes.')

if __name__ == '__main__': main()
