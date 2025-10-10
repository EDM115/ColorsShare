import argparse
import math
from pathlib import Path
from typing import List, Tuple

from PIL import Image
from PIL.PngImagePlugin import PngInfo


def _square_dims(n_pixels: int) -> Tuple[int, int]:
    """Find near-square width/height for n_pixels."""
    if n_pixels <= 0:
        return (1, 1)
    w = math.ceil(math.sqrt(n_pixels))
    h = math.ceil(n_pixels / w)
    return (w, h)


def _bytes_to_rgba_buffer(data: bytes, width: int, height: int) -> bytes:
    """
    Return a bytes object of length width*height*4 in RGBA order.
    4 bytes -> 1 pixel RGBA. Pixels beyond data are 0,0,0,0 (reserved padding).
    """
    n_pixels = width * height
    needed = n_pixels * 4

    # Pad to a multiple of 4 so we can pack whole pixels for the leading part.
    pad4 = (-len(data)) % 4
    leading = data + b"\x00" * pad4

    if len(leading) > needed:
        # Shouldn't happen with sane dims, but guard anyway
        leading = leading[:needed]

    # Fill the remaining tail with 0,0,0,0 (reserved for padding)
    tail_len = needed - len(leading)
    return leading + b"\x00" * tail_len


def _rgba_buffer_to_bytes(buf: bytes, orig_size: int) -> bytes:
    """Trim the RGBA buffer back to the original byte count."""
    return buf[:orig_size]


def file_to_png(
    input_path: str,
    output_png: str,
    clsh_out: str | None = None,
    compress_level: int = 9,
    optimize: bool = True,
) -> None:
    src = Path(input_path)
    data = src.read_bytes()
    orig_len = len(data)

    # Compute pixels and image dims (4 bytes per pixel)
    n_pixels = math.ceil(orig_len / 4) or 1
    width, height = _square_dims(n_pixels)

    rgba_bytes = _bytes_to_rgba_buffer(data, width, height)

    # Build RGBA image from bytes
    img = Image.frombytes("RGBA", (width, height), rgba_bytes)

    # Keep original length and dims in PNG metadata
    meta = PngInfo()
    meta.add_text("orig_size", str(orig_len))
    meta.add_text("width", str(width))
    meta.add_text("height", str(height))

    img.save(output_png, pnginfo=meta, compress_level=compress_level, optimize=optimize)

    # Optional human-readable CLSH dump: one row per line, space-separated r,g,b,a
    if clsh_out:
        with open(clsh_out, "w", encoding="utf-8") as f:
            f.write(f"# orig_size={orig_len} width={width} height={height}\n")
            # Iterate row-major
            for y in range(height):
                row_tokens: List[str] = []
                base = y * width * 4
                row = rgba_bytes[base : base + width * 4]
                # chunk per pixel
                for x in range(width):
                    i = x * 4
                    r, g, b, a = row[i : i + 4]
                    row_tokens.append(f"{r},{g},{b},{a}")
                f.write(" ".join(row_tokens) + "\n")


def png_to_file(input_png: str, output_file: str) -> None:
    img = Image.open(input_png)
    # Ensure RGBA order; PNG is lossless so channel values round-trip
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    # Retrieve original size
    try:
        orig_len = int(img.text.get("orig_size"))
    except Exception:
        raise ValueError("Missing 'orig_size' metadata; cannot trim padding.")

    raw_rgba = img.tobytes()  # row-major RGBA bytes
    out = _rgba_buffer_to_bytes(raw_rgba, orig_len)
    Path(output_file).write_bytes(out)


def clsh_to_file(input_clsh: str, output_file: str, png_out: str | None = None) -> None:
    """
    Parse a CLSH dump back to bytes (and optionally regenerate PNG).
    Accepts a header line starting with '# orig_size=... width=... height=...'.
    """
    orig_len = None
    width = None
    height = None
    pixels: List[Tuple[int, int, int, int]] = []

    with open(input_clsh, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("#"):
                # Parse simple key=value pairs
                for part in line[1:].split():
                    if "=" in part:
                        k, v = part.split("=", 1)
                        k = k.strip().lower()
                        v = v.strip()
                        if k == "orig_size":
                            orig_len = int(v)
                        elif k == "width":
                            width = int(v)
                        elif k == "height":
                            height = int(v)
                continue

            # Data line: "r,g,b,a r,g,b,a ..."
            tokens = line.split()
            for tok in tokens:
                comps = tok.split(",")
                if len(comps) != 4:
                    raise ValueError(f"Bad token in CLSH: {tok}")
                r, g, b, a = (int(c) for c in comps)
                for c in (r, g, b, a):
                    if not (0 <= c <= 255):
                        raise ValueError(f"Channel out of range in CLSH token: {tok}")
                pixels.append((r, g, b, a))

    if width is None or height is None:
        # If no dims provided, infer a single row
        width = len(pixels)
        height = 1
    if width * height != len(pixels):
        # If the file included padding rows, we still accept it; fix height if possible
        if width > 0 and len(pixels) % width == 0:
            height = len(pixels) // width
        else:
            raise ValueError("Inconsistent CLSH dimensions vs tokens.")

    # Rebuild byte buffer
    buf = bytearray()
    for r, g, b, a in pixels:
        buf.extend([r, g, b, a])

    # If orig_len missing, assume full buffer (no trimming)
    final_len = orig_len if orig_len is not None else len(buf)
    Path(output_file).write_bytes(bytes(buf[:final_len]))

    # Optional: recreate the PNG
    if png_out:
        img = Image.frombytes("RGBA", (width, height), bytes(buf[: width * height * 4]))
        meta = PngInfo()
        meta.add_text("orig_size", str(final_len))
        meta.add_text("width", str(width))
        meta.add_text("height", str(height))
        img.save(png_out, pnginfo=meta, compress_level=9, optimize=True)


def main():
    parser = argparse.ArgumentParser(
        description="Encode arbitrary files as RGBA PNGs and/or CLSH text dumps."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_enc = sub.add_parser("to_png", help="Convert file to PNG (and optional .clsh)")
    p_enc.add_argument("-i", "--input", required=True, help="Input file path")
    p_enc.add_argument("-o", "--output", required=True, help="Output PNG path")
    p_enc.add_argument(
        "-c", "--clsh", required=False, help="Optional path to write a .clsh dump"
    )

    p_dec = sub.add_parser("from_png", help="Reconstruct original file from PNG")
    p_dec.add_argument("-i", "--input", required=True, help="Input PNG path")
    p_dec.add_argument("-o", "--output", required=True, help="Output file path")

    p_txt = sub.add_parser("from_clsh", help="Reconstruct file from .clsh text")
    p_txt.add_argument("-i", "--input", required=True, help="Input .clsh path")
    p_txt.add_argument("-o", "--output", required=True, help="Output file path")
    p_txt.add_argument(
        "--png-out", required=False, help="Optional path to also write a PNG"
    )

    args = parser.parse_args()

    if args.cmd == "to_png":
        file_to_png(args.input, args.output, clsh_out=args.clsh)
    elif args.cmd == "from_png":
        png_to_file(args.input, args.output)
    elif args.cmd == "from_clsh":
        clsh_to_file(args.input, args.output, png_out=args.png_out)


if __name__ == "__main__":
    main()
