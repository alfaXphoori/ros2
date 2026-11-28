#!/usr/bin/env python3
"""Byte-level helper for run_container_ipc.sh (exp14, docs/03 §5.2). Stdlib only.

usage: ipc_shm_locators.py <pcap>...
Prints, per pcap, (1) every distinct 24-byte SHM locator (kind 0x13 = Fast DDS SHM) found in
PID_DEFAULT_UNICAST_LOCATOR (pid 0x0031) / PID_METATRAFFIC_UNICAST_LOCATOR (0x0032) parameters and
(2) the first 4 bytes of every distinct RTPS guidPrefix (Fast DDS: vendor 01.0f + 2-byte host id).
The pcaps are scanned as raw bytes, so any link type works.
"""
import sys

PIDS = {b"\x31\x00\x18\x00": "DEFAULT_UNICAST", b"\x32\x00\x18\x00": "METATRAFFIC_UNICAST"}
KIND = b"\x13\x00\x00\x00"

for path in sys.argv[1:]:
    data = open(path, "rb").read()
    locs, prefixes = set(), set()
    for pid, pname in PIDS.items():
        i = data.find(pid + KIND)
        while i >= 0:
            body = data[i + 8:i + 28]
            port = int.from_bytes(body[0:4], "little")
            locs.add((pname, port, body[4:].hex(" ")))
            i = data.find(pid + KIND, i + 1)
    i = data.find(b"RTPS")
    while i >= 0:
        gp = data[i + 8:i + 20]
        if len(gp) == 12:
            prefixes.add(gp[:4].hex("."))
        i = data.find(b"RTPS", i + 1)
    print(f"# {path.rsplit('/', 1)[-1]}")
    for pname, port, addr in sorted(locs):
        print(f"shm_locator {pname} port {port} address {addr}")
    print("guidPrefix[0:4] seen:", " ".join(sorted(prefixes)) or "-")
