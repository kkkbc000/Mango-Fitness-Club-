#!/usr/bin/env python3
"""Sync publicly displayable attendance data from Google Apps Script to GitHub Pages."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

API_URL = "https://script.google.com/macros/s/AKfycbzy_4PfoJBgWMmM2Ni0Gd-1-Ms3q2m0_HABzT7y53tF6JOI_rmKhhoXEAhCLK8suoA/exec"


def main():
    request = Request(API_URL, headers={"User-Agent": "MangoFitnessClubSync/1.0"})
    with urlopen(request, timeout=45) as response:
        data = json.load(response)
    if not isinstance(data, dict) or not isinstance(data.get("months"), list):
        raise ValueError("Unexpected attendance data format; previous data.json is kept.")
    # Guard against publishing an unexpected response containing extra data.
    months = []
    for item in data["months"]:
        if not isinstance(item, dict) or not isinstance(item.get("members"), list):
            raise ValueError("Unexpected month format")
        members = []
        for member in item["members"]:
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
