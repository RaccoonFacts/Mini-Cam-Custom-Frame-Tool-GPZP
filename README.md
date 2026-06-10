# Mini-Cam-Custom-Frame-Tool-GPZP
Custom photo frame toolkit for the **Photo Creator Mini Cam** toy digital camera (and likely other Generalplus GPDV-based cameras). Mostly publishing a write up so others can use Ai faster than I did, so it should help. 

Lets you extract, preview, and replace the built-in photo frame overlays stored in the camera's SPI NOR flash chip — no soldering experience required beyond chip clip access.

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
pip install Pillow
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

| Frame | Tile | Flash Offset |
|-------|------|-------------|
| film | CP0001 | see resource table |
| film | CP0002 | see resource table |
| film | CP0003 | see resource table |
| film | CP0100 | see resource table |
| skateboard | CP0101 | see resource table |
| skateboard | CP0102 | see resource table |
| skateboard | CP0103 | see resource table |
| skateboard | CP0200 | see resource table |
| graffiti 4th tile | hardcoded | 0x0DFA00 |

---

## Disclaimer

This is for personal educational use on hardware you own. Always keep a backup of your original firmware. If the flash goes wrong, re-program the original `.bin` backup.

---

## Contributing

If you have a different variant of this camera and find different offsets or color formats, open an issue or PR with your findings. Include your firmware MD5 and chip markings.
