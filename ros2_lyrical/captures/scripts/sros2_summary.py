#!/usr/bin/env python3
"""Summarise exp15 (run_sros2.sh, docs/03 §2.4). Stdlib only; runs tshark inside lyrical-wire:exp.
usage: sros2_summary.py <out/sros2 dir> <results dir>
writes <results>/sros2_runs.csv, sros2_summary.txt, sros2_governance.xml (copy of the generated, unsigned
governance; no keys). Per pcap (only frames between 172.22.1.2 and 172.22.1.3 or their multicast):
  t0 = first SPDP DATA(p) (writer 0x000100c2) sent by the talker (172.22.1.3)
  t1 = first user sample received by the subscriber (log timestamp: demo listener "I heard" or sec_sub.py
       t_first_recv_ns; CLOCK_REALTIME, same kernel clock as the pcap timestamps)
  frames/bytes in [t0, t1] (all frames incl. IP fragments, both directions);
  auth handshake = RTPS messages carrying writer 0x000201c3 (ParticipantStatelessMessage), size = sum of
  frame lengths of all IP fragments of that datagram; volatile = frames with SEC_PREFIX (0x31) but no
  SRTPS_PREFIX (0x33) (crypto-token exchange, ParticipantVolatileMessageSecure, inferred: its writer id is
  inside SEC_BODY); per-sample frame = most common frame length talker -> listener user unicast port.
"""
import collections, csv, json, os, re, shutil, statistics, subprocess, sys

out, res = sys.argv[1], sys.argv[2]
A, B = "172.22.1.3", "172.22.1.2"
FIELDS = ["frame.time_epoch", "frame.len", "ip.src", "ip.dst", "ip.id", "udp.dstport", "rtps.sm.id",
          "rtps.sm.wrEntityId", "ip.flags.mf", "ip.frag_offset"]


def tshark(pcap):
    cmd = ["docker", "run", "--rm", "--network", "none", "-v", f"{os.path.abspath(out)}:/o:ro", "lyrical-wire:exp",
           "tshark", "-r", f"/o/{pcap}", "-o", "ip.defragment:FALSE", "-T", "fields", "-E", "separator=|"]
    for f in FIELDS:
        cmd += ["-e", f]
    rows = []
    for line in subprocess.run(cmd, capture_output=True, text=True).stdout.splitlines():
        v = dict(zip(FIELDS, line.split("|")))
        if not ({v["ip.src"], v["ip.dst"]} <= {A, B} or (v["ip.src"] in (A, B) and v["ip.dst"].startswith("239."))):
            continue
        v["t"] = float(v["frame.time_epoch"]); v["len"] = int(v["frame.len"])
        rows.append(v)
    return rows


def first_recv(name):
    log = open(os.path.join(out, name + ".listener.log")).read()
    m = re.search(r"\[(\d+\.\d+)\] \[listener\]: I heard", log)
    if m:
        return float(m.group(1)), log.count("I heard"), None
    js = [json.loads(l) for l in log.splitlines() if l.startswith("{")]
    if js and js[-1].get("t_first_recv_ns"):
        return js[-1]["t_first_recv_ns"] / 1e9, js[-1]["received"], js[-1]
    return None, 0, (js[-1] if js else None)


