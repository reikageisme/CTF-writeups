# Handout manifest — Signed, Sealed, Subverted

Thư mục này chỉ chứa hiện vật được phát cho đội chơi. Không đặt cờ rõ, lời giải,
source generator, seed, dữ liệu chuẩn đối chiếu hoặc tệp debug tại đây.

| Tệp bắt buộc | Mô tả bổ sung | Trạng thái |
|---|---|---|
| `updater-aarch64` | — | `14f9fb754347c83aaa0757819e4f1acd0d6d953a18b49529691dafcc0581b818` |
| `boot.qcow2` | — | `1c4aa4802f685e99047d7e1d63bd426f3d71a7fe6662a259220b52e9c6c93311` |
| `manifest.cddl` | — | `2ecc3bae342cd1ff65f94b2548ea65e0aa59c435211b53fc5d29294cd6e1a55f` |
| `signed-base.upd` | — | `1a936d3b4d915dc30cbb680344dd285d4129a2968bf5c68c79244741cc24f4b4` |
| `public-keys.cbor` | — | `023fa60d78dd3d1e2f260850595244cc1663ae0e2514990b1e8c6c0a8554bfc3` |
| `runner.sh` | — | `3b0db71199e77b34d3dfe7049b36d94d9c0c18bc910d066ea65f1323e793c885` |
| `policy.txt` | — | `0a4b64258e813a4b657d328730bec729377e320052a79cc6e4f91f2a818c2951` |
| `SHA256SUMS` | — | `0dd2694e1954bef9b2d689d48b0f7a28a4cc6e622639dcdc4f66067ba620b3a9` |

Các cột trạng thái đã được thay bằng SHA-256 sau khi generator tạo hiện vật cuối.
Trình đóng gói sẽ từ chối phát hành nếu còn thiếu bất kỳ tệp bắt buộc nào.
