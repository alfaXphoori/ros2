#!/usr/bin/env python3
"""Minimal pcap reader + RTPS submessage decoder (standard library only, no tshark needed).

Reads .pcap and .pcap.gz with link type Ethernet (1) or Linux cooked capture
v1 (113) / v2 (276, what `tcpdump -i any` writes on newer libpcap); cooked frames are
shown with a 14-byte pseudo-Ethernet header. Other link types get a warning on stderr.
Decodes RTPS submessages: INFO_DST, INFO_TS, DATA, DATA_FRAG, HEARTBEAT, ACKNACK, NACK_FRAG,
GAP (ACKNACK/GAP details with -v), the Fast DDS statistics submessage (0x80), and SPDP/SEDP
ParameterLists (params/sedp).

Usage (from the repository root):
  python3 ros2_lyrical/tools/rtps_peek.py frame     <pcap> <frame-no>   hex dump + decoded RTPS of one frame
  python3 ros2_lyrical/tools/rtps_peek.py sms       <pcap> <NAME...>    every submessage of the given kinds
                                                                      e.g. NACK_FRAG DATA_FRAG HEARTBEAT
                                                                      (exact name: DATA does not match DATA_FRAG)
  python3 ros2_lyrical/tools/rtps_peek.py strings   <pcap> <frame-no>   printable strings (SPDP properties)
  python3 ros2_lyrical/tools/rtps_peek.py fragcount <pcap>              IP fragments per UDP datagram
  python3 ros2_lyrical/tools/rtps_peek.py params    <pcap> <frame-no>   ParameterList of every DATA in the datagram
                                                                      completed by this frame (IP fragments reassembled)
                                                                      (SPDP/SEDP, inline QoS) with QoS PIDs decoded
  python3 ros2_lyrical/tools/rtps_peek.py sedp      <pcap>              one line per SEDP DATA(w)/DATA(r): endpoint,
                                                                      topic, type and the QoS PIDs present
  python3 ros2_lyrical/tools/rtps_peek.py stats     <pcap>              per writer: DATA SNs, HEARTBEAT, GAP; ACKNACK

Option -v (anywhere on the command line) adds detail to `frame` and `sms`: HEARTBEAT reader,
count and flags F/L; ACKNACK readerSNState (base, bitmap -> requested SNs), count, flag F;
GAP gapStart + gapList (-> irrelevant SNs); DATA flags Q/D/K with inline QoS skipped. Without -v
the output of frame/sms/strings/fragcount is unchanged from earlier versions (docs quote it).
Duration_t values are printed as seconds + fraction (RTPS 2.x Time_t layout, fraction/2^32 s).

Frame numbers are 1-based, as in Wireshark. frame/sms decode only the first IP fragment of a
datagram, which is enough for RTPS headers and DATA_FRAG/NACK_FRAG fields; params/sedp/stats
reassemble IP fragments first (SEDP messages with several DATA(w) are often > 1 MTU).
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
        if link == 113:            # Linux cooked v1 (SLL): protocol at bytes 14-15, 16-byte header
            pkt = b'\x00' * 12 + pkt[14:16] + pkt[16:]
        elif link == 276:          # Linux cooked v2 (SLL2): protocol at bytes 0-1, 20-byte header
            pkt = b'\x00' * 12 + pkt[0:2] + pkt[20:]
        elif link != 1 and n == 1:
            print(f'warning: unsupported pcap link type {link}, treating frames as Ethernet '
                  '(RTPS will probably not be decoded)', file=sys.stderr)
        yield n, ts + tu / 1e6, pkt

def ip_udp(pkt):
    if pkt[12:14] != b'\x08\x00' or len(pkt) < 34:
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

def snset(body, off, e):
    """SequenceNumberSet at body[off:]: returns (base, numBits, [SNs with bit set], offset after the set)."""
    base = sn(body[off:off + 8], e)
    nb = struct.unpack(e + 'I', body[off + 8:off + 12])[0]
    nw = (nb + 31) // 32
    words = [struct.unpack(e + 'I', body[off + 12 + 4 * i:off + 16 + 4 * i])[0] for i in range(nw)]
    return base, nb, [base + i for i in range(nb) if words[i // 32] >> (31 - i % 32) & 1], off + 12 + 4 * nw

def fmt_sns(s):
    """[1,2,3,5] -> '1..3,5' (compact list of sequence numbers)."""
    out, i = [], 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and s[j + 1] == s[j] + 1: j += 1
        out.append(f'{s[i]}..{s[j]}' if j > i else f'{s[i]}')
        i = j + 1
    return '[' + ','.join(out) + ']'

def data_payload(body, fl, e):
    """DATA body -> (serializedPayload, inline QoS length). Skips the inline QoS ParameterList if flag Q."""
    otq = struct.unpack(e + 'H', body[2:4])[0]
    p = 4 + otq
    if not fl & 2:
        return body[p:], 0
    q = p
    while q + 4 <= len(body):
        pid, plen = struct.unpack(e + 'HH', body[q:q + 4])
        q += 4 + plen
        if pid == 1: break
    return body[q:], q - p

# ParameterId -> name (DDSI-RTPS 2.5 table 9.13 + Fast DDS 3.6.2 ParameterTypes.hpp)
PID = {0x0000: 'PAD', 0x0001: 'SENTINEL', 0x0002: 'PARTICIPANT_LEASE_DURATION', 0x0004: 'TIME_BASED_FILTER',
       0x0005: 'TOPIC_NAME', 0x0006: 'OWNERSHIP_STRENGTH', 0x0007: 'TYPE_NAME', 0x000f: 'DOMAIN_ID',
       0x0015: 'PROTOCOL_VERSION', 0x0016: 'VENDORID', 0x001a: 'RELIABILITY', 0x001b: 'LIVELINESS',
       0x001d: 'DURABILITY', 0x001e: 'DURABILITY_SERVICE', 0x001f: 'OWNERSHIP', 0x0021: 'PRESENTATION',
       0x0023: 'DEADLINE', 0x0025: 'DESTINATION_ORDER', 0x0027: 'LATENCY_BUDGET', 0x0029: 'PARTITION',
       0x002b: 'LIFESPAN', 0x002c: 'USER_DATA', 0x002d: 'GROUP_DATA', 0x002e: 'TOPIC_DATA',
       0x002f: 'UNICAST_LOCATOR', 0x0030: 'MULTICAST_LOCATOR', 0x0031: 'DEFAULT_UNICAST_LOCATOR',
       0x0032: 'METATRAFFIC_UNICAST_LOCATOR', 0x0033: 'METATRAFFIC_MULTICAST_LOCATOR',
       0x0034: 'PARTICIPANT_MANUAL_LIVELINESS_COUNT', 0x0035: 'CONTENT_FILTER_PROPERTY', 0x0040: 'HISTORY',
       0x0041: 'RESOURCE_LIMITS', 0x0043: 'EXPECTS_INLINE_QOS', 0x0048: 'DEFAULT_MULTICAST_LOCATOR',
       0x0049: 'TRANSPORT_PRIORITY', 0x0050: 'PARTICIPANT_GUID', 0x0052: 'GROUP_GUID', 0x0053: 'GROUP_ENTITYID',
       0x0058: 'BUILTIN_ENDPOINT_SET', 0x0059: 'PROPERTY_LIST', 0x005a: 'ENDPOINT_GUID',
       0x0060: 'TYPE_MAX_SIZE_SERIALIZED', 0x0062: 'ENTITY_NAME', 0x0070: 'KEY_HASH', 0x0071: 'STATUS_INFO',
       0x0073: 'DATA_REPRESENTATION', 0x0074: 'TYPE_CONSISTENCY_ENFORCEMENT', 0x0075: 'TYPE_INFORMATION',
       0x0077: 'BUILTIN_ENDPOINT_QOS', 0x4014: 'DOMAIN_TAG', 0x8000: 'PRODUCT_VERSION(fastdds)',
       0x8002: 'PERSISTENCE_GUID(fastdds)', 0x8003: 'MACHINE_ID(fastdds)', 0x8005: 'DISABLE_POSITIVE_ACKS(fastdds)',
       0x8006: 'DATASHARING(fastdds)', 0x8007: 'NETWORK_CONFIGURATION_SET(fastdds)'}
# QoS PIDs that `sedp` summarises (short label)
QOS_PIDS = {0x001d: 'durability', 0x001a: 'reliability', 0x0040: 'history', 0x0041: 'resource_limits',
            0x001b: 'liveliness', 0x0023: 'deadline', 0x002b: 'lifespan', 0x0027: 'latency_budget',
            0x001f: 'ownership', 0x0006: 'ownership_strength', 0x0025: 'destination_order',
            0x0021: 'presentation', 0x0029: 'partition', 0x0004: 'time_based_filter',
            0x001e: 'durability_service', 0x8005: 'disable_positive_acks'}
KINDS = {0x001d: ['VOLATILE', 'TRANSIENT_LOCAL', 'TRANSIENT', 'PERSISTENT'],
         0x001a: {1: 'BEST_EFFORT', 2: 'RELIABLE'}, 0x0040: ['KEEP_LAST', 'KEEP_ALL'],
         0x001b: ['AUTOMATIC', 'MANUAL_BY_PARTICIPANT', 'MANUAL_BY_TOPIC'], 0x001f: ['SHARED', 'EXCLUSIVE'],
         0x0025: ['BY_RECEPTION_TIMESTAMP', 'BY_SOURCE_TIMESTAMP']}

def dur(v, e):
    s, f = struct.unpack(e + 'iI', v[:8])
    if s == 0x7fffffff and f == 0xffffffff: return 'INFINITE'
    return f'{s + f / 2**32:.9g} s (sec {s} fraction 0x{f:08x})'

def kind(pid, k):
    t = KINDS.get(pid, {})
    return (t.get(k) if isinstance(t, dict) else (t[k] if 0 <= k < len(t) else None)) or f'kind {k}'

def pstr(v, e):
    n = struct.unpack(e + 'I', v[:4])[0]
    return repr(v[4:4 + n].rstrip(b'\0').decode('utf-8', 'replace'))

def pval(pid, v, e):
    """Decoded value of one parameter (hex for unknown PIDs)."""
    try:
        if pid in (0x001d, 0x001f, 0x0025):
            return kind(pid, struct.unpack(e + 'I', v[:4])[0])
        if pid in (0x001a, 0x001b):
            return f'{kind(pid, struct.unpack(e + "I", v[:4])[0])}, ' + \
                   ('max_blocking_time ' if pid == 0x001a else 'lease ') + dur(v[4:12], e)
        if pid == 0x0040:
            k, depth = struct.unpack(e + 'Ii', v[:8]); return f'{kind(pid, k)}, depth {depth}'
        if pid == 0x0041:
            return 'max_samples {}, max_instances {}, max_samples_per_instance {}'.format(*struct.unpack(e + 'iii', v[:12]))
        if pid in (0x0002, 0x0023, 0x002b, 0x0027, 0x0004):
            return dur(v, e)
        if pid in (0x0005, 0x0007, 0x0062):
            return pstr(v, e)
        if pid in (0x0050, 0x005a, 0x0052):
            return f'{v[:12].hex(" ")} | {eid(v[12:16])}'
        if pid in (0x002f, 0x0030, 0x0031, 0x0032, 0x0033, 0x0048):
            k, port = struct.unpack(e + 'iI', v[:8])
            a = '.'.join(map(str, v[20:24])) if k == 1 else v[8:24].hex()
            return f'kind {k} port {port} addr {a}'
        if pid == 0x0021:
            sc, coh, ordr = struct.unpack(e + 'I', v[:4])[0], v[4], v[5]
            return f'access_scope {sc} coherent {coh} ordered {ordr}'
        if pid == 0x0029:
            n, q, names = struct.unpack(e + 'I', v[:4])[0], 4, []
            for _ in range(n):
                ln = struct.unpack(e + 'I', v[q:q + 4])[0]
                names.append(v[q + 4:q + 4 + ln].rstrip(b'\0').decode()); q += 4 + (ln + 3) // 4 * 4
            return repr(names)
        if pid == 0x002c:
            n = struct.unpack(e + 'I', v[:4])[0]; return repr(v[4:4 + n])
        if pid in (0x0006, 0x0060, 0x0058):
            return str(struct.unpack(e + 'I', v[:4])[0]) if pid != 0x0058 else f'0x{struct.unpack(e + "I", v[:4])[0]:08x}'
        if pid == 0x0016:
            return f'{v[0]:02x}.{v[1]:02x}'
        if pid == 0x0015:
            return f'{v[0]}.{v[1]}'
        if pid == 0x0071:
            return f'0x{v[3]:02x} (bit0 disposed, bit1 unregistered)'
    except (struct.error, IndexError, UnicodeDecodeError):
        pass
    return v[:32].hex(' ') + (' ...' if len(v) > 32 else '')

def plist(b, e):
    """ParameterList -> [(offset, pid, length, value bytes)] up to and including SENTINEL."""
    out, q = [], 0
    while q + 4 <= len(b):
        pid, ln = struct.unpack(e + 'HH', b[q:q + 4])
        out.append((q, pid, ln, b[q + 4:q + 4 + ln]))
        q += 4 + ln
        if pid == 1: break
    return out

def datagrams(path):
    """Yield (frame-no, time, src, dst, UDP payload, [frame numbers]) per UDP datagram, IP fragments
    reassembled (used by params/sedp/stats). frame-no is the frame that completes the datagram,
    as in Wireshark ("Reassembled in")."""
    part = {}
    for n, t, pkt in frames(path):
        iu = ip_udp(pkt)
        if not iu or iu['proto'] != 17: continue
        if iu['foff'] == 0 and not iu['mf']:
            yield n, t, iu['src'], iu['dst'], iu['l4'][8:], [n]; continue
        k = (iu['src'], iu['dst'], iu['id'])
        p = part.setdefault(k, {'f': {}, 'n': [], 'end': None})
        p['f'][iu['foff']] = iu['l4']; p['n'].append(n)
        if not iu['mf']: p['end'] = iu['foff'] + len(iu['l4'])
        if p['end'] is not None:
            buf, off = b'', 0
            while off in p['f'] and off < p['end']:
                buf += p['f'][off]; off += len(p['f'][off])
            if off >= p['end']:
                del part[k]
                yield n, t, iu['src'], iu['dst'], buf[8:], p['n']

def data_subs(src, dst, pl):
    """Yield (sid, src, dst, flags, endianness, body, guidPrefix) for every submessage of one RTPS message."""
    if pl[:4] != b'RTPS': return
    p = 20
    while p + 4 <= len(pl):
        sid, fl = pl[p], pl[p + 1]
        e = '<' if fl & 1 else '>'
        ln = struct.unpack(e + 'H', pl[p + 2:p + 4])[0]
        body = pl[p + 4:p + 4 + ln] if ln else pl[p + 4:]
        yield sid, src, dst, fl, e, body, pl[8:20]
        if ln == 0: break
        p += 4 + ln

def payload_plist(body, fl, e):
    """(encapsulation id, endianness, ParameterList) of a DATA whose payload is PL_CDR_BE/LE, else None."""
    pl, _ = data_payload(body, fl, e)
    if len(pl) < 4 or pl[0] != 0 or pl[1] not in (2, 3): return None
    pe = '<' if pl[1] == 3 else '>'
    return pl[:2].hex(), pe, plist(pl[4:], pe)


def rtps(payload, maxlen=None, verbose=False):
    if payload[:4] != b'RTPS':
        return None
    out = [(None, f'RTPS v{payload[4]}.{payload[5]} vendor {payload[6]:02x}.{payload[7]:02x} guidPrefix {payload[8:20].hex(" ")}')]
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
            if verbose:
                pl, iq = data_payload(body, fl, e)
                d += f' Q={fl >> 1 & 1} D={fl >> 2 & 1} K={fl >> 3 & 1}' + (f' inlineQos {iq} B' if fl & 2 else '')
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
            if verbose:
                d = (f'reader {eid(body[0:4])} ' + d +
                     f' count {struct.unpack(e + "i", body[24:28])[0]} F={fl >> 1 & 1} L={fl >> 2 & 1}')
        elif verbose and sid == 0x06:
            base, nb, sns, q = snset(body, 8, e)
            d = (f'reader {eid(body[0:4])} writer {eid(body[4:8])} base {base} numBits {nb} -> ขอ SN {sns} '
                 f'count {struct.unpack(e + "i", body[q:q + 4])[0]} F={fl >> 1 & 1}')
        elif verbose and sid == 0x08:
            start = sn(body[8:16], e)
            base, nb, sns, q = snset(body, 16, e)
            d = (f'reader {eid(body[0:4])} writer {eid(body[4:8])} gapStart {start} gapList base {base} '
                 f'numBits {nb} -> SN ที่ไม่มีแล้ว {fmt_sns(list(range(start, base)) + sns)}')
        elif sid == 0x09:
            s, fr = struct.unpack(e + 'iI', body[:8]); d = f'time {s}.{fr * 1e9 / 2**32:09.0f}'
        elif sid == 0x0e:
            d = f'dst guidPrefix {body[:12].hex(" ")}'
        out.append((name, f'  [{p:3d}] {name:<18} flags 0x{fl:02x} len {ln:<5} {d}'))
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

def main():
    global verbose
    verbose = '-v' in sys.argv[1:]
    argv = [a for a in sys.argv[1:] if a != '-v']
    if len(argv) < 2:
        sys.exit(__doc__)
    cmd, path = argv[0], argv[1]
    arg = argv[2:]
    if cmd == 'frame':
        want = int(arg[0])
        for n, t, pkt in frames(path):
            if n == want:
                print(f'frame {n}: {len(pkt)} B'); hexdump(pkt)
                iu = ip_udp(pkt)
                if iu and iu['proto'] == 17:
                    for k, l in rtps(iu['l4'][8:], verbose=verbose) or []: print(l)
    elif cmd == 'strings':
        want = int(arg[0])
        for n, t, pkt in frames(path):
            if n == want: print(strings(pkt))
    elif cmd == 'sms':     # summarize RTPS submessages of interest
        hexid = lambda k: k.lower().startswith('0x') and len(k) == 4 and all(c in '0123456789abcdef' for c in k[2:].lower())
        kinds = {SM.get(int(k, 16), k.lower()) if hexid(k) else k for k in arg}   # exact names; 0xNN also accepted
        for k in sorted(kinds - set(SM.values())):
            if not hexid(k):
                print(f'warning: unknown submessage kind {k!r}; known: {" ".join(SM.values())} or 0xNN', file=sys.stderr)
        for n, t, pkt in frames(path):
            iu = ip_udp(pkt)
            if not iu or iu['proto'] != 17 or iu['foff'] != 0: continue
            r = rtps(iu['l4'][8:], verbose=verbose)
            hits = [l for k, l in (r or [])[1:] if k in kinds]
            if hits:
                print(f'frame {n} {t:.6f} {iu["src"]} -> {iu["dst"]} ip.id {iu["id"]} MF={iu["mf"]}')
                for l in hits: print(l)
    elif cmd == 'fragcount':
        from collections import Counter
        c = Counter()
        for n, t, pkt in frames(path):
            iu = ip_udp(pkt)
            if iu and iu['proto'] == 17: c[iu['id'], iu['src']] += 1
        big = {k: v for k, v in c.items() if v > 1}
        print('datagrams ที่ถูก IP fragment:', len(big), '· fragment ต่อ datagram:', Counter(big.values()))
    elif cmd == 'params':  # ParameterList of every DATA in one frame
        want = int(arg[0])
        for n, t, s, dd, pl, fr in datagrams(path):
            if n != want: continue
            if len(fr) > 1: print(f'(datagram reassembled from IP fragments in frames {fr})')
            for sid, src, dst, fl, e, body, gp in data_subs(s, dd, pl):
                if sid != 0x15: continue
                print(f'frame {n} {src} -> {dst} DATA writer {eid(body[8:12])} reader {eid(body[4:8])} SN {sn(body[12:20], e)}')
                if fl & 2:
                    otq = struct.unpack(e + 'H', body[2:4])[0]
                    print('  inline QoS:')
                    for q, pid, ln, v in plist(body[4 + otq:], e):
                        print(f'    [{q:3d}] 0x{pid:04x} {PID.get(pid, "?"):<36} len {ln:<4} {pval(pid, v, e)}')
                r = payload_plist(body, fl, e)
                if not r:
                    print('  (payload is not a ParameterList)'); continue
                enc, pe, ps = r
                print(f'  serializedPayload encap {enc} ({"PL_CDR_LE" if pe == "<" else "PL_CDR_BE"}), offsets from ParameterList start:')
                for q, pid, ln, v in ps:
                    print(f'    [{q:3d}] 0x{pid:04x} {PID.get(pid, "?"):<36} len {ln:<4} {pval(pid, v, pe)}')
    elif cmd == 'sedp':    # one line per SEDP DATA(w)/DATA(r)
        for n, t, s, dd, pl, fr in datagrams(path):
            for sid, src, dst, fl, e, body, gp in data_subs(s, dd, pl):
                w = eid(body[8:12])
                if sid != 0x15 or w not in ('00.00.03.c2', '00.00.04.c2'): continue
                kindwr = 'DATA(w)' if w == '00.00.03.c2' else 'DATA(r)'
                r = payload_plist(body, fl, e)
                if not r:
                    print(f'frame {n} {t:.6f} {src} -> {dst} {kindwr} SN {sn(body[12:20], e)} (no ParameterList: dispose/unregister)')
                    continue
                enc, pe, ps = r
                d = {pid: v for q, pid, ln, v in ps}
                ep = eid(d[0x005a][12:16]) if 0x005a in d else '?'
                topic = pval(5, d[5], pe) if 5 in d else '-'
                typ = pval(7, d[7], pe).split('::')[-1].strip("'") if 7 in d else '-'
                qos = '; '.join(f'{QOS_PIDS[pid]}={pval(pid, d[pid], pe)}' for pid in QOS_PIDS if pid in d)
                print(f'frame {n} {t:.6f} {src} -> {dst} {kindwr} SN {sn(body[12:20], e)} endpoint {ep} '
                      f'topic {topic} type {typ} | {qos or "(no QoS PIDs: all default)"}')
    elif cmd == 'stats':   # per writer/reader counters
        from collections import defaultdict
        st = defaultdict(lambda: dict(DATA=[], HEARTBEAT=0, GAP=0, ACKNACK=0, hb=None))
        for n, t, s, dd, pl, fr in datagrams(path):
            for sid, src, dst, fl, e, body, gp in data_subs(s, dd, pl):
                if sid in (0x15, 0x07, 0x08):
                    k = (src, eid(body[8:12]) if sid == 0x15 else eid(body[4:8]))
                    if sid == 0x15: st[k]['DATA'].append(sn(body[12:20], e))
                    elif sid == 0x07:
                        st[k]['HEARTBEAT'] += 1; st[k]['hb'] = (sn(body[8:16], e), sn(body[16:24], e))
                    else: st[k]['GAP'] += 1
                elif sid == 0x06:
                    st[(dst, eid(body[4:8]))]['ACKNACK'] += 1
        print('writer at (IP | entityId)          DATA  HB  GAP  ACKNACK(to it)  DATA SNs (in frame order)   last HB first..last')
        for (ip, w), s in sorted(st.items()):
            hb = f'{s["hb"][0]}..{s["hb"][1]}' if s['hb'] else '-'
            print(f'{ip:<15} {w:<18} {len(s["DATA"]):5d} {s["HEARTBEAT"]:3d} {s["GAP"]:4d} {s["ACKNACK"]:8d}        '
                  f'{",".join(map(str, s["DATA"]))[:60] or "-":<27} {hb}')


if __name__ == '__main__':
    main()
