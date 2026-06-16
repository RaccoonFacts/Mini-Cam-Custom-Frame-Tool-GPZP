# 📷 Mini-Cam-Custom-Frame-Tool-GPZP

Custom photo frame toolkit for the **Photo Creator Mini Cam** toy digital camera (and likely other Generalplus GPDV-based cameras).

⚠️ **Work in Progress** — tools are functional but not fully hardened. Use at your own risk, keep your firmware backup safe.

---

---

## What This Does

The camera stores 6 decorative photo frames (film reel, skateboard, neon star, flower, smiley, graffiti) as compressed image tiles inside a 2MB SPI NOR flash chip. This toolkit lets you:

- **Decode** the stock frames to PNG so you can see them
- **Encode** any 640x480 RGBA PNG into the camera's native format
- **Patch** your custom frame into the firmware binary
- **Reflash** the patched firmware back to the camera with an XGPro programmer

---

## Hardware Required

| Item | Notes |
|------|-------|
| XGPro T48 or T56 programmer | Any will work |
| SOIC8 chip clip | To read/write without desoldering |
| Photo Creator Mini Cam | The subject camera |

The flash chip is a **Puya PY25D16 (SOP8)** — select this exact part in XGPro.

---

## Dumping the Firmware

1. Open the camera (4 screws on back)
2. Locate the SOP8 flash chip on the PCB
3. Clip the SOIC8 clip onto the chip **with camera battery removed**
4. In XGPro: select `PY25D16 SOP8` → **Read** → save as `py25d16hb@sop8.bin`
5. Keep this file as your master backup

---

## Installation

```bash
git clone https://github.com/RaccoonFacts/Mini-Cam-Custom-Frame-Tool-GPZP.git
cd Mini-Cam-Custom-Frame-Tool-GPZP
```

---

## Usage

### Decode stock frames to PNG
```bash
python3 decode_frame.py
# Outputs all 6 frames to ./frames/
```

### Create a custom frame
- Open `examples/template.png` in any image editor (Photoshop, GIMP, Krita)
- Design your frame at **640x480 pixels**, **RGBA**
- Transparent pixels = where the photo shows through
- Save as PNG

### Encode and compress your PNG to GPZP tiles
```bash
# Step 1: encode PNG to strips
python3 frame_encoder.py myframe.png ./my_strips/

# Step 2: compress strips to fit firmware tile sizes
python3 strip_compressor.py py25d16hb@sop8.bin smiley myframe.png ./my_strips/
```

### Patch into firmware
```bash
python3 patcher.py py25d16hb@sop8.bin smiley ./my_strips/
# Outputs py25d16hb@sop8_patched.bin
```

### Reflash
1. Open XGPro, load `py25d16hb@sop8_patched.bin`
2. Select `PY25D16 SOP8`
3. **Erase** → **Program** → **Verify**
4. Reinstall chip, reassemble camera

---

## Technical Details

For anyone wanting to go deeper:

- **Container format:** GPNV (Generalplus proprietary)
- **Compression:** Raw deflate with **fixed Huffman coding (BTYPE=1)** — the camera's decompressor rejects dynamic Huffman (BTYPE=2) which is Python's zlib default. Must use `Z_FIXED` strategy via libz ctypes.
- **Color format:** UYVY (YUV422 packed), U and V swapped in decode
- **Transparency key:** `U=128, V=128, Y=140`
- **Tile size:** 640×120 pixels
- **Frame layout:** 4 tiles stacked vertically → 640×480 final image
- **Flash chip:** PY25D16, 2MB SPI NOR, SOP8 package
- **Resource base address:** `0x07EC00`
- **Resource index table:** `0x83400`
- **Platform:** Generalplus GPDV, ARM Cortex-M

### Update the frame selection preview thumbnail
```bash
python3 preview_changer.py py25d16hb@sop8.bin smiley myframe.png
```

This updates the small thumbnail shown in the camera's frame selection menu. Run this alongside the main patcher to keep the preview in sync with your custom frame.

---

## Preview Thumbnail Technical Details

The frame selection menu shows a 160×160 pixel thumbnail for each frame slot. These are stored separately from the main frame tiles in a different region of the firmware.

Key differences from frame tiles:

- **Format:** RGB565 (2 bytes per pixel, little-endian) — not UYVY like the frame tiles
- **Size:** 160×160 pixels = 51200 bytes uncompressed
- **Visible area:** Only the top 160×80 pixels are shown in the menu — the bottom half is always black/transparent padding
- **Transparency key:** `0x8C71` (RGB565) — different from the UYVY frame tile transparency key of `U=128, V=128, Y=140`
- **Compression:** Same fixed Huffman deflate (BTYPE=1) as frame tiles

Preview offsets in firmware:

| Frame | Offset |
|-------|--------|
| film | 0x143A04 |
| skateboard | 0x144004 |
| neon_star | 0x144C04 |
| flower | 0x145804 |
| smiley | 0x147404 |
| graffiti | 0x148E04 |

---

Offsets are located via the resource index table at `0x83400` using base address `0x07EC00`.
Each tile name maps to a named entry in the table formatted as `<name>GPZP` — the tool resolves these automatically. The graffiti 4th tile has no named entry and is hardcoded.

| Frame | Tile | Strip | Y Position |
|-------|------|-------|------------|
| film | CP0001 | 0 | 0 |
| film | CP0002 | 1 | 120 |
| film | CP0003 | 2 | 240 |
| film | CP0100 | 3 | 360 |
| skateboard | CP0101 | 0 | 0 |
| skateboard | CP0102 | 1 | 120 |
| skateboard | CP0103 | 2 | 240 |
| skateboard | CP0200 | 3 | 360 |
| neon_star | CP0201 | 0 | 0 |
| neon_star | CP0202 | 1 | 120 |
| neon_star | CP0203 | 2 | 240 |
| neon_star | CP0300 | 3 | 360 |
| flower | CP0301 | 0 | 0 |
| flower | CP0302 | 1 | 120 |
| flower | CP0303 | 2 | 240 |
| flower | CP0400 | 3 | 360 |
| smiley | CP0401 | 0 | 0 |
| smiley | CP0402 | 1 | 120 |
| smiley | CP0403 | 2 | 240 |
| smiley | CP0500 | 3 | 360 |
| graffiti | CP0501 | 0 | 0 |
| graffiti | CP0502 | 1 | 120 |
| graffiti | CP0503 | 2 | 240 |
| graffiti | hardcoded | 3 | 360 — `0x0DFA00` |

---

## Disclaimer

This is for personal educational use on hardware you own. Always keep a backup of your original firmware. If the flash goes wrong, re-program the original `.bin` backup.

---

## Contributing

If you have a different variant of this camera and find different offsets or color formats, open an issue or PR with your findings. Include your firmware MD5 and chip markings.

---

*Reversed and built by [RaccoonFacts](https://github.com/RaccoonFacts)*
