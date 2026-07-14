#!/usr/bin/env python3
"""Create placeholder RGBA PNG icons for Tauri application."""
import struct, zlib, os

icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src-tauri', 'icons')
os.makedirs(icons_dir, exist_ok=True)

def create_rgba_png(path, size):
    """Create a minimal valid RGBA PNG file with a solid blue color (#58a6ff)."""
    sig = b'\x89PNG\r\n\x1a\n'
    
    # IHDR chunk - color type 6 = RGBA
    ihdr_data = struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0)
    ihdr_type = b'IHDR'
    ihdr_chunk = ihdr_type + ihdr_data
    ihdr_crc = struct.pack('>I', zlib.crc32(ihdr_chunk) & 0xffffffff)
    ihdr_len = struct.pack('>I', len(ihdr_data))
    
    # Image data: blue RGBA (88, 166, 255, 255) per pixel
    raw_data = b''
    for y in range(size):
        raw_data += b'\x00'  # filter byte
        for x in range(size):
            raw_data += b'\x58\xa6\xff\xff'  # RGBA blue pixel
    
    compressed = zlib.compress(raw_data)
    idat_type = b'IDAT'
    idat_chunk = idat_type + compressed
    idat_crc = struct.pack('>I', zlib.crc32(idat_chunk) & 0xffffffff)
    idat_len = struct.pack('>I', len(compressed))
    
    # IEND chunk
    iend_type = b'IEND'
    iend_chunk = iend_type
    iend_crc = struct.pack('>I', zlib.crc32(iend_chunk) & 0xffffffff)
    iend_len = struct.pack('>I', 0)
    
    with open(path, 'wb') as f:
        f.write(sig)
        f.write(ihdr_len + ihdr_chunk + ihdr_crc)
        f.write(idat_len + idat_chunk + idat_crc)
        f.write(iend_len + iend_chunk + iend_crc)

# Create RGBA icons
create_rgba_png(os.path.join(icons_dir, '32x32.png'), 32)
create_rgba_png(os.path.join(icons_dir, '128x128.png'), 128)
create_rgba_png(os.path.join(icons_dir, '128x128@2x.png'), 256)

# Create .ico from 32x32
import shutil
shutil.copy(os.path.join(icons_dir, '32x32.png'), os.path.join(icons_dir, 'icon.ico'))
shutil.copy(os.path.join(icons_dir, '128x128.png'), os.path.join(icons_dir, 'icon.icns'))

print(f"RGBA icons created in {icons_dir}")
for f in sorted(os.listdir(icons_dir)):
    print(f"  {f}: {os.path.getsize(os.path.join(icons_dir, f))} bytes")
