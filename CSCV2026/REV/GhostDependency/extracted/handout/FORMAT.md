# FORMAT

Submit `proof.json` — an object with EXACTLY these three string fields:
- `crate_sha256` : SHA-256 (hex) of the malicious crate archive (telemetry-core).
- `host_id`      : identity of the warehouse agent. Run `./warehouse-agent`; the printed
                  value is derived at runtime (HMAC of a device nonce) — not stored.
- `activation_hex`: SHA-256 of `crate_sha256 + ":" + host_id`.

Reading `agent.spdx.json` gives the digest the SBOM *believes* for telemetry-core.
If a crate in `registry.tar.zst` does not match that claimed digest, that crate is
the subverted one — recover its archive and hash it. `registry.tar.zst` zstd → tar;
each `.crate` is gzip(tar(...)). Explain, in the writeup, *why* the crate is hostile
(look at its `build.rs`).
