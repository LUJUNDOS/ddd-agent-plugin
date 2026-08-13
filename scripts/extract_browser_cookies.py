#!/usr/bin/env python3
"""Extract cookies from Chrome/Edge local SQLite DB.

Supports Chrome/Edge >= v80 (AES-256-GCM via Local State key) and older (raw DPAPI).
Windows only — uses DPAPI via ctypes + cryptography for AES-GCM.

Usage:
    python extract_browser_cookies.py --domain douyin.com --out cookies.txt
    python extract_browser_cookies.py --domain douyin.com --out cookies.txt --format netscape
"""

import sqlite3
import os
import sys
import json
import base64
import argparse
import ctypes
import ctypes.wintypes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


# ── Windows DPAPI (for decrypting the AES master key) ─────────────────────
class DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", ctypes.wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_char)),
    ]

crypt32 = ctypes.windll.crypt32
crypt32.CryptUnprotectData.argtypes = [
    ctypes.POINTER(DATA_BLOB),           # pDataIn
    ctypes.POINTER(ctypes.c_wchar_p),    # ppszDataDescr
    ctypes.POINTER(DATA_BLOB),           # pOptionalEntropy
    ctypes.c_void_p,                     # pvReserved
    ctypes.c_void_p,                     # pPromptStruct
    ctypes.c_uint32,                     # dwFlags
    ctypes.POINTER(DATA_BLOB),           # pDataOut
]
crypt32.CryptUnprotectData.restype = ctypes.c_bool


def dpapi_decrypt(data: bytes) -> bytes | None:
    """Decrypt DPAPI-encrypted blob (used for master key and legacy cookies)."""
    if not data:
        return None
    buf = (ctypes.c_char * len(data)).from_buffer_copy(data)
    blob_in = DATA_BLOB(len(data), buf)
    blob_out = DATA_BLOB(0, None)
    if crypt32.CryptUnprotectData(
        ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)
    ):
        result = ctypes.string_at(blob_out.pbData, blob_out.cbData)
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)
        return result
    return None


# ── AES master key from Local State ───────────────────────────────────────
def get_aes_key(user_data_dir: str) -> bytes | None:
    """Read the AES-256 master key from Local State (Chrome/Edge v80+)."""
    local_state = os.path.join(user_data_dir, "Local State")
    if not os.path.exists(local_state):
        return None
    
    try:
        with open(local_state, "r", encoding="utf-8") as f:
            state = json.load(f)
    except Exception:
        return None
    
    enc_key_b64 = state.get("os_crypt", {}).get("encrypted_key")
    if not enc_key_b64:
        return None
    
    enc_key = base64.b64decode(enc_key_b64)
    # Strip "DPAPI" prefix (5 bytes)
    if enc_key[:5] == b"DPAPI":
        enc_key = enc_key[5:]
    
    return dpapi_decrypt(enc_key)


