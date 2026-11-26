#!/usr/bin/env python3
"""Minimal pcap reader + RTPS submessage decoder (standard library only, no tshark needed).

Reads .pcap and .pcap.gz (Ethernet or Linux cooked capture) and decodes RTPS
submessages: INFO_DST, INFO_TS, DATA, DATA_FRAG, HEARTBEAT, ACKNACK, NACK_FRAG,
and the Fast DDS statistics submessage (0x80).

Usage (from the repository root):
  python3 ros2_lyrical/tools/rtps_peek.py frame     <pcap> <frame-no>   hex dump + decoded RTPS of one frame
  python3 ros2_lyrical/tools/rtps_peek.py sms       <pcap> <NAME...>    every submessage of the given kinds
                                                                      e.g. NACK_FRAG DATA_FRAG HEARTBEAT
  python3 ros2_lyrical/tools/rtps_peek.py strings   <pcap> <frame-no>   printable strings (SPDP properties)
  python3 ros2_lyrical/tools/rtps_peek.py fragcount <pcap>              IP fragments per UDP datagram

Frame numbers are 1-based, as in Wireshark. Only the first IP fragment of a datagram
is decoded, which is enough for RTPS headers and DATA_FRAG/NACK_FRAG fields.
"""
import gzip, struct, sys

def frames(path):
    f = (gzip.open if path.endswith('.gz') else open)(path, 'rb')
    data = f.read()
    end = '<' if data[:4] == b'\xd4\xc3\xb2\xa1' else '>'
    link = struct.unpack(end + 'I', data[20:24])[0]
    off, n = 24, 0
    while off + 16 <= len(data):
        ts, tu, incl, orig = struct.unpack(end + 'IIII', data[off:off + 16])
        n += 1
        pkt = data[off + 16:off + 16 + incl]
        off += 16 + incl
        if link == 113:            # Linux cooked (tcpdump -i any)
            pkt = b'\x00' * 12 + pkt[14:16] + pkt[16:]
        yield n, ts + tu / 1e6, pkt

def ip_udp(pkt):
    if pkt[12:14] != b'\x08\x00':
        return None
    ip = pkt[14:]
    ihl = (ip[0] & 15) * 4
    proto = ip[9]
    fo = struct.unpack('>H', ip[6:8])[0]
    mf, foff = bool(fo & 0x2000), (fo & 0x1fff) * 8
    src, dst = '.'.join(map(str, ip[12:16])), '.'.join(map(str, ip[16:20]))
    return dict(proto=proto, src=src, dst=dst, mf=mf, foff=foff, l4=ip[ihl:], id=struct.unpack('>H', ip[4:6])[0])

SM = {0x01: 'PAD', 0x06: 'ACKNACK', 0x07: 'HEARTBEAT', 0x08: 'GAP', 0x09: 'INFO_TS', 0x0c: 'INFO_SRC',
      0x0e: 'INFO_DST', 0x12: 'NACK_FRAG', 0x13: 'HEARTBEAT_FRAG', 0x15: 'DATA', 0x16: 'DATA_FRAG', 0x80: 'FASTDDS_STATISTICS'}

def eid(b): return '.'.join(f'{x:02x}' for x in b)

def sn(b, e): hi, lo = struct.unpack(e + 'iI', b); return (hi << 32) | lo

