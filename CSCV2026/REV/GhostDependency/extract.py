import zstandard, tarfile, io
with open('extracted/handout/registry.tar.zst', 'rb') as f:
    data = zstandard.ZstdDecompressor().decompress(f.read())
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        tar.extractall('extracted/registry')
