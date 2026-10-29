from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(r"C:/Users/user/.cursor/projects/e-currsor-C-blog/assets")

pairs = [
    (SRC / "reland-hero-city.jpg", ROOT / "static/assets/reland-hero-city.webp", 88),
    (SRC / "legal-office-premium.jpg", ROOT / "static/assets/legal-office-source.webp", 85),
    (SRC / "community-neighborhood.jpg", ROOT / "static/assets/community-neighborhood.webp", 85),
    (SRC / "kang-studio-hero.jpg", ROOT / "kang_blog/assets/office.webp", 85),
    (SRC / "kang-studio-hero.jpg", ROOT / "kang_blog/assets/hero-bg.webp", 82),
]

for inp, out, q in pairs:
    im = Image.open(inp).convert("RGB")
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, "WEBP", quality=q, method=6)
    print(out.relative_to(ROOT), im.size)
