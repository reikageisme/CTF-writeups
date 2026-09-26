# Handout manifest — Ghost Dependency

Thư mục này chỉ chứa hiện vật được phát cho đội chơi. Không đặt cờ rõ, lời giải,
source generator, seed, dữ liệu chuẩn đối chiếu hoặc tệp debug tại đây.

| Tệp bắt buộc | Mô tả bổ sung | Trạng thái |
|---|---|---|
| `warehouse-agent` | stripped x86-64 ELF | `664711b3a8bb8de5f637ad2531e22bf7403d7a7901771318a3999691ffd4aba9` |
| `agent.spdx.json` | — | `840a08e4c3714f1e1dfbf88e888ca9c9e6e6b076074489ee3631e9749a8d193d` |
| `cargo-build.log` | — | `9cdb05df6e3983deb41eac3b2f9713f02c4314ba351b6ddd9fd993b23c5b6ca4` |
| `registry.tar.zst` | — | `bde5023aef6199017de871a1cc9c5a2823367bfa688d80ba60e62b59e1b4eb6d` |
| `flag.enc` | — | `00bd2ad27593693d16b595af0715c5046f3e7ac1a76e9e808a70927cac198994` |
| `verify.py` | — | `d8db44aff9db356131dc6e1e5c93a0b2e132ae9fd9bb07962f3b25ac924ab94d` |
| `FORMAT.md` | — | `95f1bad1475afb85fec31c39bdde10079063e0a653eaf997adc96e2f14bec614` |
| `SHA256SUMS` | — | `f22c2b0b3a2c7da7de2885bc28a8d7596dd151a3a5d28f46aa1aa1dddd4f8f49` |

Các cột trạng thái đã được thay bằng SHA-256 sau khi generator tạo hiện vật cuối.
Trình đóng gói sẽ từ chối phát hành nếu còn thiếu bất kỳ tệp bắt buộc nào.
