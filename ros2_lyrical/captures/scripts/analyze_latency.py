#!/usr/bin/env python3
"""Summarise out/latency/<config>/run_XX.* produced by run_latency.sh (standard library only).

Per config:
  - samples: rows with seq >= --warmup of every run (warm-up rule: the first N sequence
    numbers of each run are discarded, whether or not they arrived)
  - min, median, mean, p90, p99, p99.9 (only when n >= 10 / (1 - 0.999) = 10 000), max
    percentiles: linear interpolation between order statistics (same as numpy default)
  - 95% CI for median / p90 / p99 by CLUSTER bootstrap: resample whole runs with
    replacement, pool their samples, compute the statistic; --boot resamples, fixed seed;
    percentile interval (2.5%, 97.5%). Runs are the independent unit, samples within a
    run are correlated.
  - per-run medians: min / median / max across runs (between-run variability)
  - delivery: unique seqs received / expected over ALL seqs (warm-up included),
    duplicates, out-of-order arrivals, image payload length errors
  - Udp RcvbufErrors delta (after - before) in the subscriber's network namespace
Outputs: --json (full summary), --csv (one row per config), and <csv dir>/latency_runs.csv
(one row per run).  All latencies in microseconds.
"""
import argparse
import csv
import glob
import json
import os
import random
import statistics


def pct(sorted_x, q):
    """Linear interpolation percentile, q in [0, 100]."""
    n = len(sorted_x)
    if n == 0:
        return float('nan')
    h = (n - 1) * q / 100.0
    lo = int(h)
    hi = min(lo + 1, n - 1)
    return sorted_x[lo] + (sorted_x[hi] - sorted_x[lo]) * (h - lo)


def rcvbuf_delta(path):
    try:
        lines = open(path).read().split('\n')
        vals = {}
        for ln in lines:
            if not ln.strip():
                continue
            tag, rest = ln.split(' ', 1)
            f = rest.split()
            # "Udp: InDatagrams NoPorts InErrors OutDatagrams RcvbufErrors ..." values line
            vals[tag] = (int(f[3]), int(f[5]))   # InErrors, RcvbufErrors
        return (vals['after'][1] - vals['before'][1], vals['after'][0] - vals['before'][0])
    except (OSError, KeyError, ValueError, IndexError):
        return (None, None)


def load_config(d, warmup):
    runs = []
    for c in sorted(glob.glob(os.path.join(d, 'run_*.csv'))):
        if c.endswith('.pub.csv'):
            continue
        base = c[:-4]
        pubcall = []
        try:
            with open(base + '.pub.csv') as f:
                for row in csv.DictReader(f):
                    if int(row['seq']) >= warmup:
                        pubcall.append(int(row['publish_call_ns']) / 1000.0)
        except OSError:
            pass
        lat = []
        early = {}
        neg = 0
        with open(c) as f:
            for row in csv.DictReader(f):
                if int(row['seq']) < warmup:
                    early[int(row['seq'])] = int(row['latency_ns']) / 1000.0
                    continue
                v = int(row['latency_ns']) / 1000.0
                if v < 0:
                    neg += 1
                lat.append(v)
        try:
            meta = json.load(open(base + '.meta.json'))
        except OSError:
            meta = None
        rb, inerr = rcvbuf_delta(base + '.snmp')
        runs.append({'run': os.path.basename(base), 'lat': lat, 'neg': neg, 'meta': meta,
                     'pubcall': pubcall, 'early': early,
                     'rcvbuf': rb, 'inerr': inerr})
    return runs


