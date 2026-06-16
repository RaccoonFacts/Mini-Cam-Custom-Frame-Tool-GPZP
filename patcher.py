#!/usr/bin/env python3
# patcher.py
# Patches fitted GPZP strips into firmware bin
# Usage: python3 patcher.py <firmware.bin> <frame_name> <strip_dir>

import sys, os, shutil, zlib

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

def get_original_size(fw, off):
    chunk = fw[off:off+200000]
    d = zlib.decompressobj(wbits=-15)
    d.decompress(chunk)
    return len(chunk) - len(d.unused_data)

def patch(fw_path, frame_name, strip_dir):
    if frame_name not in FRAMES:
        print(f"Unknown frame. Options: {', '.join(FRAMES.keys())}"); sys.exit(1)

    backup = fw_path + '.bak'
    if not os.path.exists(backup):
        shutil.copy2(fw_path, backup)
        print(f'Backup -> {backup}')
    else:
        print(f'Backup exists: {backup}')

    fw = bytearray(open(fw_path,'rb').read())

    for i, tile in enumerate(FRAMES[frame_name]):
        path = os.path.join(strip_dir, f'fitted_strip{i}.bin')
        if not os.path.exists(path):
            print(f'MISSING {path} — skipping'); continue

        new_data = open(path,'rb').read()[4:]  # strip GPZP header
        off = GRAFFITI_4TH if tile is None else TILE_OFFSETS[tile]
        old_size = get_original_size(fw, off)
        new_size = len(new_data)

        print(f'  {tile or "0x0DFA04"} @ 0x{off:06X}: old={old_size} new={new_size} bytes', end='')

        if new_size > old_size:
            print(f'  WARNING: {new_size-old_size} bytes over, writing anyway')
        else:
            new_data = new_data + bytes([0xFF]*(old_size-new_size))
            print(f'  (+{old_size-new_size} padding)')

        fw[off:off+len(new_data)] = new_data

    out = fw_path.replace('.bin', '_patched.bin')
    if out == fw_path:
        out = fw_path + '_patched.bin'
    open(out,'wb').write(fw)
    print(f'\nPatched -> {out}')
    print('Flash: XGPro -> PY25D16 SOP8 -> Erase -> Program -> Verify')

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print('Usage: python3 patcher.py <firmware.bin> <frame_name> <strip_dir>'); sys.exit(1)
    patch(sys.argv[1], sys.argv[2], sys.argv[3])
