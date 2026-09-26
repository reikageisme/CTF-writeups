# Public submission format — Ghost Dependency

Nộp một JSON duy nhất tới endpoint server của Ban tổ chức:

```json
{
  "challenge": "REV-01",
  "proof": {}
}
```

Các khóa bắt buộc: `proof: crate_sha256, host_id, activation_hex, malicious_snippet_sha256`. Mọi JSON được chuẩn hóa UTF-8, sort key và không
được có trường thừa. Server chỉ trả `accepted` hoặc `rejected`, không chỉ ra
trường sai. Không có verifier hoặc cờ trong handout.
