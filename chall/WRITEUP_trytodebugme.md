# Write-up: `trytodebugme`

## Kết quả

Flag: **`CTF{Byp455_4nt1_D3bUg}`**

Bài này là ELF64 Linux viết bằng C++, đã bị strip. Chương trình được thiết kế để im lặng khi chạy bình thường; nếu phát hiện debugger thì nó mới chạy nhánh in flag. Vì vậy chạy file rồi thấy không có output chưa chắc là file lỗi.

## 1. Nhận diện binary và tìm luồng chính

Kiểm tra file và kiến trúc:

```bash
file trytodebugme
rabin2 -I trytodebugme
```

Binary là ELF 64-bit x86-64, C++, stripped. Mở bằng radare2 và phân tích:

```bash
r2 -A trytodebugme
```

Trong radare2, xem hàm `main` ở `0x3858`:

```text
pdf @ main
```

`main` gọi hàm tại `0x3787`, kiểm tra giá trị trả về, rồi chỉ gọi hàm in tại `0x37b9` khi giá trị đó khác 0. Nếu không phát hiện debugger, chương trình kết thúc mà không in gì.

Có thể đọc nhanh các hàm liên quan bằng:

```text
pdf @ 0x3787
pdf @ 0x32c9
pdf @ 0x3414
pdf @ 0x37b9
```

## 2. Phân tích cơ chế phát hiện debugger

Hàm `0x3787` kết hợp hai phép kiểm tra:

1. Hàm `0x32c9` mở `/proc/self/status`, tìm dòng `TracerPid:` rồi chuyển phần số phía sau thành số nguyên. `TracerPid` khác 0 nghĩa là tiến trình hiện tại đang bị một tiến trình khác trace.
2. Nếu phép kiểm tra trên không phát hiện gì, hàm `0x3414` duyệt `/proc`. Nó bỏ qua các thư mục không có tên PID dạng số, đọc `/proc/<pid>/comm`, rồi so tên tiến trình với danh sách debugger được nhúng trong binary: `gdb-multiarch`, `lldb`, `radare2`, `ida64`, `ghidra`, `cheatengine`.

Chỉ cần một trong hai phép kiểm tra nhận ra debugger, `0x3787` trả về khác 0. `main` khi đó gọi `0x37b9`; nếu không, chương trình thoát im lặng.

## 3. Giải mã dữ liệu flag

Hàm in `0x37b9` dựng dữ liệu mã hóa trên stack bằng ba hằng 64-bit:

```text
0xcd8980bb82bfadba
0xa6c88d97cda6cccc
0x849eac9bcabda6c8
```

Do x86-64 little-endian, mỗi hằng được ghi ra bộ nhớ theo thứ tự byte đảo ngược. Hàm đặt byte khóa `0xf9`, sau đó lặp đúng `0x16` (22) byte và in từng byte sau phép XOR với khóa.

Có một chi tiết dễ bỏ sót khi tái tạo dữ liệu: hằng thứ ba được ghi tại `[rbp-0x32]`, tức vị trí bắt đầu là byte thứ 14 tính từ `[rbp-0x40]`. Nó ghi đè hai byte cuối của hằng thứ hai. Vì vậy cần mô phỏng đúng vị trí ghi, thay vì nối tuần tự ba hằng 8-byte:

```python
import struct

encoded = bytearray(22)
struct.pack_into("<Q", encoded, 0,  0xcd8980bb82bfadba)
struct.pack_into("<Q", encoded, 8,  0xa6c88d97cda6cccc)
struct.pack_into("<Q", encoded, 14, 0x849eac9bcabda6c8)

flag = bytes(byte ^ 0xf9 for byte in encoded)
print(flag.decode())
```

Kết quả:

```text
CTF{Byp455_4nt1_D3bUg}
```

## 4. Kiểm chứng

Chạy binary gốc trong môi trường hiện tại không in gì, đúng với nhánh “không phát hiện debugger”. Môi trường này chặn `ptrace`, nên không thể xác minh bằng cách khởi chạy trực tiếp dưới radare2. Để kiểm tra nhánh in, mình tạo một bản sao tạm trong `/tmp`, đổi điều kiện nhảy tại offset `0x3878` để đi vào hàm `0x37b9`, rồi chạy bản sao. Nó in đúng:

```text
CTF{Byp455_4nt1_D3bUg}
```

Binary challenge gốc không bị sửa.
