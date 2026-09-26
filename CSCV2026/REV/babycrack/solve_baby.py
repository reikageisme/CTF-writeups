"""Static BabyCrackMe solver. Run with Python 3 and cryptography installed."""

from pathlib import Path
from hashlib import sha256
import re
import struct

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7


root = Path(__file__).resolve().parent
binary_candidates = (
    root / "extracted" / "Challenge1" / "chall.exe",
    root / "extracted" / "chall.exe",
    root / "Challenge1" / "chall.exe",
    root / "chall.exe",
)
binary_path = next((path for path in binary_candidates if path.exists()), None)
if binary_path is None:
    raise FileNotFoundError(
        "Extract BabyCrackme.7z into extracted/ (password: infected) first"
    )
binary = binary_path.read_bytes()

# The outer PE carries an embedded PE at file offset 0xE00. Its .text starts
# at embedded file offset 0x400. The first function builds an 80-byte vector
# with twenty `mov dword ptr [rbp+disp8], imm32` instructions.
code = binary[0x1200:0x12A1]
encoded = bytearray(80)
seen = set()
for match in re.finditer(rb"\xC7\x45(.)(.{4})", code, re.DOTALL):
    displacement = struct.unpack("<b", match.group(1))[0]
    position = displacement + 0x50
    if 0 <= position <= 76 and position % 4 == 0:
        encoded[position:position + 4] = match.group(2)
        seen.update(range(position, position + 4))
assert len(seen) == 80, f"Recovered {len(seen)} of 80 embedded bytes"

# The embedded program uses the first 32 bytes as an AES-256 key. It derives
# the CBC IV by combining the high nibble of each even byte with the low
# nibble of the next byte. The remaining 48 bytes are ciphertext.
key = bytes(encoded[:32])
iv = bytes(((key[i] << 4) & 0xF0) | (key[i + 1] & 0x0F)
           for i in range(0, 32, 2))
decryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
padded = decryptor.update(bytes(encoded[32:])) + decryptor.finalize()
unpadder = PKCS7(128).unpadder()
target = unpadder.update(padded) + unpadder.finalize()

# Each output byte takes one bit from each of eight input bytes, rotating
# the source byte index by the output position. Reverse that permutation.
password = bytearray()
for offset in range(0, 32, 8):
    block = bytearray(8)
    for output_index, value in enumerate(target[offset:offset + 8]):
        for bit in range(8):
            source_index = (output_index + bit) & 7
            block[source_index] |= value & (0x80 >> bit)
    password.extend(block)

def transform(block):
    return bytes(sum(block[(out + bit) & 7] & (0x80 >> bit)
                     for bit in range(8)) for out in range(8))

assert b"".join(transform(password[i:i + 8])
                for i in range(0, 32, 8)) == target[:32]
print("Password:", password.decode("ascii"))

# The file decryptor hashes the accepted password with SHA-256. It uses that
# digest as the AES-256 key and builds the IV from the low nibbles of adjacent
# digest bytes. BCryptDecrypt is called with block padding enabled.
encrypted_paths = (
    root / "extracted" / "Challenge1" / "flag.png.enc",
    root / "extracted" / "flag.png.enc",
    root / "Challenge1" / "flag.png.enc",
    root / "flag.png.enc",
)
encrypted_path = next((path for path in encrypted_paths if path.exists()), None)
if encrypted_path is None:
    raise FileNotFoundError(
        "Extract BabyCrackme.7z into extracted/ (password: infected) first"
    )

file_key = sha256(password).digest()
file_iv = bytes(((file_key[i] << 4) & 0xF0) | (file_key[i + 1] & 0x0F)
                for i in range(0, 32, 2))
decryptor = Cipher(algorithms.AES(file_key), modes.CBC(file_iv)).decryptor()
decrypted_padded = decryptor.update(encrypted_path.read_bytes()) + decryptor.finalize()
unpadder = PKCS7(128).unpadder()
png = unpadder.update(decrypted_padded) + unpadder.finalize()
assert png.startswith(b"\x89PNG\r\n\x1a\n"), "Decryption did not produce a PNG"
assert png.endswith(b"IEND\xaeB`\x82"), "Decrypted PNG is truncated"

output_path = encrypted_path.with_name("flag.png")
if not output_path.exists() or output_path.read_bytes() != png:
    output_path.write_bytes(png)
print("Flag image:", output_path)
