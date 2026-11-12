"""Generated RE:LAND category cover assets must be real and unique."""
from pathlib import Path
import hashlib
from PIL import Image


def test_nine_category_images_are_present_and_distinct():
    root=Path(__file__).resolve().parents[1]/"static/assets/boards"
    files=[root/f"cover-{i:02d}.jpg" for i in range(1,10)]
    assert all(x.is_file() for x in files), [str(x) for x in files if not x.is_file()]
    digests=set()
    for image in files:
        assert image.stat().st_size > 6000
        with Image.open(image) as img:
            assert img.format=="JPEG"
            assert img.width >= 200 and img.height >= 130
            assert img.getbbox() is not None
        digests.add(hashlib.sha256(image.read_bytes()).hexdigest())
    assert len(digests) == 9