def rtps(payload, maxlen=None):
    if payload[:4] != b'RTPS':
        return None
    out = [f'RTPS v{payload[4]}.{payload[5]} vendor {payload[6]:02x}.{payload[7]:02x} guidPrefix {payload[8:20].hex(" ")}']
    p = 20
    while p + 4 <= len(payload):
        sid, fl, ln = payload[p], payload[p + 1], None
        e = '<' if fl & 1 else '>'
        ln = struct.unpack(e + 'H', payload[p + 2:p + 4])[0]
        body = payload[p + 4:p + 4 + ln] if ln else payload[p + 4:]
        name = SM.get(sid, f'0x{sid:02x}')
        d = ''
        if sid == 0x15:
            otq = struct.unpack(e + 'H', body[2:4])[0]
            d = f'reader {eid(body[4:8])} writer {eid(body[8:12])} SN {sn(body[12:20], e)}'
            pl = body[4 + otq:]
            d += f' | payload {len(pl)} B: encap {pl[:2].hex()} {pl[4:40]!r}'
        elif sid == 0x16:
            d = (f'reader {eid(body[4:8])} writer {eid(body[8:12])} SN {sn(body[12:20], e)} '
                 f'fragStart {struct.unpack(e+"I", body[20:24])[0]} inSub {struct.unpack(e+"H", body[24:26])[0]} '
                 f'fragSize {struct.unpack(e+"H", body[26:28])[0]} sampleSize {struct.unpack(e+"I", body[28:32])[0]}')
        elif sid == 0x12:
            base, nb = struct.unpack(e + 'II', body[16:24])
            bm = body[24:24 + 4 * ((nb + 31) // 32)]
            words = [struct.unpack(e + 'I', bm[i:i + 4])[0] for i in range(0, len(bm), 4)]
            missing = [base + i for i in range(nb) if words[i // 32] >> (31 - i % 32) & 1]
            d = f'writer {eid(body[4:8])} SN {sn(body[8:16], e)} bitmapBase {base} numBits {nb} -> ขอ fragment {missing}'
        elif sid == 0x07:
            d = f'writer {eid(body[4:8])} firstSN {sn(body[8:16], e)} lastSN {sn(body[16:24], e)}'
        elif sid == 0x09:
            s, fr = struct.unpack(e + 'iI', body[:8]); d = f'time {s}.{fr * 1e9 / 2**32:09.0f}'
        elif sid == 0x0e:
            d = f'dst guidPrefix {body[:12].hex(" ")}'
        out.append(f'  [{p:3d}] {name:<18} flags 0x{fl:02x} len {ln:<5} {d}')
        if ln == 0:
            break
        p += 4 + ln
    return out

def hexdump(b):
    for i in range(0, len(b), 16):
        ch = b[i:i + 16]
        print(f'  {i:04x}  {ch.hex(" "):<47}  {"".join(chr(c) if 32 <= c < 127 else "." for c in ch)}')

def strings(b, minlen=4):
    cur, res = b'', []
    for c in b:
        if 32 <= c < 127: cur += bytes([c])
        else:
            if len(cur) >= minlen: res.append(cur.decode())
            cur = b''
    return res

if len(sys.argv) < 3:
    sys.exit(__doc__)
cmd, path = sys.argv[1], sys.argv[2]
arg = sys.argv[3:]
if cmd == 'frame':
    want = int(arg[0])
    for n, t, pkt in frames(path):
        if n == want:
            print(f'frame {n}: {len(pkt)} B'); hexdump(pkt)
            iu = ip_udp(pkt)
            if iu and iu['proto'] == 17:
                for l in rtps(iu['l4'][8:]) or []: print(l)
elif cmd == 'strings':
    want = int(arg[0])
    for n, t, pkt in frames(path):
        if n == want: print(strings(pkt))
elif cmd == 'sms':     # summarize RTPS submessages of interest
    kinds = set(arg)
    for n, t, pkt in frames(path):
        iu = ip_udp(pkt)
        if not iu or iu['proto'] != 17 or iu['foff'] != 0: continue
        r = rtps(iu['l4'][8:])
        if r and any(k in l for k in kinds for l in r[1:]):
            print(f'frame {n} {t:.6f} {iu["src"]} -> {iu["dst"]} ip.id {iu["id"]} MF={iu["mf"]}')
            for l in r[1:]:
                if any(k in l for k in kinds): print(l)
elif cmd == 'fragcount':
    from collections import Counter
    c = Counter()
    for n, t, pkt in frames(path):
        iu = ip_udp(pkt)
        if iu and iu['proto'] == 17: c[iu['id'], iu['src']] += 1
    big = {k: v for k, v in c.items() if v > 1}
    print('datagrams ที่ถูก IP fragment:', len(big), '· fragment ต่อ datagram:', Counter(big.values()))