def summarise(name, runs, cfg, boot, seed, warmup):
    pooled = sorted(v for r in runs for v in r['lat'])
    n = len(pooled)
    s = {'config': name, **cfg, 'warmup_discarded_per_run': warmup, 'n_runs': len(runs),
         'n_samples': n}
    metas = [r['meta'] for r in runs if r['meta']]
    s['expected_total'] = sum(m['expected'] for m in metas)
    s['delivered_total'] = sum(m['unique'] for m in metas)
    s['delivered_ratio'] = s['delivered_total'] / s['expected_total'] if s['expected_total'] else None
    s['duplicates'] = sum(m['duplicates'] for m in metas)
    s['out_of_order'] = sum(m['out_of_order'] for m in metas)
    s['bad_length'] = sum(m['bad_length'] for m in metas)
    s['runs_with_missing'] = sum(1 for m in metas if m['missing'])
    s['runs_without_meta'] = len(runs) - len(metas)
    s['negative_latencies'] = sum(r['neg'] for r in runs)
    rbs = [r['rcvbuf'] for r in runs if r['rcvbuf'] is not None]
    s['rcvbuf_errors_total'] = sum(rbs) if rbs else None
    s['runs_with_rcvbuf_errors'] = sum(1 for x in rbs if x > 0)
    s['rcvbuf_errors_max_per_run'] = max(rbs) if rbs else None
    if n == 0:
        return s
    s['min_us'] = pooled[0]
    s['median_us'] = pct(pooled, 50)
    s['mean_us'] = statistics.fmean(pooled)
    s['p90_us'] = pct(pooled, 90)
    s['p99_us'] = pct(pooled, 99)
    s['p999_us'] = pct(pooled, 99.9) if n >= 10000 else None
    s['max_us'] = pooled[-1]
    s['frac_gt_10ms'] = sum(1 for v in pooled if v > 10000.0) / n
    # warm-up samples are excluded above; report the first two separately (cold path)
    fs = {}
    for q in (0, 1):
        x = sorted(r['early'][q] for r in runs if q in r['early'])
        fs['seq%d' % q] = {'received_in_runs': len(x), 'min_us': x[0] if x else None,
                           'median_us': statistics.median(x) if x else None,
                           'max_us': x[-1] if x else None}
    s['first_samples'] = fs
    pc = sorted(v for r in runs for v in r['pubcall'])
    if pc:
        # duration of the publish() call itself in the publisher (same warm-up rule)
        s['publish_call_us'] = {'n': len(pc), 'median': pct(pc, 50), 'p99': pct(pc, 99),
                                'max': pc[-1]}
    meds = sorted(statistics.median(r['lat']) for r in runs if r['lat'])
    s['per_run_median_us'] = {'min': meds[0], 'median': statistics.median(meds), 'max': meds[-1]}
    # cluster bootstrap over runs
    rng = random.Random(seed)
    groups = [r['lat'] for r in runs if r['lat']]
    k = len(groups)
    bs = {'median': [], 'p90': [], 'p99': []}
    for _ in range(boot):
        x = sorted(v for _ in range(k) for v in groups[rng.randrange(k)])
        bs['median'].append(pct(x, 50))
        bs['p90'].append(pct(x, 90))
        bs['p99'].append(pct(x, 99))
    for key, vals in bs.items():
        vals.sort()
        s[key + '_ci95_us'] = [pct(vals, 2.5), pct(vals, 97.5)]
    s['bootstrap'] = {'type': 'cluster (runs resampled with replacement)', 'resamples': boot,
                      'seed': seed, 'interval': 'percentile 2.5/97.5'}
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='inp', required=True)
    ap.add_argument('--warmup', type=int, default=10)
    ap.add_argument('--boot', type=int, default=2000)
    ap.add_argument('--seed', type=int, default=20261127)
    ap.add_argument('--json', required=True)
    ap.add_argument('--csv', required=True)
    a = ap.parse_args()

    order = ['small_cross', 'small_same', 'image_cross_rel', 'image_same_rel',
             'image_cross_be', 'image_cross_rel_bigbuf']
    dirs = sorted(d for d in os.listdir(a.inp) if os.path.isdir(os.path.join(a.inp, d)))
    dirs.sort(key=lambda d: (order.index(d) if d in order else 99, d))
    out, per_run = [], []
    for d in dirs:
        p = os.path.join(a.inp, d)
        try:
            cfg = json.load(open(os.path.join(p, 'config.json')))
            cfg.pop('config', None)
        except OSError:
            cfg = {}
        runs = load_config(p, a.warmup)
        if not runs:
            continue
        out.append(summarise(d, runs, cfg, a.boot, a.seed, a.warmup))
        for r in runs:
            x = sorted(r['lat'])
            m = r['meta'] or {}
            per_run.append([d, r['run'], len(x),
                            round(pct(x, 50), 1) if x else '', round(pct(x, 99), 1) if x else '',
                            round(x[-1], 1) if x else '', m.get('unique', ''), m.get('expected', ''),
                            r['rcvbuf'] if r['rcvbuf'] is not None else ''])

    os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
    with open(a.json, 'w') as f:
        json.dump({'unit': 'microseconds', 'warmup_rule': 'seq < %d discarded per run' % a.warmup, 'measured': 'rclpy publish() call -> start of '
                   'subscriber callback, same host kernel clock', 'configs': out}, f, indent=1)

    def r1(v):
        return '' if v is None else round(v, 1)
    cols = ['config', 'topology', 'payload', 'reliability', 'rate_hz', 'n_runs', 'n_samples',
            'delivered_total', 'expected_total', 'min_us', 'median_us', 'median_ci_lo',
            'median_ci_hi', 'mean_us', 'p90_us', 'p90_ci_lo', 'p90_ci_hi', 'p99_us', 'p99_ci_lo',
            'p99_ci_hi', 'p999_us', 'max_us', 'run_median_min', 'run_median_med',
            'run_median_max', 'rcvbuf_errors_total', 'runs_with_rcvbuf_errors',
            'out_of_order', 'duplicates', 'bad_length', 'negative_latencies',
            'publish_call_median_us', 'publish_call_p99_us']
    with open(a.csv, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(cols)
        for s in out:
            if not s['n_samples']:
                continue
            w.writerow([s['config'], s.get('topology'), s.get('payload'), s.get('reliability'),
                        s.get('rate_hz'), s['n_runs'], s['n_samples'], s['delivered_total'],
                        s['expected_total'], r1(s['min_us']), r1(s['median_us']),
                        r1(s['median_ci95_us'][0]), r1(s['median_ci95_us'][1]), r1(s['mean_us']),
                        r1(s['p90_us']), r1(s['p90_ci95_us'][0]), r1(s['p90_ci95_us'][1]),
                        r1(s['p99_us']), r1(s['p99_ci95_us'][0]), r1(s['p99_ci95_us'][1]),
                        r1(s['p999_us']), r1(s['max_us']), r1(s['per_run_median_us']['min']),
                        r1(s['per_run_median_us']['median']), r1(s['per_run_median_us']['max']),
                        s['rcvbuf_errors_total'], s['runs_with_rcvbuf_errors'], s['out_of_order'],
                        s['duplicates'], s['bad_length'], s['negative_latencies'],
                        r1(s.get('publish_call_us', {}).get('median')),
                        r1(s.get('publish_call_us', {}).get('p99'))])
    with open(os.path.join(os.path.dirname(os.path.abspath(a.csv)), 'latency_runs.csv'), 'w',
              newline='') as f:
        w = csv.writer(f)
        w.writerow(['config', 'run', 'n_samples', 'median_us', 'p99_us', 'max_us', 'delivered',
                    'expected', 'rcvbuf_errors'])
        w.writerows(per_run)

    for s in out:
        if not s['n_samples']:
            print('%-24s no samples' % s['config']); continue
        print('%-24s runs=%d n=%d deliv=%d/%d med=%.0f [%.0f,%.0f] p90=%.0f p99=%.0f [%.0f,%.0f] '
              'max=%.0f us rcvbuf=%s neg=%d ooo=%d pubcall_med=%s'
              % (s['config'], s['n_runs'], s['n_samples'], s['delivered_total'],
                 s['expected_total'], s['median_us'], *s['median_ci95_us'], s['p90_us'],
                 s['p99_us'], *s['p99_ci95_us'], s['max_us'], s['rcvbuf_errors_total'],
                 s['negative_latencies'], s['out_of_order'],
                 r1(s.get('publish_call_us', {}).get('median'))))


if __name__ == '__main__':
    main()
