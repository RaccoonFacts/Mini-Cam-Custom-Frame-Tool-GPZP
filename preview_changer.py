#!/usr/bin/env python3
# preview_changer.py
# Updates the frame selection preview thumbnail for a given frame slot
#
# Usage: python3 preview_changer.py <firmware.bin> <frame_name> <input.png>
#
# Preview tiles are 160x160 RGB565, top 80 rows are visible in the selection menu
# Transparency key: 0x8C71
#
# frame_name options: film, skateboard, neon_star, flower, smiley, graffiti

import sys, os, zlib, struct, ctypes, ctypes.util
from PIL import Image

TRANS_KEY = 0x8C71  # RGB565 transparency key for preview tiles

PREVIEW_OFFSETS = {
    'film':       0x143A04,
    'skateboard': 0x144004,
    'neon_star':  0x144C04,
    'flower':     0x145804,
    'smiley':     0x147404,
    'graffiti':   0x148E04,
}

libz = ctypes.CDLL(ctypes.util.find_library('z'))

class z_stream(ctypes.Structure):
    _fields_ = [
        ('next_in',   ctypes.c_char_p), ('avail_in',  ctypes.c_uint),
        ('total_in',  ctypes.c_ulong),  ('next_out',  ctypes.c_char_p),
        ('avail_out', ctypes.c_uint),   ('total_out', ctypes.c_ulong),
        ('msg',       ctypes.c_char_p), ('state',     ctypes.c_void_p),
        ('zalloc',    ctypes.c_void_p), ('zfree',     ctypes.c_void_p),
        ('opaque',    ctypes.c_void_p), ('data_type', ctypes.c_int),
        ('adler',     ctypes.c_ulong),  ('reserved',  ctypes.c_ulong),
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

def get_original_size(fw, off):
    chunk = fw[off:off+200000]
    d = zlib.decompressobj(wbits=-15)
    d.decompress(chunk)
    return len(chunk) - len(d.unused_data)

def encode_preview(png_path):
    """Convert PNG to 160x160 RGB565 raw data. Top 80 rows = image, bottom 80 = transparent."""
    img = Image.open(png_path).convert('RGBA')
    img = img.resize((160, 80), Image.LANCZOS)
    raw = bytearray()
    # top 80 rows — image content
    for r,g,b,a in img.getdata():
        px = TRANS_KEY if a < 128 else ((r>>3)<<11) | ((g>>2)<<5) | (b>>3)
        raw += struct.pack('<H', px)
    # bottom 80 rows — transparent padding
    raw += struct.pack('<H', TRANS_KEY) * (160*80)
    return bytes(raw)

def main():
    if len(sys.argv) < 4:
        print('Usage: python3 preview_changer.py <firmware.bin> <frame_name> <input.png>')
        print(f'Frames: {", ".join(PREVIEW_OFFSETS.keys())}')
        sys.exit(1)

    fw_path, frame_name, png_path = sys.argv[1], sys.argv[2], sys.argv[3]

    if frame_name not in PREVIEW_OFFSETS:
        print(f"Unknown frame '{frame_name}'. Options: {', '.join(PREVIEW_OFFSETS.keys())}")
        sys.exit(1)

    fw = bytearray(open(fw_path, 'rb').read())
    off = PREVIEW_OFFSETS[frame_name]

    raw = encode_preview(png_path)
    compressed = compress_fixed(raw)
    old_size = get_original_size(fw, off)
    new_size = len(compressed)

    print(f'{frame_name} preview @ 0x{off:06X}: old={old_size} new={new_size} bytes', end='')

    if new_size > old_size:
        print(f'  WARNING: {new_size-old_size} bytes over, writing anyway')
    else:
        compressed = compressed + bytes([0xFF] * (old_size - new_size))
        print(f'  (+{old_size-new_size} padding)')

    fw[off:off+len(compressed)] = compressed

    out = fw_path.replace('.bin', '_patched.bin')
    if out == fw_path:
        out = fw_path + '_patched.bin'
    open(out, 'wb').write(fw)
    print(f'Patched -> {out}')
    print('Flash: XGPro -> PY25D16 SOP8 -> Erase -> Program -> Verify')

if __name__ == '__main__': main()
