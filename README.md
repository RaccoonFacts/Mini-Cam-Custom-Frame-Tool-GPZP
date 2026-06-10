# 📷 Mini-Cam-Custom-Frame-Tool-GPZP

Custom photo frame toolkit for the **Photo Creator Mini Cam** toy digital camera (and likely other Generalplus GPDV-based cameras).
Giving this information in a way that AI can understand, they struggle with image placement. Most likely you will get stuck here and I hope it helps you out some. 

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

### Encode your PNG to GPZP tiles
```bash
python3 encode_frame.py myframe.png ./my_strips/
# Outputs strip0.bin - strip3.bin
```

### Patch into firmware
```bash
python3 patch_frame.py py25d16hb@sop8.bin skateboard ./my_strips/
# Outputs py25d16hb@sop8_patched.bin
```

Frame name options: `film`, `skateboard`, `neon_star`, `flower`, `smiley`, `graffiti`

### Reflash
1. Open XGPro, load `py25d16hb@sop8_patched.bin`
2. Select `PY25D16 SOP8`
3. **Erase** → **Program** → **Verify**
4. Reinstall chip, reassemble camera

---

## Technical Details

For anyone wanting to go deeper:

- **Container format:** GPNV (Generalplus proprietary)
- **Image format:** GPZP — 4-byte magic header + raw deflate (zlib wbits=-15)
- **Color format:** UYVY (YUV422 packed), U and V swapped in decode
- **Transparency key:** `U=128, V=128, Y=140`
- **Tile size:** 640×120 pixels
- **Frame layout:** 4 tiles stacked vertically → 640×480 final image
- **Flash chip:** PY25D16, 2MB SPI NOR, SOP8 package
- **Resource base address:** `0x07EC00`
- **Resource index table:** `0x83400`
- **Platform:** Generalplus GPDV, ARM Cortex-M

---

## Stock Frame Offsets

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
