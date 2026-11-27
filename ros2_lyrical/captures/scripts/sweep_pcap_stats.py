#!/usr/bin/env python3
"""Per-run counts from a receiver-side capture of the image workload (standard library only).

Used by run_rcvbuf_sweep.sh (docs/03 §9 and §11). Prints ONE JSON object on stdout:

  frames              all frames in the capture
  datafrag_total      DATA_FRAG submessages sender -> receiver (fragmentsInSubmessage summed)
  datafrag_unique     distinct (writer, SN, fragmentStartingNum) among them
  datafrag_retrans    datafrag_total - datafrag_unique  (RELIABLE: repairs after NACK_FRAG)
  nackfrag            NACK_FRAG submessages receiver -> sender
  sn_seen / sn_complete   image SNs seen / SNs whose every fragment (1..ceil(sampleSize/fragSize))
                      appeared at least once on the wire
  ip_frags_per_dgram  most common number of IP fragments per DATA_FRAG datagram
  burst_ms_med/min/max    per image SN: time from the first IP fragment of its first DATA_FRAG datagram
                      to the last IP fragment of the last datagram, first transmissions only,
                      complete images only (all fragments seen)
  dgram_us_med        per DATA_FRAG datagram: first -> last IP fragment (first transmissions)
  gap_us_med          median gap between consecutive IP fragments of one datagram
  image_frame_bytes   Ethernet frame bytes (no FCS) of one complete image (first transmissions)
  image_wire_us_1g    the same image on 1000BASE-T: (bytes + 24 B per frame for FCS 4 +
                      preamble/SFD 8 + inter-frame gap 12) * 8 / 1e9 s      (a calculation, not a measurement)

Timestamps are what tcpdump wrote (microsecond pcap, so gaps are multiples of 1 us). Only frames from --src to --dst are
counted as data; NACK_FRAG is counted from --dst to --src.

With --per-image, prints instead one CSV line per image SN (first transmissions):
  sn,datagrams,ip_frags,first_to_last_ms,dgram_us_med,gap_us_med

Usage: sweep_pcap_stats.py <pcap> [--src 172.20.0.3] [--dst 172.20.0.2] [--per-image]
"""
import gzip, json, statistics, struct, sys
from collections import Counter, defaultdict

# Pcap reading follows tools/rtps_peek.py (which cannot be imported: it runs its CLI on import).
def frames(path):
    f = (gzip.open if path.endswith('.gz') else open)(path, 'rb')
    data = f.read()
    magic = data[:4]
    end = '<' if magic in (b'\xd4\xc3\xb2\xa1', b'\x4d\x3c\xb2\xa1') else '>'
    nano = magic in (b'\x4d\x3c\xb2\xa1', b'\xa1\xb2\x3c\x4d')
    link = struct.unpack(end + 'I', data[20:24])[0]
    if link != 1:
        raise SystemExit(f'{path}: link type {link}, expected Ethernet (capture on eth0)')
    off = 24; t_first = None
    while off + 16 <= len(data):
        ts, tu, incl, _ = struct.unpack(end + 'IIII', data[off:off + 16])
        # Time as integer nanoseconds converted once, relative to the first frame: a float of
        # 1.8e9 s since the epoch only resolves ~0.24 us, which turned 1 us gaps into 0.954.
        t_ns = ts * 1_000_000_000 + (tu if nano else tu * 1000)
        if t_first is None:
            t_first = t_ns
        yield None, (t_ns - t_first) / 1e9, data[off + 16:off + 16 + incl]
        off += 16 + incl


def ip_udp(pkt):
    if pkt[12:14] != b'\x08\x00' or len(pkt) < 34:
        return None
    ip = pkt[14:]
    ihl = (ip[0] & 15) * 4
    fo = struct.unpack('>H', ip[6:8])[0]
    return dict(proto=ip[9], src='.'.join(map(str, ip[12:16])), dst='.'.join(map(str, ip[16:20])),
                foff=(fo & 0x1fff) * 8, l4=ip[ihl:], id=struct.unpack('>H', ip[4:6])[0])


def submessages(payload):
    """yield (id, endian, body) for each RTPS submessage"""
    if payload[:4] != b'RTPS':
        return
    p = 20
    while p + 4 <= len(payload):
        sid, fl = payload[p], payload[p + 1]
        e = '<' if fl & 1 else '>'
        ln = struct.unpack(e + 'H', payload[p + 2:p + 4])[0]
        body = payload[p + 4:p + 4 + ln] if ln else payload[p + 4:]
        yield sid, e, body
        if ln == 0:
            break
        p += 4 + ln


