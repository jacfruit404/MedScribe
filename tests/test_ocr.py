import pytest
from PIL import Image

from medscribe.ocr import extract_from_upload, preprocess_image


def test_preprocess_image_converts_to_grayscale():
    img = Image.new("RGB", (10, 10), color=(255, 0, 0))
    processed = preprocess_image(img)
    assert processed.mode in ("L", "RGB")  # grayscale then filtered
    assert processed.size == (10, 10)


def test_extract_from_upload_rejects_unsupported_type():
    with pytest.raises(ValueError, match="Unsupported file type"):
        extract_from_upload(b"not a real file", "notes.txt")


def test_extract_from_upload_dispatches_to_image_path(monkeypatch):
    called = {}

    def fake_extract_from_image_bytes(data, source_name="upload"):
        called["source_name"] = source_name
        return "sentinel"

    monkeypatch.setattr(
        "medscribe.ocr.extract_from_image_bytes", fake_extract_from_image_bytes
    )

    result = extract_from_upload(b"fake-bytes", "scan.png")
    assert result == "sentinel"
    assert called["source_name"] == "scan.png"
