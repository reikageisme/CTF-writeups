from pathlib import Path
import sys
import struct

sys.path.insert(0, r"D:\CTF\tmp\babycrackme-deps")
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86_const import X86_OP_MEM, X86_REG_RIP


SOURCE = Path(__file__).with_name("chall.exe")
pe = pefile.PE(str(SOURCE))
image = bytearray(pe.get_memory_mapped_image())
base = pe.OPTIONAL_HEADER.ImageBase
md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True


def dump(start, end):
    for insn in md.disasm(bytes(image[start:end]), base + start):
        print(f"{insn.address:016x}  {insn.mnemonic:8} {insn.op_str}")


def xor(start, count, key):
    for i in range(start, start + count):
        image[i] ^= key


if __name__ == "__main__":
    embedded = bytearray(image[0x3000:0x3000 + 0x6a00])
    embedded[:2] = b"MZ"
    embedded[0x100:0x104] = b"PE\0\0"
    inner = pefile.PE(data=bytes(embedded))
    print("=== embedded PE ===")
    print(f"Entry RVA: {inner.OPTIONAL_HEADER.AddressOfEntryPoint:#x}")
    for section in inner.sections:
        print(section.Name, hex(section.VirtualAddress), hex(section.Misc_VirtualSize), hex(section.PointerToRawData), hex(section.SizeOfRawData))
    inner_image = bytearray(inner.get_memory_mapped_image())
    start = struct.unpack_from("<Q", inner_image, 0x8200)[0]
    end = struct.unpack_from("<Q", inner_image, 0x8208)[0]
    print("=== target ===")
    print(hex(start), hex(end), end - start)
    if base <= start < base + len(inner_image):
        print(inner_image[start-base:end-base].hex())
    if len(sys.argv) > 1:
        if sys.argv[1] == "refs":
            for i in range(0x1000, 0x46e4):
                for insn in md.disasm(bytes(inner_image[i:i + 15]), base + i, count=1):
                    for op in insn.operands:
                        if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                            target = insn.address + insn.size + op.mem.disp - base
                            if 0x81f0 <= target <= 0x8210:
                                print(f"{insn.address:016x} -> {target:#x} {insn.mnemonic} {insn.op_str}")
            sys.exit()
        for arg in sys.argv[1:]:
            parts = arg.split(":")
            start = int(parts[0], 16)
            end = int(parts[1], 16) if len(parts) > 1 else start + 0x90
            print(f"=== {start:#x} ===")
            for insn in md.disasm(bytes(inner_image[start:end]), base + start):
                print(f"{insn.address:016x}  {insn.mnemonic:8} {insn.op_str}")
        sys.exit()
    print("=== string references ===")
    for needle in (b"[!] Enter the password", b"[+] Correct", b"[-] Incorrect", b"flag.png.enc", b"flag.png"):
        rva = inner_image.find(needle)
        print(needle, hex(rva))
        for i in range(0x1000, 0x46e4):
            for insn in md.disasm(bytes(inner_image[i:i + 15]), base + i, count=1):
                if any(op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP and insn.address + insn.size + op.mem.disp == base + rva for op in insn.operands):
                    print(f"  {insn.address:016x} {insn.mnemonic} {insn.op_str}")
    print("=== password checker ===")
    for insn in md.disasm(bytes(inner_image[0x23d0:0x2610]), base + 0x23d0):
        print(f"{insn.address:016x}  {insn.mnemonic:8} {insn.op_str}")
    print("=== compare function ===")
    for insn in md.disasm(bytes(inner_image[0x3380:0x36e0]), base + 0x3380):
        print(f"{insn.address:016x}  {insn.mnemonic:8} {insn.op_str}")
    print("=== compare function after jump ===")
    for insn in md.disasm(bytes(inner_image[0x339e:0x36e0]), base + 0x339e):
        print(f"{insn.address:016x}  {insn.mnemonic:8} {insn.op_str}")
    print("=== embedded entry ===")
    for insn in md.disasm(bytes(inner_image[0x3a60:0x3c00]), base + 0x3a60):
        print(f"{insn.address:016x}  {insn.mnemonic:8} {insn.op_str}")
    xor(0x1022, 0x27, 0x15)
    print("=== stage 1 ===")
    dump(0x1022, 0x108b)
    xor(0x108b, 0x2d, 0x33)
    print("=== stage 2 ===")
    dump(0x108b, 0x10f5)
    xor(0x10f5, 0x2e, 0x62)
    print("=== stage 3 ===")
    dump(0x10f5, 0x1156)
    xor(0x1156, 0x47, 0x92)
    print("=== stage 4 ===")
    dump(0x1156, 0x11cd)
    for i in range(0x9e, 0, -1):
        image[0x11cd + i - 1] ^= 0x91
        image[0x11cd + i] ^= 0
    print("=== stage 5 ===")
    dump(0x11cd, 0x129b)
    xor(0x129b, 0xd2, 0x67)
    print("=== stage 6 ===")
    dump(0x129b, 0x139e)
    xor(0x139e, 0x12f, 0xba)
    print("=== stage 7 ===")
    dump(0x139e, 0x14fe)
    xor(0x14fe, 0xb6, 0xde)
    print("=== stage 8 ===")
    dump(0x14fe, 0x15b4)
