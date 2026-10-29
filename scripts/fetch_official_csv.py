"""Download MOLIT urban renewal CSV from data.go.kr (15160169)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import httpx

PAGE = "https://www.data.go.kr/data/15160169/fileData.do"
OUT = Path(__file__).resolve().parents[1] / "data" / "molit_urban_renewal_official.csv"


def main() -> int:
    headers = {"User-Agent": "RE-LAND/3.0 (+https://reland.lexid.site)"}
    with httpx.Client(headers=headers, follow_redirects=True, timeout=120) as client:
        html = client.get(PAGE).text
        links = re.findall(r"(/cmm/cmm/fileDownload\.do\?[^\"'<>\\s]+)", html)
        if not links:
            print("No fileDownload links in page HTML", file=sys.stderr)
            return 1
        # Prefer CSV attachment (usually first file download)
        url = "https://www.data.go.kr" + links[0]
        print("GET", url)
        resp = client.get(url)
        resp.raise_for_status()
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_bytes(resp.content)
        print("saved", OUT, "bytes", len(resp.content))
        preview = OUT.read_bytes()[:200]
        print("head", preview[:80])
    return 0 if OUT.stat().st_size > 1000 else 1


if __name__ == "__main__":
    raise SystemExit(main())
