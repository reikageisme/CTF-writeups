from pathlib import Path
import io
import tarfile

import zstandard


ROOT = Path(__file__).resolve().parent
ARCHIVE_CANDIDATES = (
    ROOT / "handout" / "registry.tar.zst",
    ROOT / "extracted" / "handout" / "registry.tar.zst",
)
archive = next((path for path in ARCHIVE_CANDIDATES if path.is_file()), None)
if archive is None:
    raise FileNotFoundError(
        "Unpack download.zip first; expected handout/registry.tar.zst"
    )

data = zstandard.ZstdDecompressor().decompress(archive.read_bytes())
output = ROOT / "extracted" / "registry"
output.mkdir(parents=True, exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(data)) as tar:
    tar.extractall(output)
print(f"Extracted registry members to {output}")
