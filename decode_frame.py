#!/usr/bin/env python3
# decode_frame.py
# Extracts all stock frames from firmware to PNG
# Usage: python3 decode_frame.py <firmware.bin>

import sys, os, zlib
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

def yuv_to_rgb(y, u, v):
    u -= 128; v -= 128
    r = max(0, min(255, int(y + 1.402*v)))
    g = max(0, min(255, int(y - 0.344*u - 0.714*v)))
    b = max(0, min(255, int(y + 1.772*u)))
    return (r, g, b, 255)

def decode_at(fw, off):
    raw = zlib.decompress(fw[off:off+200000], -15)
    w, h = 640, 120
    pixels = []
    for i in range(0, w*h*2, 4):
        u,y0,v,y1 = raw[i],raw[i+1],raw[i+2],raw[i+3]
        pixels.append((0,0,0,0) if (u==TRANS_U and v==TRANS_V and y0==TRANS_Y) else yuv_to_rgb(y0,v,u))
        pixels.append((0,0,0,0) if (u==TRANS_U and v==TRANS_V and y1==TRANS_Y) else yuv_to_rgb(y1,v,u))
    img = Image.new('RGBA',(w,h)); img.putdata(pixels); return img

def main():
    fw_path = sys.argv[1] if len(sys.argv) > 1 else 'py25d16hb@sop8idk.bin'
    fw = open(fw_path,'rb').read()
    os.makedirs('frames', exist_ok=True)
    for fname, tiles in FRAMES.items():
        full = Image.new('RGBA',(640,480),(0,0,0,0))
        for i, tile in enumerate(tiles):
            off = GRAFFITI_4TH if tile is None else TILE_OFFSETS[tile]
            img = decode_at(fw, off)
            full.paste(img,(0,i*120),img)
            print(f'  {tile or "0x0DFA04"} @ 0x{off:06X}')
        full.save(f'frames/{fname}.png')
        print(f'Saved frames/{fname}.png\n')

if __name__ == '__main__': main()
