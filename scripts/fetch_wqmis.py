"""Fetch official JJM/WQMIS WQ6 data for Uttar Pradesh."""

import csv
import json
from base64 import b64encode
from datetime import date
from pathlib import Path

import requests
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


BASE = "https://ejalshakti.gov.in/WQMIS"
STATE_ID = "31"
STATE_NAME = "up"


def current_financial_year():
    """Return current Indian financial year as YYYY-YYYY."""
    today = date.today()

    if today.month >= 4:
        start_year = today.year
    else:
        start_year = today.year - 1

    return f"{start_year}-{start_year + 1}"


def encrypted_aes(value):
    """Match the encryption used by the WQMIS web application."""
    key = b"8080808080808080"
    iv = b"8080808080808080"

    padder = padding.PKCS7(128).padder()
    data = padder.update(str(value).encode()) + padder.finalize()

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()

    encrypted = (
        encryptor.update(data)
        + encryptor.finalize()
    )

    return b64encode(encrypted).decode()


def fetch_wqmis(fy):
    """Fetch state-level WQ6 data for Uttar Pradesh."""
    session = requests.Session()

    session.get(
        f"{BASE}/Report/Contaminantwise",
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=(5, 60),
    )

    params = {
        "cpage": encrypted_aes("1"),
        "st": encrypted_aes(STATE_ID),
        "dt": encrypted_aes("0"),
        "bl": encrypted_aes("0"),
        "gp": encrypted_aes("0"),
        "vill": encrypted_aes("0"),
        "fy": encrypted_aes(fy),
        "IsPws": encrypted_aes("1"),
        "SchemeId": encrypted_aes("0"),
        "SampleType": encrypted_aes("0"),
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": f"{BASE}/Report/Contaminantwise",
        "X-Requested-With": "XMLHttpRequest",
    }

    response = session.get(
        f"{BASE}/Report/GetContaminantwiseData",
        params=params,
        headers=headers,
        timeout=(5, 60),
    )

    response.raise_for_status()

    return response.json()


def save_data(data, fy):
    """Save raw JSON and a flat CSV copy."""
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    suffix = fy.replace("-", "_")

    json_path = output_dir / f"wqmis_up_{suffix}.json"
    csv_path = output_dir / f"wqmis_up_{suffix}.csv"

    json_path.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )

    rows = data.get("Contaminantwise", [])

    if not rows:
        raise ValueError("WQMIS returned no Contaminantwise rows.")

    fields = list(rows[0].keys())

    with csv_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fields,
        )
        writer.writeheader()
        writer.writerows(rows)

    return json_path, csv_path, len(rows)


if __name__ == "__main__":
    fy = current_financial_year()

    print("Financial Year:", fy)
    print("State:", STATE_NAME.upper())
    print("Fetching WQ6 data...")

    data = fetch_wqmis(fy)

    json_path, csv_path, count = save_data(data, fy)

    print("Rows:", count)
    print("JSON:", json_path)
    print("CSV:", csv_path)
    print("WQ6 fetch completed successfully.")
