"""RE:LAND journal protected presentation media.

Never mutates original column artwork. The branded response is a generated
representation of original project media, not evidence of copyright title.
"""
from functools import lru_cache
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, Response
from PIL import Image, ImageOps


def install_journal_media(app, root: Path) -> None:
    root = Path(root)
    sources = root / 'static' / 'assets' / 'columns'
    watermark = root / 'static' / 'assets' / 'journal-watermark-overlay-v6.png'

    @lru_cache(maxsize=50)
    def branded_image(article_id: int) -> bytes:
        path = sources / f'column-{article_id:03d}.webp'
        if not path.is_file() or not watermark.is_file():
            raise FileNotFoundError(f'Journal image or branding asset missing: {article_id}')
        with Image.open(path) as f:
            art = ImageOps.exif_transpose(f).convert('RGBA')
        with Image.open(watermark) as w:
            if w.size != art.size:
                mark = w.convert('RGBA').resize(art.size, Image.Resampling.LANCZOS)
            else:
                mark = w.convert('RGBA')
        output = Image.alpha_composite(art, mark).convert('RGB')
        buffer = BytesIO()
        output.save(buffer, format='WEBP', quality=88, method=5)
        return buffer.getvalue()

    @app.get('/journal-image/{article_id}.webp', include_in_schema=False)
    def journal_image(article_id: int):
        if article_id < 1 or article_id > 120:
            raise HTTPException(status_code=404, detail='저널 이미지를 찾을 수 없습니다.')
        try:
            result = branded_image(article_id)
        except (FileNotFoundError, OSError, ValueError) as exc:
            raise HTTPException(status_code=404, detail='저널 이미지가 준비되지 않았습니다.') from exc
        return Response(
            content=result, media_type='image/webp',
            headers={
                'Cache-Control': 'public, max-age=86400, immutable',
                'X-Content-Type-Options': 'nosniff',
                'Content-Disposition': f'inline; filename="RELAND-JOURNAL-{article_id:03d}.webp"',
            },
        )
