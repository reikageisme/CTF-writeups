# Ghost Dependency

> Mã đề `REV-01` · Reverse Engineering · Mục tiêu 150-210 minutes

## Bối cảnh

Northstar Logistics signed and released a Rust-based warehouse agent. The package signature is valid, yet one build sends a token only on a narrowly selected host. Determine exactly what entered the build and reproduce the host condition that activates it.

## Mục tiêu

Create proof.json with the malicious crate digest, the selected host identifier and the recovered 32-byte activation value. Run verify.py proof.json to obtain the flag.

## Tệp được cấp

- `agent.spdx.json`
- `cargo-build.log`
- `registry.tar.zst`
- `warehouse-agent`
- `FORMAT.md`
- `SUBMISSION-FORMAT.md`

## Dữ kiện được bảo đảm

- Exactly one crate archive in registry.tar.zst differs from the source provenance committed by the signed build log.
- No cryptographic primitive must be broken and no network access is required.
- The selected host identifier is present in the supplied evidence after deterministic decoding; it is not a dictionary word.
- verify.py checks a complete commitment and does not reveal which individual field is wrong.

## Nộp bài

Phân tích handout, tạo JSON theo `handout/SUBMISSION-FORMAT.md` và gửi tới
endpoint CTFd/service do Ban tổ chức công bố. Không có lệnh `verify.py` cục bộ.
Server chỉ trả kết quả tổng quát, không làm oracle chỉ ra trường sai.

## Gợi ý

- [ENTRY] T+90 minutes: Compare source provenance, not package names or versions. (dẫn vào: crate_sha256)
- [CHOKE] T+150 minutes: The activation check is split across two Rust async states; reconstruct the state transition before evaluating the hash. (chốt: host_id)

## Cạm bẫy đã công bố

No signature forgery or cryptographic break is needed or intended. A crate hash that merely matches SPDX is not enough: the SPDX-trusted crate declares build="build.rs" but ships no such file, so you must read the subverted build.rs and prove it with malicious_snippet_sha256 = sha256(build.rs).

## Quy định

- Không cần Internet ngoài endpoint nộp bài được công bố.
- Không được truy cập thư mục organizer hoặc service state.
- Giữ nguyên tên tệp, schema, encoding và giá trị kỹ thuật.
