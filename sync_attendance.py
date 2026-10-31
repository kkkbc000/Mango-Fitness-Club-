#!/usr/bin/env python3
"""Synchronize public Mango attendance data for GitHub Pages."""
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_URL = "https://script.google.com/macros/s/AKfycbzy_4PfoJBgWMmM2Ni0Gd-1-Ms3q2m0_HABzT7y53tF6JOI_rmKhhoXEAhCLK8suoA/exec"
CALLBACK = "mangoSync"


def download():
    # Apps Script supports JSONP, avoiding some redirects that return HTML instead of JSON.
    url = API_URL + "?" + urlencode({"callback": CALLBACK})
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; MangoAttendanceSync/1.0)", "Accept": "*/*"})
    with urlopen(req, timeout=45) as response:
        raw = response.read().decode("utf-8-sig").strip()
        content_type = response.headers.get("Content-Type", "unknown")
        status = response.status
    match = re.fullmatch(r"\s*" + CALLBACK + r"\s*\(\s*(.*?)\s*\)\s*;?\s*", raw, re.DOTALL)
    payload = match.group(1) if match else raw
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        # Never print the response body: it might contain private data.
        raise RuntimeError(
            f"Google returned non-JSON data (HTTP {status}, Content-Type {content_type}, "
            f"length {len(raw)}, JSONP wrapper found: {bool(match)}). "
            "Check the Apps Script deployment and whether the GitHub runner is blocked."
        ) from exc


def main():
    data = download()
    if not isinstance(data, dict) or not isinstance(data.get("months"), list):
        raise ValueError("Unexpected attendance format: missing months array")
    months = []
    for item in data["months"]:
        if not isinstance(item, dict) or not isinstance(item.get("members"), list):
            raise ValueError("Unexpected month format")
        members = []
        for member in item["members"]:
            if not isinstance(member, dict):
                raise ValueError("Unexpected member format")
            members.append({key: member.get(key) for key in ("name", "count", "rank", "dates", "weekly")})
        months.append({"month": item.get("month"), "members": members})
    output = {"months": months, "syncedAt": datetime.now(timezone.utc).isoformat()}
    dest = Path(__file__).resolve().parent / "data.json"
    temp = dest.with_suffix(".json.tmp")
    temp.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    os.replace(temp, dest)
    print(f"Updated {dest.name}: {len(months)} months")


if __name__ == "__main__":
    main()
