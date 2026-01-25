# Writeup: flagchecker1 - Android Reverse Engineering (100 pts)

## 1. Phân tích tổng quan
Thử thách cung cấp một file APK Android. Sau khi phân tích file `AndroidManifest.xml` và các lớp Java, chúng ta xác định logic kiểm tra flag chính nằm trong thư viện native `libnative-lib.so` thông qua hàm JNI:
`Java_com_vsl_flagchecker_MainActivity_checkFlag`.

## 2. Reverse Engineering lớp Native
Sử dụng công cụ disassembly (như Ghidra hoặc IDA), chúng ta xác định được các thành phần quan trọng trong `libnative-lib.so`:

### a. Khởi tạo trạng thái (Seed & RNG)
Chương trình sử dụng thuật toán hash **DJB2** để băm chuỗi cố định `"VKU_SECRUITY_LAB"`. Kết quả này được dùng làm seed cho một bộ sinh số ngẫu nhiên tuyến tính (LCG) có tên `ObfRand48` (multiplier: `0x5DEECE66D`, increment: `0x0B`).

### b. Thuật toán mã mã hóa
Dựa trên các hằng số và cấu trúc vòng lặp, thuật toán được xác định là một biến thể của **XTEA**:
*   **Hằng số Delta:** `0x61C88647` (thay vì `0x9E3779B9` tiêu chuẩn).
*   **Cập nhật Sum:** Trong vòng lặp chính, giá trị `sum` được cập nhật bằng lệnh `sub` (`sum = sum - delta`), điều này yêu cầu chúng ta phải đảo ngược chính xác thứ tự cập nhật khi giải mã.
*   **Chế độ khối (Mode):** Hoạt động theo cơ chế tương tự **CBC**. 8 byte đầu tiên của dữ liệu mục tiêu là Vector khởi tạo (IV/Mask). Các khối 8-byte tiếp theo sau khi giải mã XTEA sẽ được XOR với khối ciphertext trước đó để thu được plaintext.

### c. Trích xuất dữ liệu từ Binary
*   **Key (16 bytes):** Tại offset `0x900` là chuỗi hex `0ddc01c863994541812dfc0479296063`.
*   **Ciphertext (72 bytes):** Tại offset `0x930`, bao gồm 8 byte IV và 64 byte dữ liệu đã mã hóa.

## 3. Script Giải mã (Python)

Dưới đây là mã nguồn để khôi phục flag:

```python
import struct

def xtea_decrypt_custom(l, r, k, delta):
    # Tạo danh sách các giá trị sum đã được sử dụng khi mã hóa (sum = sum - delta)
    sums = []
    curr_sum = 0
    for i in range(32):
        s_old = curr_sum
        curr_sum = (curr_sum - delta) & 0xFFFFFFFF
        sums.append((s_old, curr_sum))
    
    # Giải mã ngược từ vòng lặp cuối về đầu
    for s_old, s_new in reversed(sums):
        r = (r - (((l << 4 ^ l >> 5) + l) ^ (s_new + k[(s_new >> 11) & 3]))) & 0xFFFFFFFF
        l = (l - (((r << 4 ^ r >> 5) + r) ^ (s_old + k[s_old & 3]))) & 0xFFFFFFFF
    return l, r

# Cấu hình dữ liệu
key_hex = "0ddc01c863994541812dfc0479296063"
target_hex = "a369c782fb8e4e527f110fb15ad8e0cb0cb848d149e6096060beca9b28c9818adea0f1af237492b1b4d8f9d9de35930370d34c9d9e6b50cbe5521b5a9a2ec82138abaa7bd0779560"
delta = 0x61C88647

K = struct.unpack("<4I", bytes.fromhex(key_hex))
data = bytes.fromhex(target_hex)

# 8 byte đầu là IV/Mask ban đầu
curr_mask_L, curr_mask_R = struct.unpack("<2I", data[0:8])
flag_bytes = b""

# Giải mã từng khối 8 byte
for i in range(8, len(data), 8):
    l_out, r_out = struct.unpack("<2I", data[i:i+8])
    
    # 1. Giải mã XTEA
    l_work, r_work = xtea_decrypt_custom(l_out, r_out, K, delta)
    
    # 2. Đảo ngược CBC (XOR với ciphertext block trước đó)
    l_in = (l_work ^ curr_mask_L) & 0xFFFFFFFF
    r_in = (r_work ^ curr_mask_R) & 0xFFFFFFFF
    
    flag_bytes += struct.pack("<2I", l_in, r_in)
    curr_mask_L, curr_mask_R = l_out, r_out

print("Decrypted Flag:", flag_bytes.split(b'}')[0].decode() + "}")
```

## 4. Kết quả
Quá trình giải mã cho ra chuỗi flag hoàn chỉnh. Các byte dư thừa ở cuối (`\x02\x02`) là padding theo chuẩn PKCS7.

**Flag:** `VSL{Reverse_Android_NDK_CPP_1337_Encryption_Algorithm}`
