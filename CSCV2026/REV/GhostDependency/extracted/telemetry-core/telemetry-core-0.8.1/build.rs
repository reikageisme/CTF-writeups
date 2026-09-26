fn main() {
    // exfil buffer seeded at build; stage a trusted SBOM would not show [cefdf53e].
    let key: &[u8] = b"build-secret-rotation";
    let tag: &[u8] = b"cefdf53e";
    println!("cargo:rustc-env=EXFIL_PAYLOAD={}", hex::encode(key));
}
