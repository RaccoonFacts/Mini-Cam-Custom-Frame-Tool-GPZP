#!/usr/bin/env python3
# strip_compressor.py
# Recompresses strips to fit within original firmware tile sizes
# Usage: python3 strip_compressor.py <firmware.bin> <frame_name> <input.png> <strip_dir>

import sys, os, zlib, ctypes, ctypes.util
from PIL import Image

TRANS_U, TRANS_V, TRANS_Y = 128, 128, 140

TILE_OFFSETS = {
    'CP0001': 0x088204, 'CP0002': 0x088C04, 'CP0003': 0x089204, 'CP0100': 0x089804,
    'CP0101': 0x08A404, 'CP0102': 0x08B404, 'CP0103': 0x08BA04, 'CP0200': 0x08CC04,
    'CP0201': 0x091204, 'CP0202': 0x095C04, 'CP0203': 0x097404, 'CP0300': 0x099004,
    'CP0301': 0x09E004, 'CP0302': 0x0A4E04, 'CP0303': 0x0A9804, 'CP0400': 0x0AE804,
    'CP0401': 0x0B3204, 'CP0402': 0x0B9604, 'CP0403': 0x0C3C04, 'CP0500': 0x0CA004,
    'CP0501': 0x0CF604, 'CP0502': 0x0D6A04, 'CP0503': 0x0DB204,
}

GRAFFITI_4TH = 0x0DFA04

FRAMES = {
    'film':       ['CP0001','CP0002','CP0003','CP0100'],
    'skateboard': ['CP0101','CP0102','CP0103','CP0200'],
    'neon_star':  ['CP0201','CP0202','CP0203','CP0300'],
    'flower':     ['CP0301','CP0302','CP0303','CP0400'],
    'smiley':     ['CP0401','CP0402','CP0403','CP0500'],
    'graffiti':   ['CP0501','CP0502','CP0503', None],  # 4th tile hardcoded at 0x0DFA04
}

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

def rgb_to_yuv(r, g, b):
    y = max(0, min(255, int( 0.299*r + 0.587*g + 0.114*b)))
    u = max(0, min(255, int(-0.169*r - 0.331*g + 0.500*b + 128)))
    v = max(0, min(255, int( 0.500*r - 0.419*g - 0.081*b + 128)))
    return y, u, v

def quantize(val, step):
    return (val // step) * step

def encode_raw(img, quant=1, scale=1.0):
    w, h = 640, 120
    if scale < 1.0:
        sw, sh = max(2, int(w*scale)), max(2, int(h*scale))
        img = img.resize((sw,sh), Image.BILINEAR).resize((w,h), Image.NEAREST)
    pixels = list(img.getdata())
    raw = bytearray()
    for i in range(0, w*h, 2):
        r0,g0,b0,a0 = pixels[i]
        r1,g1,b1,a1 = pixels[i+1]
        if a0 < 128:
            v, y0, u = TRANS_V, TRANS_Y, TRANS_U
        else:
            y0,u,v = rgb_to_yuv(r0,g0,b0)
            if quant > 1: y0=quantize(y0,quant); u=quantize(u,quant); v=quantize(v,quant)
        y1 = TRANS_Y if a1<128 else rgb_to_yuv(r1,g1,b1)[0]
        if quant > 1 and a1 >= 128: y1 = quantize(y1, quant)
        raw += bytes([v, y0, u, y1])
    return bytes(raw)

QUALITY_LADDER = [
    (1,1.00),(2,1.00),(4,1.00),(4,0.75),(8,0.75),
    (8,0.50),(16,0.50),(16,0.25),(32,0.25),(32,0.15),
    (64,0.15),(64,0.10),(128,0.10),(128,0.05),
]

def fit_strip(img, max_bytes, idx):
    for quant, scale in QUALITY_LADDER:
        raw = encode_raw(img, quant, scale)
        c = compress_fixed(raw)
        print(f'    quant={quant:3d} scale={scale:.2f} -> {len(c)} bytes (max {max_bytes})', end='')
        if len(c) <= max_bytes:
            print(' ✓')
            return b'GPZP' + c
        print()
    print(f'  WARNING: strip{idx} could not fit, using smallest')
    return b'GPZP' + compress_fixed(encode_raw(img, 128, 0.05))

def main():
    if len(sys.argv) < 5:
        print('Usage: python3 strip_compressor.py <firmware.bin> <frame_name> <input.png> <strip_dir>')
        sys.exit(1)
    fw_path, frame_name, png_path, strip_dir = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    fw = open(fw_path,'rb').read()
    tiles = FRAMES[frame_name]
    img_full = Image.open(png_path).convert('RGBA')
    if img_full.size != (640,480):
        img_full = img_full.resize((640,480), Image.LANCZOS)
    os.makedirs(strip_dir, exist_ok=True)
    for i, tile in enumerate(tiles):
        off = GRAFFITI_4TH if tile is None else TILE_OFFSETS[tile]
        max_bytes = get_original_size(fw, off)
        print(f'\nstrip{i} ({tile or "hardcoded"}) max={max_bytes} bytes:')
        img = img_full.crop((0, i*120, 640, (i+1)*120))
        fitted = fit_strip(img, max_bytes, i)
        out = os.path.join(strip_dir, f'fitted_strip{i}.bin')
        open(out,'wb').write(fitted)
        print(f'  Saved {out} ({len(fitted)} bytes)')
    print('\nDone. Use fitted_strip*.bin with patcher.py')

if __name__ == '__main__': main()