# ── Cookie value decryption ────────────────────────────────────────────────
def decrypt_cookie(encrypted: bytes, aes_key: bytes | None) -> str | None:
    """Decrypt a Chrome/Edge cookie value.
    
    - v10/v11 prefix (3 bytes): AES-256-GCM. First 12 bytes after prefix = nonce,
      remaining = ciphertext (last 16 bytes = auth tag).
    - v20 prefix: AES-256-GCM but different IV derivation (not yet common).
    - No prefix / raw: legacy DPAPI.
    """
    if not encrypted:
        return ""
    
    # AES-256-GCM (v10/v11, Chrome/Edge >= v80)
    if encrypted[:3] == b"v10" or encrypted[:3] == b"v11":
        if not aes_key:
            return None
        payload = encrypted[3:]
        nonce = payload[:12]
        ciphertext = payload[12:]
        try:
            aesgcm = AESGCM(aes_key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode("utf-8", errors="replace")
        except Exception:
            return None
    
    # AES-256-GCM (v20, Chromium >= ~130, different IV derivation)
    if encrypted[:3] == b"v20":
        # v20 uses SHA-256 hash of the domain for IV — not implemented yet
        if not aes_key:
            return None
        payload = encrypted[3:]
        nonce = payload[:12]
        ciphertext = payload[12:]
        try:
            aesgcm = AESGCM(aes_key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode("utf-8", errors="replace")
        except Exception:
            return None
    
    # Legacy DPAPI (Chrome < v80)
    result = dpapi_decrypt(encrypted)
    if result:
        return result.decode("utf-8", errors="replace")
    
    return None


# ── Browser discovery ─────────────────────────────────────────────────────
BROWSERS = [
    ("Chrome", os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")),
    ("Edge",   os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data")),
]


def find_profiles(user_data_dir: str) -> list[tuple[str, str, str]]:
    """Returns [(label, profile_dir, user_data_dir), ...]."""
    results = []
    if not os.path.isdir(user_data_dir):
        return results
    for entry in os.listdir(user_data_dir):
        prof_dir = os.path.join(user_data_dir, entry)
        if not os.path.isdir(prof_dir):
            continue
        if entry != "Default" and not entry.startswith("Profile "):
            continue
        db = os.path.join(prof_dir, "Network", "Cookies")
        if os.path.exists(db):
            results.append((entry, prof_dir, user_data_dir))
    return results


# ── Extraction loop ────────────────────────────────────────────────────────
def extract_cookies(domain: str, verbose: bool = True) -> dict[str, str]:
    """Extract all cookies for a domain from all browser profiles."""
    all_cookies: dict[str, str] = {}

    for browser_name, user_data_dir in BROWSERS:
        profiles = find_profiles(user_data_dir)
        if not profiles:
            continue
        
        aes_key = get_aes_key(user_data_dir)
        
        for prof_name, prof_dir, _ in profiles:
            db_path = os.path.join(prof_dir, "Network", "Cookies")
            abs_path = os.path.abspath(db_path).replace("\\", "/")
            
            try:
                conn = sqlite3.connect(f"file:{abs_path}?mode=ro", uri=True, timeout=1)
                cur = conn.cursor()
                cur.execute(
                    "SELECT host_key, name, encrypted_value FROM cookies "
                    "WHERE host_key LIKE ?",
                    (f"%{domain}%",)
                )
                rows = cur.fetchall()
                conn.close()
            except Exception as e:
                if verbose:
                    print(f"  [{browser_name}/{prof_name}] Cannot read: {e}", file=sys.stderr)
                continue
            
            if not rows:
                continue
            
            label = f"{browser_name}/{prof_name}"
            if verbose:
                print(f"[FOUND] {label}: {len(rows)} cookies")
            
            for host, name, enc in rows:
                val = decrypt_cookie(enc, aes_key)
                if val:
                    all_cookies[name] = val
                    if verbose:
                        print(f"  {name} = {val[:60]}{'...' if len(val) > 60 else ''}")
                elif verbose:
                    print(f"  {name} = (decrypt failed)", file=sys.stderr)
    
    return all_cookies


# ── Output formatting ──────────────────────────────────────────────────────
def format_keyvalue(cookies: dict[str, str]) -> str:
    return "; ".join(f"{k}={v}" for k, v in cookies.items())


def format_netscape(cookies: dict[str, str], domain: str) -> str:
    lines = ["# Netscape HTTP Cookie File"]
    for name, value in cookies.items():
        lines.append(f"{domain}\tTRUE\t/\tTRUE\t0\t{name}\t{value}")
    return "\n".join(lines)


# ── Main ───────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Extract Chrome/Edge cookies (DPAPI + AES-GCM)")
    parser.add_argument("--domain", required=True, help="Domain (e.g. douyin.com)")
    parser.add_argument("--out", required=True, help="Output file")
    parser.add_argument("--format", choices=["keyvalue", "netscape"], default="keyvalue")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress per-cookie output")
    args = parser.parse_args()

    cookies = extract_cookies(args.domain, verbose=not args.quiet)

    if not cookies:
        print(f"\n[FAIL] No {args.domain} cookies found.", file=sys.stderr)
        print("Ensure you're logged in and the browser is CLOSED.", file=sys.stderr)
        sys.exit(1)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    
    if args.format == "netscape":
        content = format_netscape(cookies, args.domain)
    else:
        content = format_keyvalue(cookies)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\n[DONE] {len(cookies)} cookies → {args.out} ({len(content)} chars)")


if __name__ == "__main__":
    main()
