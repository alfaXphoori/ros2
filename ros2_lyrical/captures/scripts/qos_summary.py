#!/usr/bin/env python3
"""Summarise experiment 16 (run_qos.sh): one CSV row per case + trimmed node logs.

Reads out/qos/<case>.pcap (filtered) and <case>.{pub,sub}.log, decodes RTPS with
tools/rtps_peek.py (imported, stdlib only) and writes
  <res>/qos_summary.csv  case, pcap, SEDP frames of /qos_demo, user DATA/HEARTBEAT/ACKNACK/GAP
                         counts of the /qos_demo writer, SNs sent, SNs sent twice, GAP SNs,
                         ParticipantMessage DATA(m) count + times, HEARTBEATs with L flag,
                         samples received by qos_sub.py, QoS PIDs in DATA(w)/DATA(r)
  <res>/qos_node_logs.txt  the qos_pub.py / qos_sub.py logs of every case (PUB, RECV, ASSERT,
                         QoS events, rclpy warnings), host name replaced with <host>
"""
import argparse, csv, importlib.util, os, re
from collections import Counter

ap = argparse.ArgumentParser()
ap.add_argument('--out', required=True); ap.add_argument('--res', required=True)
ap.add_argument('--cap', required=True); ap.add_argument('--host', default='')
a = ap.parse_args()
here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('rtps_peek', os.path.join(here, '..', '..', 'tools', 'rtps_peek.py'))
rp = importlib.util.module_from_spec(spec); spec.loader.exec_module(rp)

CASES = 'tl_d1 tl_d10 tl_all vol_d10 live_auto live_man dl_ls mm_rel mm_dur loss_d1 loss_d50'.split()
rows, ev = [], []
for c in CASES:
    pc = os.path.join(a.out, c + '.pcap')
    if not os.path.exists(pc): continue
    sedp, uw = [], None
    t0 = None
    for n, t, s, d, pl, fr in rp.datagrams(pc):
        for sid, src, dst, fl, e, body, gp in rp.data_subs(s, d, pl):
            w = rp.eid(body[8:12])
            if sid == 0x15 and w in ('00.00.03.c2', '00.00.04.c2'):
                r = rp.payload_plist(body, fl, e)
                if not r: continue
                enc, pe, ps = r
                dd = {pid: v for q, pid, ln, v in ps}
                if 5 in dd and 'rt/qos_demo' in rp.pval(5, dd[5], pe):
                    kind = 'w' if w == '00.00.03.c2' else 'r'
                    qos = ' / '.join(f'{rp.QOS_PIDS[p]}={rp.pval(p, dd[p], pe).split(" (")[0]}'
                                     for p in rp.QOS_PIDS if p in dd)
                    sedp.append((kind, n, qos))
                    if kind == 'w': uw = (src, rp.eid(dd[0x005a][12:16]))
    cnt = Counter(); sns = []; gaps = []; dm = []; lhb = 0
    for n, t, s, d, pl, fr in rp.datagrams(pc):
        t0 = t0 or t
        for sid, src, dst, fl, e, body, gp in rp.data_subs(s, d, pl):
            if uw and src == uw[0] and sid in (0x15, 0x07, 0x08) and \
                    rp.eid(body[8:12] if sid == 0x15 else body[4:8]) == uw[1]:
                name = rp.SM[sid]; cnt[name] += 1
                if sid == 0x15: sns.append(rp.sn(body[12:20], e))
                if sid == 0x07 and fl & 4: lhb += 1
                if sid == 0x08:
                    start = rp.sn(body[8:16], e); base, nb, l, q = rp.snset(body, 16, e)
                    gaps += list(range(start, base)) + l
            if uw and dst == uw[0] and sid == 0x06 and rp.eid(body[4:8]) == uw[1]:
                cnt['ACKNACK'] += 1
            if sid == 0x15 and rp.eid(body[8:12]) == '00.02.00.c2':
                dm.append(f'{t - t0:.3f}')
    sub = open(os.path.join(a.out, c + '.sub.log')).read() if os.path.exists(os.path.join(a.out, c + '.sub.log')) else ''
    twice = sorted(k for k, v in Counter(sns).items() if v > 1)
    rows.append(dict(case=c, pcap=f'exp16_qos_{c}.pcap',
                     sedp_w_frames=' '.join(str(n) for k, n, q in sedp if k == 'w'),
                     sedp_r_frames=' '.join(str(n) for k, n, q in sedp if k == 'r'),
                     user_writer=uw[1] if uw else '',
                     user_DATA=cnt['DATA'], user_HEARTBEAT=cnt['HEARTBEAT'], user_HB_with_L=lhb,
                     ACKNACK_to_user_writer=cnt['ACKNACK'], user_GAP=cnt['GAP'],
                     SNs_sent=rp.fmt_sns(sorted(set(sns))), SNs_sent_twice=rp.fmt_sns(twice),
                     GAP_SNs=rp.fmt_sns(sorted(set(gaps))),
                     participant_msg_DATA=len(dm), participant_msg_t_s=' '.join(dm),
                     sub_received=len(re.findall(r' RECV ', sub)),
                     qos_DATA_w=next((q for k, n, q in sedp if k == 'w'), ''),
                     qos_DATA_r=next((q for k, n, q in sedp if k == 'r'), '')))
    for role in ('pub', 'sub'):
        f = os.path.join(a.out, f'{c}.{role}.log')
        if not os.path.exists(f): continue
        keep = [l.rstrip() for l in open(f)]
        ev.append(f'== {c} {role} ({len(keep)} lines)')
        ev += keep
with open(os.path.join(a.res, 'qos_summary.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
txt = '\n'.join(ev) + '\n'
if a.host: txt = txt.replace(a.host, '<host>')
open(os.path.join(a.res, 'qos_node_logs.txt'), 'w').write(txt)
print(f'{len(rows)} cases -> {a.res}/qos_summary.csv, qos_node_logs.txt')
