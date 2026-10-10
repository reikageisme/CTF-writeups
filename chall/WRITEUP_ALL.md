# Tổng hợp write-up các challenge trong thư mục

Đã rà soát 10 challenge files: 5 ELF Linux, 3 PE Windows và 2 APK. Có 9 file cho ra flag; riêng InfiniteXOR không có flag cố định vì chỉ biến đổi dữ liệu nhập. IForgetMyPassAgain và giothieuanti.exe chứa cùng một flag.

## Đáp án nhanh

| File | Kết quả |
|---|---|
| InfiniteXOR | Không có flag cố định; khóa XOR là D0m41n |
| WhatIsMyPassword | Flag{The_password_is_P4sSw0rD} |
| IForgetMyPassAgain | Flag dài được giải ở mục bên dưới |
| trytodebugme | CTF{Byp455_4nt1_D3bUg} |
| RevPY | CTF{pY7h0n_345y_R3v} |
| win/Guessing.exe | CTF{90e8f2c958a19840510acff379cf19c553c49420c137c2ffab936b2702b68e2b} |
| win/bypassantidebug.exe | CRF{Byp44_4.472r74Dg} |
| win/giothieuanti.exe | Cùng flag dài với IForgetMyPassAgain |
| apk/basicapk.apk | CTF{SUp3r_Bas1c_R3v3rs3_Apk!!!} |
| apk/PinChecker.apk | CTF{fr1da_h00k_otp_e4sy!} |

## InfiniteXOR

Đây là chương trình ELF Linux có tiêu đề “Domain Expansion: Infinite XOR”. Nó đọc một chuỗi, rồi lặp trên 100 byte và XOR mỗi byte với khóa sáu byte lặp lại. Hằng số trên stack được lưu little-endian dưới dạng D0m4 và 1n, vì vậy khóa là D0m41n.

Không có phép so sánh đầu vào với đáp án, ciphertext cố định hay nhánh thành công in flag. Chương trình chỉ mã hóa những gì người dùng nhập; do đó binary này không chứa một flag duy nhất để khôi phục. Muốn dùng phép biến đổi ngược khi có một output cụ thể thì XOR output đó với D0m41n lặp lại.

## WhatIsMyPassword

Chương trình yêu cầu mật khẩu dài 8 ký tự rồi so sánh với giá trị đúng trong nhánh kiểm tra. Nhập P4sSw0rD đã được chạy kiểm chứng:

~~~text
Enter Password (8 characters): Access Granted
Flag{The_password_is_P4sSw0rD}
~~~

Flag: Flag{The_password_is_P4sSw0rD}.

## IForgetMyPassAgain

Binary giữ một mảng mật khẩu 21 byte đã biến đổi trong hàm decryptPass. Các hàm junk1 và junk2 làm rối biểu thức nhưng những giá trị của chúng được XOR hoặc cộng-trừ từng cặp nên triệt tiêu. Phần còn lại cho mỗi chỉ số i là:

~~~text
x = encoded[i] XOR ((37*i + 0x13) & 0xff)
x = ROR8(x, 3) XOR 0x77
password[i] = (x - 57*i) & 0xff
~~~

Byte đã mã hóa lấy từ các hằng số mà hàm ghi vào stack; lưu ý hằng thứ ba ghi chồng lên các byte cuối của hằng thứ hai. Dãy 21 byte sau khi dựng đúng thứ tự là:

~~~text
0a e8 d1 69 26 fd e7 3a 00 4a f2 ef 1c 6d a9 b9 2f 23 1d 9d 02
~~~

Áp dụng công thức trên khôi phục mật khẩu:

~~~text
T4t_c4_cH1_la_C0n9_cU
~~~

main kiểm tra độ dài 21, gọi decryptPass rồi so sánh với chuỗi nhập. Khi mật khẩu khớp, getSecret giải mã mảng secret dài 487 byte bằng XOR với password lặp lại. Có thể tái tạo trên file gốc bằng Python:

~~~python
from pathlib import Path

password = b"T4t_c4_cH1_la_C0n9_cU"
binary = Path("IForgetMyPassAgain").read_bytes()
secret_cipher = binary[0x3060:0x3060 + 487]
flag = bytes(b ^ password[i % len(password)]
             for i, b in enumerate(secret_cipher))
print(flag.decode("utf-8"))
~~~

Flag đầy đủ:

