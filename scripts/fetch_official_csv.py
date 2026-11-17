"""Fetch the unrestricted MOLIT 2026 urban-renewal CSV without an API key.

Safeguards:
- uses the published data.go.kr download flow, not an undocumented login bypass;
- never silently overwrites a previously downloaded source;
- validates columns, record count, encoding, and reports same-name collisions;
- does not geocode, assume distinct identical names are one project, or alter DB.

Usage: python scripts/fetch_official_csv.py
       python scripts/fetch_official_csv.py --out data/new_molit_snapshot_YYYYMMDD.csv
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
from pathlib import Path

import httpx

PAGE = "https://www.data.go.kr/data/15160169/fileData.do"
BASE = "https://www.data.go.kr"
DETAIL_PK = "uddi:4d7f16a9-b0fd-4d07-b266-d0ad82aeaf34"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "data" / "molit_urban_renewal_official_20260518.csv"
HEADERS = [
    "시도", "시군구", "구역명칭", "현 사업추진단계",
    "사업유형", "사업시행자", "공급 예정 세대수",
]


def fetch_bytes() -> bytes:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; RE-LAND official-data-check/1.0)",
        "Referer": PAGE,
        "X-Requested-With": "XMLHttpRequest",
    }
    with httpx.Client(headers=headers, follow_redirects=True, timeout=35) as client:
        landing = client.get(PAGE)
        landing.raise_for_status()
        if "15160169" not in landing.text:
            raise ValueError("공식 데이터셋 페이지를 확인할 수 없습니다.")
        response = client.post(
            BASE + "/tcs/dss/selectFileDataDownload.do",
            data={
                "publicDataDetailPk": DETAIL_PK,
                "publicDataPk": "15160169",
                "atchFileId": "",
                "fileDetailSn": "1",
                "publicDataTyCode": "PR0051",
            },
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("status") is not True or not payload.get("atchFileId"):
            raise ValueError("공식 다운로드 파일 식별자 조회 실패")
        atch_id = payload["atchFileId"]
        file_sn = str(payload["fileDetailSn"])
        source_name = payload["dataSetFileDetailInfo"]["dataNm"]
        limit = client.post(BASE + "/cmm/cmm/check-limit.json",
                            data={"atchFileId": atch_id, "fileDetailSn": file_sn})
        limit.raise_for_status()
        if limit.json().get("needCaptcha"):
            raise RuntimeError("공식 사이트 CAPTCHA 필요: 브라우저에서 직접 다운로드해야 합니다.")
        file_response = client.get(
            BASE + "/cmm/cmm/fileDownload.do",
            params={"atchFileId": atch_id, "fileDetailSn": file_sn, "dataNm": source_name},
        )
        file_response.raise_for_status()
        if "html" in file_response.headers.get("content-type", "").lower():
            raise ValueError("원본 CSV 대신 HTML이 반환됐습니다.")
        return file_response.content


def analyze(raw: bytes) -> dict:
    if len(raw) < 20000:
        raise ValueError("다운로드 파일이 정상 CSV로 보기에는 너무 작습니다.")
    text = None
    for enc in ("cp949", "utf-8-sig", "euc-kr"):
        try:
            sample = raw.decode(enc)
            if sample.startswith("시도,") or sample.startswith("\ufeff시도,"):
                text = sample
                break
        except UnicodeError:
            continue
    if text is None:
        raise ValueError("공식 CSV 인코딩 또는 헤더가 예상과 다릅니다.")
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames != HEADERS:
        raise ValueError(f"예상하지 못한 CSV 헤더: {reader.fieldnames}")
    seen = {}
    rows = 0
    for row in reader:
        key = tuple(str(row[k]).strip() for k in ("시도", "시군구", "구역명칭"))
        if not all(key):
            raise ValueError("빈 정비구역 식별 키가 존재합니다.")
        seen[key] = seen.get(key, 0) + 1
        rows += 1
    if rows < 1000:
        raise ValueError(f"전체 사업 데이터로 보기에는 행 수가 부족합니다: {rows}")
    overlaps = [v for v in seen.values() if v > 1]
    return {
        "source_url": PAGE,
        "rows": rows,
        "distinct_location_name_keys": len(seen),
        "same_name_groups": len(overlaps),
        "extra_same_name_rows": sum(v - 1 for v in overlaps),
        "size_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="국토교통부 정비사업 공식 원본 다운로드·검증")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--check-only", action="store_true", help="다운로드·검증만 진행")
    args = parser.parse_args()
    raw = fetch_bytes()
    report = analyze(raw)
    print(report)
    if args.check_only:
        return
    out = args.out.expanduser().resolve()
    if out.is_file():
        original_hash = hashlib.sha256(out.read_bytes()).hexdigest()
        if original_hash == report["sha256"]:
            print("파일 내용 동일: 중복 저장하지 않음", out)
            return
        raise FileExistsError(f"기존 파일은 보존합니다. 새 이름을 --out으로 지정하세요: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(raw)
    print("saved", out)


if __name__ == "__main__":
    main()
