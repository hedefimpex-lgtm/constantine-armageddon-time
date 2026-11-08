#!/usr/bin/env python3
"""Fetch the publisher's installer with bounded, verified HTTPS ranges."""
import concurrent.futures
import hashlib
import os
from pathlib import Path
import re
import sys
import tempfile
import time
from urllib.request import Request, urlopen

URL = "https://download.istanbuloyun.com/istanbulkur6_0.exe"
CHUNK = 16 * 1024 * 1024


def request(start, end, validator=None):
    headers = {"Range": f"bytes={start}-{end}", "Accept-Encoding": "identity"}
    if validator:
        headers["If-Range"] = validator
    return urlopen(Request(URL, headers=headers), timeout=75)


def download(destination):
    with request(0, 0) as first:
        match = re.fullmatch(r"bytes 0-0/(\d+)", first.headers.get("Content-Range", ""))
        if first.status != 206 or not match or len(first.read(2)) != 1:
            raise ValueError("Kaynak HTTP aralıklarını desteklemiyor")
        size = int(match[1])
        etag = first.headers.get("ETag", "")
        validator = etag if etag and not etag.startswith("W/") else first.headers.get("Last-Modified")
        if not validator or not 0 < size <= 2*1024**3:
            raise ValueError("Kaynak doğrulayıcısı veya boyutu geçersiz")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as folder:
        temp = Path(folder) / "installer.part"
        fd = os.open(temp, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600)
        def fetch_part(start):
            end = min(start + CHUNK, size) - 1
            for attempt in range(3):
                try:
                    with request(start, end, validator) as resp:
                        expected = f"bytes {start}-{end}/{size}"
                        if resp.status != 206 or resp.headers.get("Content-Range") != expected:
                            raise ValueError("Kurulum sürümü veya aralık değişti")
                        data = resp.read(end - start + 2)
                    if len(data) != end-start+1 or os.pwrite(fd, data, start) != len(data):
                        raise OSError("Eksik parça")
                    return len(data)
                except OSError:
                    if attempt == 2:
                        raise
                    time.sleep(2**attempt)
        try:
            os.ftruncate(fd, size)
            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as workers:
                done = 0
                for length in workers.map(fetch_part,range(0,size,CHUNK)):
                    done += length
                    if done == size or done % (CHUNK*10) == 0:
                        print(f"{done}/{size} bytes", flush=True)
        finally:
            os.close(fd)
        with temp.open("rb") as src:
            print("SHA-256",hashlib.file_digest(src,"sha256").hexdigest(),flush=True)
        temp.replace(destination)


if __name__ == "__main__":
    download(Path(sys.argv[1]))
