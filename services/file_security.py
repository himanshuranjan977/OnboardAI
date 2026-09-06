import hashlib

MAGIC={
    ".pdf": [b"%PDF"],
    ".png": [b"\x89PNG\r\n\x1a\n"],
    ".jpg": [b"\xff\xd8\xff"],
    ".jpeg": [b"\xff\xd8\xff"],
    ".webp": [b"RIFF"],
    ".tif": [b"II*\x00", b"MM\x00*"],
    ".tiff": [b"II*\x00", b"MM\x00*"],
}

def validate_signature(extension, content):
    signatures=MAGIC.get(extension.lower())
    if not signatures: return False
    return any(content.startswith(sig) for sig in signatures)

def sha256(content):
    return hashlib.sha256(content).hexdigest()