def main():
    args = sys.argv[1:]
    if not args or args[0] in ('-h', '--help'):
        print(__doc__); return 0
    path, src, dst = args[0], '172.20.0.3', '172.20.0.2'
    if '--src' in args: src = args[args.index('--src') + 1]
    if '--dst' in args: dst = args[args.index('--dst') + 1]

    n_frames = 0
    dg = {}                      # (ip id) -> {'t0','t1','n','bytes','ts':[...]}  for src->dst fragmented/UDP datagrams
    dg_key = {}                  # ip id -> list of (writer, sn, fragStart, inSub, fragSize, sampleSize)
    nack = 0
    for _, ts, pkt in frames(path):
        n_frames += 1
        d = ip_udp(pkt)
        if d is None or d['proto'] != 17:
            continue
        if d['src'] == dst and d['dst'] == src and d['foff'] == 0:
            for sid, e, body in submessages(d['l4'][8:]):
                if sid == 0x12:
                    nack += 1
            continue
        if d['src'] != src or d['dst'] != dst:
            continue
        rec = dg.get(d['id'])
        if rec is None or (d['foff'] == 0 and rec.get('have_first')):
            rec = dg[d['id']] = {'t0': ts, 't1': ts, 'n': 0, 'bytes': 0, 'ts': []}
        rec['t0'] = min(rec['t0'], ts); rec['t1'] = max(rec['t1'], ts)
        rec['n'] += 1; rec['bytes'] += len(pkt); rec['ts'].append(ts)
        if d['foff'] == 0:
            rec['have_first'] = True
            keys = []
            for sid, e, body in submessages(d['l4'][8:]):
                if sid == 0x16 and len(body) >= 32:
                    writer = body[8:12].hex()
                    hi, lo = struct.unpack(e + 'iI', body[12:20])
                    fs = struct.unpack(e + 'I', body[20:24])[0]
                    insub, fsz = struct.unpack(e + 'HH', body[24:28])
                    ssz = struct.unpack(e + 'I', body[28:32])[0]
                    keys.append((writer, (hi << 32) | lo, fs, insub, fsz, ssz))
            if keys:
                dg_key[d['id']] = keys
                rec['keys'] = keys

    total = 0; seen = set(); per_sn = defaultdict(set); nfrag_needed = {}
    first_tx = defaultdict(list)          # (writer, sn) -> records of first transmissions
    nfr = Counter(); dgram_us = []; gaps = []
    for rec in dg.values():
        keys = rec.get('keys')
        if not keys:
            continue
        fresh = False
        for (w, s, fs, insub, fsz, ssz) in keys:
            total += insub
            for k in range(fs, fs + insub):
                if (w, s, k) not in seen:
                    seen.add((w, s, k)); fresh = True
                per_sn[(w, s)].add(k)
            nfrag_needed[(w, s)] = -(-ssz // fsz) if fsz else 0
        nfr[rec['n']] += 1
        if fresh:
            first_tx[(w, s)].append(rec)
            dgram_us.append((rec['t1'] - rec['t0']) * 1e6)
            t = sorted(rec['ts'])
            gaps.extend((b - a) * 1e6 for a, b in zip(t, t[1:]))
    complete = [k for k in per_sn if len(per_sn[k]) >= nfrag_needed.get(k, 1 << 30)]
    bursts = []; img_bytes = None; img_frames = None
    for k in complete:
        recs = first_tx[k]
        bursts.append((max(r['t1'] for r in recs) - min(r['t0'] for r in recs)) * 1e3)
        if img_bytes is None:
            img_bytes = sum(r['bytes'] for r in recs); img_frames = sum(r['n'] for r in recs)

    def med(x): return round(statistics.median(x), 3) if x else None
    if '--per-image' in args:
        print('sn,datagrams,ip_frags,first_to_last_ms,dgram_us_med,gap_us_med,complete')
        for k in sorted(first_tx, key=lambda k: k[1]):
            recs = first_tx[k]
            g = []
            for r in recs:
                t = sorted(r['ts']); g.extend((b - a) * 1e6 for a, b in zip(t, t[1:]))
            print(f"{k[1]},{len(recs)},{sum(r['n'] for r in recs)},"
                  f"{(max(r['t1'] for r in recs) - min(r['t0'] for r in recs)) * 1e3:.3f},"
                  f"{med([(r['t1'] - r['t0']) * 1e6 for r in recs])},{med(g)},{int(k in complete)}")
        return 0
    out = {
        'frames': n_frames,
        'datafrag_total': total,
        'datafrag_unique': len(seen),
        'datafrag_retrans': total - len(seen),
        'nackfrag': nack,
        'sn_seen': len(per_sn),
        'sn_complete': len(complete),
        'ip_frags_per_dgram': nfr.most_common(1)[0][0] if nfr else None,
        'burst_ms_med': med(bursts),
        'burst_ms_min': round(min(bursts), 3) if bursts else None,
        'burst_ms_max': round(max(bursts), 3) if bursts else None,
        'dgram_us_med': med(dgram_us),
        'gap_us_med': med(gaps),
        'image_frame_bytes': img_bytes,
        'image_frames': img_frames,
        'image_wire_us_1g': round((img_bytes + 24 * img_frames) * 8 / 1e9 * 1e6, 1) if img_bytes else None,
    }
    print(json.dumps(out))
    return 0


if __name__ == '__main__':
    sys.exit(main())