rows = []
for f in sorted(os.listdir(out)):
    m = re.match(r"(func|timing)_(sec|plain)_r(\d+)\.pcap$", f)
    if not m:
        continue
    mode, sec, rep = m.groups(); name = f[:-5]
    fr = tshark(f)
    t1, received, sub = first_recv(name)
    spdp_a = [r for r in fr if r["ip.src"] == A and "0x000100c2" in r["rtps.sm.wrEntityId"]]
    t0 = spdp_a[0]["t"] if spdp_a else None
    win = [r for r in fr if t0 is not None and t1 is not None and t0 <= r["t"] <= t1]
    # handshake datagrams (group IP fragments by (src, ip.id))
    groups = collections.defaultdict(list)
    for r in fr:
        groups[(r["ip.src"], r["ip.id"])].append(r)
    hs = [g for g in groups.values() if any("0x000201c3" in r["rtps.sm.wrEntityId"] for r in g)]
    hs_sizes = sorted(sum(r["len"] for r in g) for g in hs)
    vol = [r for r in fr if "0x31" in r["rtps.sm.id"] and "0x33" not in r["rtps.sm.id"]]
    srtps = [r for r in fr if "0x33" in r["rtps.sm.id"]]
    hello = []
    if sec == "plain":
        ports = collections.Counter(r["udp.dstport"] for r in fr if r["ip.src"] == A and r["ip.dst"] == B
                                    and r["rtps.sm.id"].startswith("0x0e,0x09,0x15"))
    # user port of the listener = 7400 + 250*15 + 11 (participant 0, started first)
    up = str(7400 + 250 * 15 + 11)
    data_frames = [r["len"] for r in fr if r["ip.src"] == A and r["ip.dst"] == B and r["udp.dstport"] == up
                   and (t1 is None or r["t"] >= t1 - 0.01)]
    mode_len = collections.Counter(data_frames).most_common(3)
    pubj = None
    if mode == "timing":
        tl = open(os.path.join(out, name + ".talker.log")).read()
        js = [json.loads(l) for l in tl.splitlines() if l.startswith("{")]
        pubj = js[-1] if js else None
    row = dict(mode=mode, security=sec, rep=rep, received=received,
               t_spdp_to_first_sample_ms=round((t1 - t0) * 1e3, 1) if (t0 and t1) else "",
               frames_spdp_to_first_sample=len(win), bytes_spdp_to_first_sample=sum(r["len"] for r in win),
               auth_handshake_msgs=len(hs), auth_handshake_bytes=sum(hs_sizes),
               auth_handshake_msg_sizes=" ".join(map(str, hs_sizes)),
               volatile_secure_frames=len(vol), srtps_frames=len(srtps), frames_total=len(fr),
               user_port_frame_len_top3=" ".join(f"{l}x{n}" for l, n in mode_len))
    if pubj:
        row.update(pub_match_ms=round((pubj["t_match_ns"] - pubj["t_create_ns"]) / 1e6, 1) if pubj.get("t_match_ns") else "",
                   pub_create_to_first_recv_ms=round(((t1 or 0) * 1e9 - pubj["t_create_ns"]) / 1e6, 1) if t1 else "",
                   published_after_match=pubj.get("published_after_match"),
                   pub_cpu_s=round(pubj.get("cpu_user_s", 0) + pubj.get("cpu_sys_s", 0), 3),
                   sub_cpu_s=round(sub.get("cpu_user_s", 0) + sub.get("cpu_sys_s", 0), 3) if sub else "")
    rows.append(row)

os.makedirs(res, exist_ok=True)
keys = []
for r in rows:
    keys += [k for k in r if k not in keys]
with open(os.path.join(res, "sros2_runs.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(rows)
gov = os.path.join(out, "sros2_keystore", "enclaves", "governance.xml")
if os.path.exists(gov):
    shutil.copy(gov, os.path.join(res, "sros2_governance.xml"))
with open(os.path.join(res, "sros2_summary.txt"), "w") as fh:
    for mode in ("func", "timing"):
        for sec in ("plain", "sec"):
            rs = [r for r in rows if r["mode"] == mode and r["security"] == sec]
            if not rs:
                continue
            fh.write(f"== {mode} {sec} ({len(rs)} reps)\n")
            for k in keys[3:]:
                vals = [r.get(k, "") for r in rs]
                nums = [v for v in vals if isinstance(v, (int, float))]
                med = f"  median {statistics.median(nums)}" if len(nums) == len(vals) and nums else ""
                fh.write(f"  {k}: {vals}{med}\n")
print(open(os.path.join(res, "sros2_summary.txt")).read())
