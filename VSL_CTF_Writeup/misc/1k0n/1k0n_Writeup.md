# Writeup: 1k0n

## Challenge Overview
**Challenge Name**: 1k0n
**Type**: Crypto / Encoding
**Input**: `MUYxRUExRjFGMjFGMUY0MUYxRUYxRjFFRV8xRjFFRTFGMUY4XzFGMUU2MUYxRjExRjFGQzFGMUU2MUYxRkUxRjFGOF8xRjFFQjFGMUZBMUYxRjMxRjFGMzFGMUZF`

## Bước 1: Base64 Decode
Chuỗi đầu vào có format Base64.
```bash
echo "MUYxRUExRjFGMjFGMUY0MUYxRUYxRjFFRV8xRjFFRTFGMUY4XzFGMUU2MUYxRjExRjFGQzFGMUU2MUYxRkUxRjFGOF8xRjFFQjFGMUZBMUYxRjMxRjFGMzFGMUZF" | base64 -d
```
Output:
`1F1EA1F1F21F1F41F1EF1F1EE_1F1EE1F1F8_1F1E61F1F11F1FC1F1E61F1FE1F1F8_1F1EB1F1FA1F1F31F1F31F1FE`

## Bước 2: Phân tích Hex & Unicode
Chuỗi kết quả bao gồm các nhóm ký tự Hex dài 5 ký tự được phân tách bằng dấu gạch dưới `_`.
Mỗi nhóm bắt đầu bằng `1F1xx`. Đây là dải Unicode của **Regional Indicator Symbols** (các ký tự dùng để tạo cờ quốc gia emoji).

Dải này bắt đầu từ `U+1F1E6` tương ứng chữ cái `A`.

Mapping:
- `1F1E6` -> A
- `1F1E7` -> B
- ...

## Bước 3: Giải mã
Ta tách chuỗi và map về ký tự ASCII:

**Nhóm 1:** `1F1EA 1F1F2 1F1F4 1F1EF 1F1EE`
- 1F1EA (E)
- 1F1F2 (M)
- 1F1F4 (O)
- 1F1EF (J)
- 1F1EE (I)
=> **EMOJI**

**Nhóm 2:** `1F1EE 1F1F8`
- 1F1EE (I)
- 1F1F8 (S)
=> **IS**

**Nhóm 3:** `1F1E6 1F1F1 1F1FC 1F1E6 1F1FE 1F1F8`
- 1F1E6 (A)
- 1F1F1 (L)
- 1F1FC (W)
- 1F1E6 (A)
- 1F1FE (Y)
- 1F1F8 (S)
=> **ALWAYS**

**Nhóm 4:** `1F1EB 1F1FA 1F1F3 1F1F3 1F1FE`
- 1F1EB (F)
- 1F1FA (U)
- 1F1F3 (N)
- 1F1F3 (N)
- 1F1FE (Y)
=> **FUNNY**

## Kết quả
Flag: `VSL{EMOJI_IS_ALWAYS_FUNNY}`
