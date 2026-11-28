#!/usr/bin/env python3
"""Summarise exp14 (run_container_ipc.sh) runs. Stdlib only.
usage: ipc_summary.py <out/ipc dir> <results dir>
writes <results>/ipc_runs.csv (one row per run) and <results>/ipc_summary.txt (decision table + evidence)."""
import csv, glob, os, re, sys

out, res = sys.argv[1], sys.argv[2]
OURS = {"172.22.0.2", "172.22.0.3", "127.0.0.1"}
rows = []
for lis in sorted(glob.glob(os.path.join(out, "*_r[0-9]*.listener.log"))):
    name = os.path.basename(lis)[:-len(".listener.log")]
    arm, rep = re.match(r"(.+)_r(\d+)$", name).groups()
    rd = lambda suf: open(os.path.join(out, name + suf)).read() if os.path.exists(os.path.join(out, name + suf)) else ""
    received = rd(".listener.log").count("I heard")
    published = rd(".talker.log").count("Publishing")
    pub2 = rd(".talker2.log").count("Publishing")
    flows = {}
    for s in "AB":
        for line in rd(f".{s}.hello.txt").splitlines():
            n, src, dst = line.split()
            if not {src, dst} <= OURS:   # frames of other experiments sharing ctrnet (other domain)
                continue
            # the same flow is captured in both netns on bridge arms: take the larger count
            # (c_A's capture stops when c_A is killed in arm "kill")
            flows[(src, dst)] = max(flows.get((src, dst), 0), int(n))
    hello_lo = sum(n for (src, _), n in flows.items() if src.startswith("127."))
    hello_eth = sum(n for (src, _), n in flows.items() if not src.startswith("127."))
    # SHM locators of domain 14 only (user unicast ports 10900+11+2*pid; other domains share ctrnet)
    hostids = sorted(set(h for port, h in re.findall(r"port (\d+) address 55 (\w\w \w\w)", rd(".shmloc.txt"))
                         if 10900 <= int(port) < 11150))
    midA, midB = rd(".A.shm_mid.txt"), rd(".B.shm_mid.txt")
    ns = lambda t, k: (re.search(k + r"=(\S+)", t) or [None, ""])[1]
    shm_segs = lambda t: len(re.findall(r" fastdds_[0-9a-f]{16}$", t, re.M))
    shm_ports = lambda t: " ".join(sorted(re.findall(r" fastdds_port(\d+)$", t, re.M)))
    row = dict(arm=arm, rep=rep, published=published, received=received,
               hello_frames_ip=hello_eth, hello_frames_lo=hello_lo,
               same_ipcns=int(ns(midA, "ipcns") == ns(midB, "ipcns") != ""),
               same_netns=int(ns(midA, "netns") == ns(midB, "netns") != ""),
               same_hostname=int(ns(midA, "hostname") == ns(midB, "hostname") != ""),
               shm_hostids=" / ".join(hostids), n_distinct_hostids=len(hostids),
               A_shm_segments=shm_segs(midA), A_shm_ports=shm_ports(midA),
               B_shm_segments=shm_segs(midB), B_shm_ports=shm_ports(midB),
               shm_size=ns(midA, "shm_fs").replace("shm", "") if midA else "",
               talker2_published=pub2,
               B_shm_after_kill=" ".join(re.findall(r" (fastdds_\S+)$", rd(".B.shm_afterkill.txt"), re.M)),
               B_shm_after_talker2=" ".join(re.findall(r" (fastdds_\S+)$", rd(".B.shm_after2.txt"), re.M)))
    rows.append(row)
if not rows:
    sys.exit("no runs in " + out)
os.makedirs(res, exist_ok=True)
with open(os.path.join(res, "ipc_runs.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)
by = {}
for r in rows:
    by.setdefault(r["arm"], []).append(r)
with open(os.path.join(res, "ipc_summary.txt"), "w") as f:
    f.write("exp14 decision table (per arm, all reps); data path = where 'Hello World' frames were seen\n")
    f.write("arm | reps | same ipc/net/hostname | distinct SHM host ids | Hello frames IP / lo (per rep) | received/published (per rep) | data path\n")
    for arm, rs in by.items():
        ip = [r["hello_frames_ip"] for r in rs]; lo = [r["hello_frames_lo"] for r in rs]
        path = "UDP (container IP)" if all(ip) else ("UDP lo" if all(lo) else ("SHM (no user DATA on any interface)" if not any(ip) and not any(lo) and all(r["received"] for r in rs) else ("none: 0 received" if not any(r["received"] for r in rs) else "mixed")))
        r0 = rs[0]
        f.write(f"{arm} | {len(rs)} | {r0['same_ipcns']}/{r0['same_netns']}/{r0['same_hostname']} | "
                f"{','.join(str(r['n_distinct_hostids']) for r in rs)} | {ip} / {lo} | "
                f"{[(r['received'], r['published'] + r['talker2_published']) for r in rs]} | {path}\n")
print(open(os.path.join(res, "ipc_summary.txt")).read())