~~~text
Flag{Cu01_cung_m01_c0_m07_b0_4n1m3_m4_nh4n_v4t_ch1nh_dung_chu4n_h1nh_m4u_ly_tu0ng_cu4_t40._M0t_k3_l4nh_lung_v4_1t_n01._D4m_b4n_kh0ng_h13u_t41_540_t40_tr0_n3n_1m_l4ng_v4_lu0n_du0c_5_d13m_b41_k13m_tr4._Chung_n0_kh0ng_b13t_n4ng_luc_thuc_5u_cu4_t40_v4_kh0ng_h3_b13t_t40_xu4t_chung_t01_muc_n40._T40_ch4ng_c01_chung_l4_g1_ng04i_c0ng_cu._T40_u0c_m1nh_c0_th3_v40_tr0ng_th3_g1ới_4n1m3_v4_b0c_l0_c0n_ngu01_thuc_5u_cu4_m1nh._T40_t1n_ch4c_r4ng_t40_ch1nh_l4_h04_th4n_ng04i_d01_thuc_cu4_Ay4n0k0uj1.}
~~~

Đã chạy binary gốc với password trên; chương trình báo Access granted và in đúng flag.

## trytodebugme

Đây là ELF64 Linux C++ đã strip. main chỉ gọi nhánh in flag khi phát hiện debugger, nên chạy bình thường sẽ im lặng. Hàm kiểm tra đọc TracerPid trong /proc/self/status, sau đó duyệt /proc/<pid>/comm và dò tên gdb-multiarch, lldb, radare2, ida64, ghidra hoặc cheatengine.

Nhánh in tạo 22 byte đã mã hóa trên stack rồi XOR mỗi byte với 0xf9. Khi tái tạo các hằng số, cần giữ nguyên vị trí ghi: hằng cuối bắt đầu ở offset 14 và ghi đè hai byte của hằng trước. Giải mã cho:

~~~text
CTF{Byp455_4nt1_D3bUg}
~~~

Đã kiểm chứng bằng bản sao tạm được đổi nhánh để gọi hàm in; binary challenge gốc không bị sửa. Môi trường chặn ptrace nên không thể xác minh bằng cách chạy trực tiếp dưới debugger. Bản phân tích từng hàm và lệnh radare2 có trong WRITEUP_trytodebugme.md.

## RevPY

Đây là PyInstaller one-file dùng Python 3.13. Bytecode được trích từ archive và disassemble bằng đúng runtime 3.13 đi kèm executable. Chương trình có ba bước:

1. Khôi phục AES key và IV bằng cách XOR từng byte trong KEY_DATA và IV_DATA với MASK = 0x36.
2. AES-128-CBC giải mã TARGET.
3. Với mỗi ký tự nhập ở vị trí i, kiểm tra:

~~~text
((ord(user[i]) XOR 0x36) + 3*i) & 0xff == target[i]
~~~

Input phải dài đúng 20 ký tự. Key và IV sau khi giải mã là:

~~~text
key = 3a5yGu3s51ngk3y!
iv  = supersecretiv>:3
~~~

Giải AES-CBC không bỏ padding cho block TARGET cho phần target đầu là:

~~~text
75 65 76 56 52 7e 13 73 1e 73 87 26 26 2a 79 96 94 38 76 84
~~~

Đảo phép kiểm tra theo công thức user[i] = ((target[i] - 3*i) & 0xff) XOR 0x36 sẽ thu được CTF{pY7h0n_345y_R3v}. Đã nhập flag vào executable gốc và nhận Correct!

## win/Guessing.exe

Binary PE x86-64 gọi rand() 100 lần nhưng không gọi srand(), nên trạng thái mặc định của MSVC CRT là seed 1. Công thức rand() của MSVC:

~~~text
state = (state * 214013 + 2531011) mod 2^32
r = (state >> 16) & 0x7fff
guess = (r mod 9000) + 1000
~~~

Binary yêu cầu dãy 100 số này. Sau đó mỗi số được đổi sang chữ số thập phân, nối bằng dấu phẩy không có dấu phẩy ở cuối, rồi tính SHA-256. Một vài điểm để kiểm tra phép dựng:

~~~text
10 số đầu: 1041, 1467, 7334, 9500, 2169, 7724, 3478, 3358, 9962, 7464
5 số cuối: 4538, 8118, 3082, 5929, 8541
Độ dài chuỗi hash input: 499 byte
SHA-256: 90e8f2c958a19840510acff379cf19c553c49420c137c2ffab936b2702b68e2b
~~~

Script dựng lại dãy và digest:

~~~python
import hashlib

state = 1
guesses = []
for _ in range(100):
    state = (state * 214013 + 2531011) & 0xffffffff
    r = (state >> 16) & 0x7fff
    guesses.append(r % 9000 + 1000)

