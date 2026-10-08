"""Generates assets/icon.png + icon.ico (pure stdlib): red rounded square with an 'A'."""
import struct, zlib, pathlib
S = 256
def px(x, y):
    r, m = 48, 8
    cx = min(max(x, m + r), S - m - r - 1); cy = min(max(y, m + r), S - m - r - 1)
    if not ((x-cx)**2 + (y-cy)**2 <= r*r and m <= x < S-m and m <= y < S-m): return (0, 0, 0, 0)
    t = (y - 60) / 140
    on = 0 <= t <= 1 and (abs(x - (128 - 55*t)) < 14 or abs(x - (128 + 55*t)) < 14 or (0.6 < t < 0.75 and abs(x-128) < 60))
    return (255, 255, 255, 255) if on else (227, 72, 80, 255)
raw = b"".join(b"\0" + b"".join(bytes(px(x, y)) for x in range(S)) for y in range(S))
def chunk(t, d): c = struct.pack(">I", len(d)) + t + d; return c + struct.pack(">I", zlib.crc32(t + d))
png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", S, S, 8, 6, 0, 0, 0))
       + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
a = pathlib.Path(__file__).resolve().parent.parent / "assets"; a.mkdir(exist_ok=True)
(a / "icon.png").write_bytes(png)
(a / "icon.ico").write_bytes(struct.pack("<HHH", 0, 1, 1) + struct.pack("<BBBBHHII", 0, 0, 0, 0, 1, 32, len(png), 22) + png)