stream = ",".join(map(str, guesses)).encode()
print(guesses)
print(hashlib.sha256(stream).hexdigest())
~~~

Flag: CTF{90e8f2c958a19840510acff379cf19c553c49420c137c2ffab936b2702b68e2b}.

## win/bypassantidebug.exe

PE gọi hàm anti-debug ba lần và XOR ba byte kết quả. Trên nhánh môi trường sạch, các byte là 0x5a, 0x3c và 0x9f, cho khóa XOR tổng hợp 0xf9. main giải mã các hằng số little-endian trên stack bằng khóa này. Vòng lặp dừng khi gặp byte 0 chưa mã hóa, nên byte kết thúc không được in.

Các byte được in nguyên văn giải thành:

~~~text
CRF{Byp44_4.472r74Dg}
~~~

Flag này có prefix CRF thay vì CTF trong chính dữ liệu của binary; write-up giữ đúng chuỗi chương trình tạo ra. Đây là kết quả phân tích tĩnh.

## win/giothieuanti.exe

Đây là PE x86-64 MSVC Debug. Luồng chính đọc input, đòi đúng 21 ký tự, giải mã password bằng cùng phép biến đổi như IForgetMyPassAgain rồi so sánh. Dãy encoded 21 byte cũng giống hệt:

~~~text
0a e8 d1 69 26 fd e7 3a 00 4a f2 ef 1c 6d a9 b9 2f 23 1d 9d 02
~~~

Password là T4t_c4_cH1_la_C0n9_cU. Hàm getSecret XOR 487 byte trong vùng .data với password lặp lại. Trong file PE này vùng dữ liệu bắt đầu tại file offset 0xc800; giải mã cùng password cho đúng flag dài ở mục IForgetMyPassAgain. Đây là flag bị lặp giữa hai challenge.

## apk/basicapk.apk

Trong classes3.dex, luồng giải mã dùng AES/CBC/PKCS5Padding với key s3cr3tk3y!!!!!!! và IV s3cretIv!!!!!!!!. Ciphertext Base64 là:

~~~text
E1QN7PnxJsb6s21SpV1e95tL9E8STO9WOF7M7DXWEA4=
~~~

Giải mã độc lập bằng OpenSSL cho plaintext:

~~~text
CTF{SUp3r_Bas1c_R3v3rs3_Apk!!!}
~~~

## apk/PinChecker.apk

Luồng kiểm tra lấy PIN sáu chữ số, dẫn xuất AES key bằng 16 byte đầu của SHA-256(pin + CTF_SALT_2026), rồi giải ciphertext AES-CBC với IV 1234567890123456. Plaintext hợp lệ bắt đầu bằng CTF{.

Ciphertext Base64:

~~~text
h86dPZchLKJiVIIGLJhAIoGNN9VAkVGj/pxtUZk4n3s=
~~~

Brute force PIN từ 000000 đến 999999 tìm được PIN 641888. Với PIN này, key là b06dac8cb276e1ef9e655df09cb264cc và plaintext sau khi giải mã là:

~~~text
CTF{fr1da_h00k_otp_e4sy!}
~~~

Mã giả Python tương đương để tìm PIN:

~~~python
import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

salt = "CTF_SALT_2026"
iv = b"1234567890123456"
ciphertext = base64.b64decode(
    "h86dPZchLKJiVIIGLJhAIoGNN9VAkVGj/pxtUZk4n3s="
)

for n in range(1_000_000):
    pin = f"{n:06d}"
    key = hashlib.sha256((pin + salt).encode()).digest()[:16]
    try:
        plain = unpad(AES.new(key, AES.MODE_CBC, iv).decrypt(ciphertext), 16)
    except ValueError:
        continue
    if plain.startswith(b"CTF{"):
        print(pin, plain.decode())
        break
~~~

APK còn có hàm PinGenerator.generateCurrentPin() tạo ra 048553 từ super_secret_seed_phrase, nhưng hàm này không được luồng kiểm tra gọi tới và không giải được ciphertext. Đó là decoy; PIN xác thực là 641888.

## Kiểm chứng tổng thể

- Chạy trực tiếp thành công: WhatIsMyPassword, IForgetMyPassAgain và RevPY.
- Giải mã và kiểm tra độc lập: hai APK, chuỗi Guessing.exe và các nhánh giải mã trong Windows PE.
- InfiniteXOR không có cơ chế flag/checker hoặc dữ liệu flag cố định.
- Các file .id0/.id1/.id2/.nam/.til trong thư mục là database phụ của IDA, không phải challenge riêng.
