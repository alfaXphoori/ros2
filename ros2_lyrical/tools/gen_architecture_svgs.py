#!/usr/bin/env python3
"""Animated architecture SVGs for docs/04_architectures.md (part 4).

GitHub-safe: inline CSS + SMIL only, no scripts, no external assets.
Usage: python3 gen_architecture_svgs.py <out_dir>
"""
import math
import sys
from xml.sax.saxutils import escape as esc

OUT = sys.argv[1]

FONT = "'Segoe UI','Helvetica Neue',Arial,sans-serif"
MONO = "'JetBrains Mono',Consolas,Menlo,monospace"
C = dict(bg='#f6f8fa', card='#ffffff', line='#d0d7de', navy='#0f2239', ink='#57606a', faint='#8c959f',
         accent='#f86b1d', adeep='#dc5812', asoft='#fdecdd', blue='#2c5f9e', blue2='#3a6aa6', bsoft='#e3ecf7',
         green='#27a689', gdeep='#17765f', gsoft='#d9f0e8', amber='#e2962a', amdeep='#9a5b00', amsoft='#fdf1dc',
         purple='#8250df', psoft='#efe7fb', red='#cf222e', rsoft='#ffebe9', grey='#6e7781', gysoft='#eaeef2')
CSS = ('<style>.march{stroke-dasharray:6 6;animation:m 1s linear infinite}@keyframes m{to{stroke-dashoffset:-24}}'
       '.pulse{animation:p 1.6s ease-in-out infinite}@keyframes p{50%{opacity:.35}}</style>')


def text(x, y, s, size=13, fill=C['navy'], weight=400, family=FONT, anchor='start', extra=''):
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}" {extra}>{esc(str(s))}</text>')


def rect(x, y, w, h, fill, stroke='none', rx=8, sw=1.2, extra=''):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'


def line(x1, y1, x2, y2, col, sw=1.5, extra=''):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="{sw}" {extra}/>'


def dot(path, col, dur, r=5, begin='0s'):
    return (f'<circle r="{r}" fill="{col}" stroke="#fff" stroke-width="1.5">'
            f'<animateMotion dur="{dur}s" begin="{begin}" repeatCount="indefinite" path="{path}"/></circle>')


def head(W, H, title, sub, desc):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img">',
            f'<title>{esc(desc)}</title>', CSS, rect(0, 0, W, H, C['bg'], rx=18),
            text(40, 46, title, 24, weight=700), text(40, 70, sub, 12.5, C['faint'], family=MONO)]


def tag(x, y, w, label, col):
    return [rect(x, y, w, 26, col, rx=13), text(x + w / 2, y + 17.5, label, 12, '#fff', 700, anchor='middle')]


def blink(n, i, dur):
    """discrete opacity animation: element i of n is highlighted during its slot."""
    a, b = i / n, (i + 1) / n
    if i == 0:
        return (f'<animate attributeName="opacity" dur="{dur}s" repeatCount="indefinite" calcMode="discrete" '
                f'keyTimes="0;{b:.4f};1" values="1;0;0"/>')
    return (f'<animate attributeName="opacity" dur="{dur}s" repeatCount="indefinite" calcMode="discrete" '
            f'keyTimes="0;{a:.4f};{b:.4f};1" values="0;1;0;0"/>')


# ---------------------------------------------------------------- 1. rmw plugin + middleware internals
def rmw_svg():
    W, H = 1000, 860
    o = head(W, H, 'rmw is a plugin: four middleware architectures behind one C ABI',
             'RMW_IMPLEMENTATION picks the shared library at runtime · same rcl code, different internals',
             'ROS 2 Lyrical rmw plugin architecture and the internals of Fast DDS, Cyclone DDS, Zenoh and Connext')
    # common upper stack
    top = [('Application · rclcpp / rclpy', 'nodes · executors · callbacks'),
           ('rcl', 'graph · QoS · wait set · context'),
           ('rmw C ABI  (rmw_implementation dispatch)', 'dlopen(librmw_<name>.so) chosen by RMW_IMPLEMENTATION')]
    y = 92
    for i, (a, b) in enumerate(top):
        fill = C['asoft'] if i == 2 else C['card']
        o += [rect(60, y, 880, 44, fill, C['line'], 8), text(76, y + 20, a, 14, weight=700), text(76, y + 36, b, 11.5, C['ink'], family=MONO)]
        y += 52
    cols = [
        ('rmw_fastrtps_cpp', 'Fast DDS 3.6.x', 'default', C['accent'], C['asoft'], [
            ('DomainParticipant', '1 per context'),
            ('Publisher → DataWriter', 'history · QoS'),
            ('RTPS Stateful/Stateless', 'HEARTBEAT · ACKNACK'),
            ('FlowController', 'SYNCHRONOUS (default)'),
            ('Transports', 'UDPv4 · SHM · TCP'),
            ('threads', 'dds.udp.<port> · dds.ev')],
         'no daemon · DS optional'),
        ('rmw_cyclonedds_cpp', 'Cyclone DDS 11.0', 'Tier 1', C['blue'], C['bsoft'], [
            ('dds_domain', 'XML: CYCLONEDDS_URI'),
            ('writer · reader', 'WHC / RHC caches'),
            ('DDSI-RTPS core', 'SPDP · SEDP · reliability'),
            ('delivery queues', 'dq.builtins · dq.user'),
            ('Transports', 'UDP · TCP · iceoryx'),
            ('threads', 'recv · tev · gc  [K]')],
         'iox-roudi only when SHM is on'),
        ('rmw_zenoh_cpp', 'zenoh-c 1.x', 'Tier 1', C['amber'], C['amsoft'], [
            ('Zenoh session', 'mode: peer · 1 per context'),
            ('AdvancedPublisher', 'put() · pub cache'),
            ('liveliness tokens', '@ros2_lv/… = graph'),
            ('queryable / get', 'services'),
            ('Transports', 'tcp · udp · quic · tls · shm'),
            ('router rmw_zenohd', 'tcp/[::]:7447 · gossip')],
         'router required for discovery'),
        ('rmw_connextdds', 'Connext 7.7', 'no arm64', C['grey'], C['gysoft'], [
            ('DomainParticipant', 'RTI DDS'),
            ('DataWriter', 'history · QoS'),
            ('RTPS', 'standard wire'),
            ('XML QoS profiles', 'NDDS_QOS_PROFILES'),
            ('Transports', 'UDPv4 · SHM'),
            ('license', 'commercial / eval')],
         'details: vendor docs [K]'),
    ]
    cw, gap, x0, cy = 212, 11, 60, 270
    dur = 12
    for k, (pkg, mw, tier, col, soft, rows, foot) in enumerate(cols):
        x = x0 + k * (cw + gap)
        o += [line(500, y - 8, x + cw / 2, cy, C['line'], 1.5, 'stroke-dasharray="3 4"')]
        # highlight frame cycles through the four plugins
        o.append(f'<rect x="{x - 4}" y="{cy - 4}" width="{cw + 8}" height="{H - cy - 76}" rx="12" fill="none" '
                 f'stroke="{col}" stroke-width="3" opacity="0">{blink(4, k, dur)}</rect>')
        o += [rect(x, cy, cw, H - cy - 84, C['card'], col, 10, 1.6),
              rect(x, cy, cw, 54, col, rx=10), rect(x, cy + 40, cw, 14, col, rx=0),
              text(x + 12, cy + 22, pkg, 13, '#fff', 700, family=MONO), text(x + 12, cy + 42, f'{mw} · {tier}', 11, '#fff', family=MONO)]
        ry = cy + 66
        for j, (a, b) in enumerate(rows):
            o += [rect(x + 10, ry, cw - 20, 56, soft, 'none', 7), text(x + 20, ry + 23, a, 12.5, weight=700),
                  text(x + 20, ry + 42, b, 10.6, C['ink'], family=MONO)]
            if j < len(rows) - 1:
                o.append(line(x + cw / 2, ry + 56, x + cw / 2, ry + 64, col, 2))
            ry += 64
        o += [text(x + cw / 2, ry + 18, foot, 10.5, col if col != C['grey'] else C['ink'], 700, family=MONO, anchor='middle')]
        # data token falls through the column during its slot
        p = f'M{x + cw / 2} {cy + 60} L{x + cw / 2} {ry - 10}'
        o.append(f'<circle r="6" fill="{col}" stroke="#fff" stroke-width="2" opacity="0">{blink(4, k, dur)}'
                 f'<animateMotion dur="{dur / 4}s" repeatCount="indefinite" path="{p}"/></circle>')
    # env selector caption
    for k, (pkg, *_rest) in enumerate(cols):
        o.append(f'<g opacity="0">{blink(4, k, dur)}' + rect(300, H - 52, 400, 28, C['navy'], rx=14)
                 + text(500, H - 33, f'export RMW_IMPLEMENTATION={pkg}', 12.5, '#fff', 700, family=MONO, anchor='middle') + '</g>')
    o.append('</svg>')
    return '\n'.join(o)


# ---------------------------------------------------------------- 2. discovery architectures
def discovery_svg():
    W, H = 1000, 640
    o = head(W, H, 'Discovery architectures', 'who must talk to whom before the first sample can flow',
             'Three discovery architectures: DDS simple discovery, Fast DDS Discovery Server, Zenoh router')
    panels = [
        ('Simple discovery (DDS default)', C['accent'], C['asoft'], 'mesh',
         ['SPDP multicast 239.255.0.1:7400', 'SEDP unicast between every pair', 'traffic grows ~ N²', 'breaks on Wi-Fi / no multicast']),
        ('Fast DDS Discovery Server', C['blue'], C['bsoft'], 'server',
         ['ROS_DISCOVERY_SERVER=ip:11811', 'clients talk only to server(s)', 'data still peer-to-peer', 'ROS_SUPER_CLIENT for CLI tools']),
        ('Zenoh router (rmw_zenoh default)', C['amber'], C['amsoft'], 'router',
         ['rmw_zenohd tcp/[::]:7447', 'multicast scouting OFF', 'liveliness tokens via router', 'data peer-to-peer after match']),
    ]
    pw, gap, px0, py = 300, 20, 30, 96
    for k, (title, col, soft, kind, notes) in enumerate(panels):
        px = px0 + k * (pw + gap)
        o += [rect(px, py, pw, H - py - 30, C['card'], C['line'], 14, 1.5),
              rect(px, py, pw, 34, col, rx=14), rect(px, py + 18, pw, 16, col, rx=0),
              text(px + pw / 2, py + 23, title, 13.5, '#fff', 700, anchor='middle')]
        cx, cy, R = px + pw / 2, py + 200, 112
        n = 6
        pts = [(cx + R * math.cos(2 * math.pi * i / n - math.pi / 2), cy + R * math.sin(2 * math.pi * i / n - math.pi / 2)) for i in range(n)]
        if kind == 'mesh':
            for i in range(n):
                for j in range(i + 1, n):
                    o.append(line(*pts[i], *pts[j], col, 1.2, 'opacity=".55"'))
            # SEDP dots on a few edges
            for (i, j), d in zip([(0, 3), (1, 4), (2, 5), (0, 2), (3, 5)], [2.2, 2.6, 3.0, 2.4, 2.8]):
                o.append(dot(f'M{pts[i][0]:.1f} {pts[i][1]:.1f} L{pts[j][0]:.1f} {pts[j][1]:.1f}', col, d, 4))
            # multicast rings from node 0
            for b in (0, 0.8):
                o.append(f'<circle cx="{pts[0][0]:.1f}" cy="{pts[0][1]:.1f}" r="10" fill="none" stroke="{col}" stroke-width="2">'
                         f'<animate attributeName="r" values="10;150" dur="1.6s" begin="{b}s" repeatCount="indefinite"/>'
                         f'<animate attributeName="opacity" values=".8;0" dur="1.6s" begin="{b}s" repeatCount="indefinite"/></circle>')
            o.append(text(cx, cy + 4, f'{n}·{n - 1}/2 = {n * (n - 1) // 2} links', 12, C['adeep'], 700, family=MONO, anchor='middle'))
        else:
            label = 'DS' if kind == 'server' else 'router'
            for i, (x, y) in enumerate(pts):
                o.append(line(cx, cy, x, y, col, 1.6))
                o.append(dot(f'M{x:.1f} {y:.1f} L{cx} {cy}', col, 2.0 + 0.25 * i, 4))
            # data peer-to-peer between two matched nodes
            a, b = pts[1], pts[4]
            o.append(f'<path d="M{a[0]:.1f} {a[1]:.1f} Q {cx + 70} {cy + 20} {b[0]:.1f} {b[1]:.1f}" fill="none" stroke="{C["green"]}" stroke-width="2.4" class="march"/>')
            o.append(dot(f'M{a[0]:.1f} {a[1]:.1f} Q {cx + 70} {cy + 20} {b[0]:.1f} {b[1]:.1f}', C['green'], 1.6, 5))
            o += [f'<circle cx="{cx}" cy="{cy}" r="30" fill="{col}" class="pulse"/>',
                  text(cx, cy + 5, label, 13, '#fff', 700, anchor='middle')]
            if kind == 'server':
                bx, by = cx - 92, cy + 2
                o += [line(cx, cy, bx, by, col, 1.2, 'stroke-dasharray="4 4"'),
                      f'<circle cx="{bx}" cy="{by}" r="17" fill="#fff" stroke="{col}" stroke-width="2"/>',
                      text(bx, by + 4, 'DS2', 10.5, col, 700, anchor='middle'), text(bx, by + 32, 'backup', 10, C['ink'], family=MONO, anchor='middle')]
            o.append(text(cx + 70, cy + 40, 'data', 11, C['gdeep'], 700, family=MONO, anchor='middle'))
        for i, (x, y) in enumerate(pts):
            o += [f'<circle cx="{x:.1f}" cy="{y:.1f}" r="15" fill="#fff" stroke="{C["navy"]}" stroke-width="1.8"/>',
                  text(x, y + 4, f'n{i + 1}', 10.5, C['navy'], 700, anchor='middle')]
        ny = py + 350
        for i, s in enumerate(notes):
            o += [f'<circle cx="{px + 22}" cy="{ny + i * 26 - 4}" r="3.5" fill="{col}"/>', text(px + 34, ny + i * 26, s, 11.4, C['navy'], family=MONO)]
        o.append(rect(px + 16, H - 78, pw - 32, 30, soft, 'none', 8))
        foot = {'mesh': 'ROS_AUTOMATIC_DISCOVERY_RANGE', 'server': 'fastdds discovery …', 'router': 'ros2 run rmw_zenoh_cpp rmw_zenohd'}[kind]
        o.append(text(px + pw / 2, H - 58, foot, 11.2, C['navy'], 700, family=MONO, anchor='middle'))
    o.append('</svg>')
    return '\n'.join(o)


# ---------------------------------------------------------------- 3. communication patterns
def patterns_svg():
    W, H = 1000, 640
    o = head(W, H, 'Topic · Service · Action and how each RMW names them',
             'an action is not a new transport: it is 3 services + 2 topics',
             'ROS 2 communication patterns mapped to DDS topic names and Zenoh key expressions')
    # header row
    o += [text(40, 110, 'ROS ENTITY', 12, C['faint'], 700, extra='letter-spacing="2"'),
          text(370, 110, 'DDS TOPIC (Fast/Cyclone/Connext)', 12, C['faint'], 700, extra='letter-spacing="2"'),
          text(700, 110, 'ZENOH (rmw_zenoh_cpp)', 12, C['faint'], 700, extra='letter-spacing="2"')]
    rows = [
        ('Topic', '/chatter', C['accent'], [('rt/chatter', 'pub/sub')], [('0/chatter/<type>/<hash>', 'put / subscriber')]),
        ('Service', '/add_two_ints', C['blue'], [('rq/add_two_intsRequest', 'client → server'), ('rr/add_two_intsReply', 'server → client')],
         [('0/add_two_ints/<type>/<hash>', 'get → queryable')]),
        ('Action', '/fibonacci', C['purple'], [
            ('rq|rr …/_action/send_goal…', 'service'), ('rq|rr …/_action/cancel_goal…', 'service'),
            ('rq|rr …/_action/get_result…', 'service'), ('rt/fibonacci/_action/feedback', 'topic'),
            ('rt/fibonacci/_action/status', 'topic')],
         [('3 queryables + 2 publishers', 'same split, Zenoh keys')]),
    ]
    y = 126
    for name, ent, col, dds, zen in rows:
        h = max(len(dds) * 38 + 30, 96)
        o += [rect(30, y, 940, h, C['card'], C['line'], 12, 1.3), rect(30, y, 8, h, col, rx=4),
              text(52, y + 30, name, 17, col, 700), text(52, y + 52, ent, 12, C['navy'], family=MONO)]
        # little actor diagram
        ax, bx, my = 205, 340, y + 40
        o += [rect(ax - 26, my - 16, 52, 32, C['bsoft'] if name != 'Topic' else C['asoft'], col, 6),
              text(ax, my + 4, 'A', 12, col, 700, anchor='middle'),
              rect(bx - 36, my - 16, 52, 32, C['bsoft'] if name != 'Topic' else C['asoft'], col, 6),
              text(bx - 10, my + 4, 'B', 12, col, 700, anchor='middle')]
        if name == 'Topic':
            p = f'M{ax + 26} {my} L{bx - 36} {my}'
            o += [line(ax + 26, my, bx - 36, my, col, 2, 'class="march"'), dot(p, col, 1.2), dot(p, col, 1.2, begin='0.6s'),
                  text((ax + bx) / 2 - 5, my + 30, 'many, one-way', 10.5, C['ink'], family=MONO, anchor='middle')]
        elif name == 'Service':
            p1 = f'M{ax + 26} {my - 6} L{bx - 36} {my - 6}'
            p2 = f'M{bx - 36} {my + 6} L{ax + 26} {my + 6}'
            o += [line(ax + 26, my - 6, bx - 36, my - 6, col, 1.5), line(ax + 26, my + 6, bx - 36, my + 6, C['green'], 1.5),
                  f'<circle r="5" fill="{col}"><animateMotion dur="2.4s" repeatCount="indefinite" keyPoints="0;1;1" keyTimes="0;0.45;1" calcMode="linear" path="{p1}"/></circle>',
                  f'<circle r="5" fill="{C["green"]}"><animateMotion dur="2.4s" repeatCount="indefinite" keyPoints="0;0;1;1" keyTimes="0;0.5;0.95;1" calcMode="linear" path="{p2}"/></circle>',
                  text((ax + bx) / 2 - 5, my + 30, 'request → reply', 10.5, C['ink'], family=MONO, anchor='middle')]
        else:
            # goal -> accept -> feedback x3 -> result
            seq = [('goal', 0.00, 0.10, 1, col), ('accept', 0.12, 0.22, -1, C['green']),
                   ('fb', 0.30, 0.40, -1, C['amber']), ('fb', 0.45, 0.55, -1, C['amber']), ('fb', 0.60, 0.70, -1, C['amber']),
                   ('result', 0.78, 0.88, -1, C['green'])]
            for lab, a, b, d, cc in seq:
                p = f'M{ax + 26} {my} L{bx - 36} {my}' if d == 1 else f'M{bx - 36} {my} L{ax + 26} {my}'
                o.append(f'<circle r="5" fill="{cc}" opacity="0"><animate attributeName="opacity" dur="6s" repeatCount="indefinite" '
                         f'calcMode="discrete" keyTimes="0;{a};{b};1" values="0;1;0;0"/>'
                         f'<animateMotion dur="6s" repeatCount="indefinite" keyPoints="0;0;1;1" keyTimes="0;{a};{b};1" calcMode="linear" path="{p}"/></circle>')
            o += [line(ax + 26, my, bx - 36, my, col, 1.5),
                  text((ax + bx) / 2 - 5, my + 30, 'goal · feedback · result', 10.5, C['ink'], family=MONO, anchor='middle')]
        for i, (s, d) in enumerate(dds):
            yy = y + 16 + i * 38
            o += [rect(370, yy, 310, 30, C['asoft'] if 'rt/' in s else C['bsoft'], 'none', 6),
                  text(380, yy + 19, s, 11.2, C['navy'], 700, family=MONO), text(672, yy + 19, d, 10, C['ink'], family=MONO, anchor='end')]
        for i, (s, d) in enumerate(zen):
            yy = y + 16 + i * 38
            o += [rect(700, yy, 255, 46, C['amsoft'], 'none', 6),
                  text(710, yy + 19, s, 11.2, C['amdeep'], 700, family=MONO), text(710, yy + 37, d, 10, C['ink'], family=MONO)]
        y += h + 14
    o += [text(40, H - 46, 'DDS prefixes: rt/ = ROS topic · rq/ = request · rr/ = reply (rmw_dds_common naming)  [K]', 11, C['ink'], family=MONO),
          text(40, H - 28, 'Zenoh key: <domain>/<name>/<type>/<RIHS01 hash>  [V: rmw_zenoh docs/design.md, branch lyrical]', 11, C['ink'], family=MONO)]
    o.append('</svg>')
    return '\n'.join(o)


# ---------------------------------------------------------------- 4. intra-host data paths
def intrahost_svg():
    W, H = 1000, 720
    o = head(W, H, 'Same host, six data paths: how many times is the payload copied?',
             'publisher process → subscriber process (except intra-process) · copy counts are approximate [K]',
             'Intra-host data paths in ROS 2 Lyrical and their approximate payload copy counts')
    lanes = [
        ('intra-process', 'rclcpp IPC · same process', C['purple'], [('msg', 'move')], 0, 'unique_ptr hand-off, no rmw, no serialize'),
        ('UDP loopback', 'FASTDDS_BUILTIN_TRANSPORTS=UDPv4', C['blue'], [('CDR', 'copy'), ('sendmsg', 'copy'), ('recvmsg', 'copy'), ('deser.', 'copy')], 4, 'full kernel stack on lo'),
        ('Fast DDS SHM', 'default on same host', C['accent'], [('CDR', 'copy'), ('memcpy→seg', 'copy'), ('descriptor', 'ring'), ('deser.', 'copy')], 3, '512 KiB segment · 64 KB chunks'),
        ('Zenoh SHM', 'opt-in · ≥ 512 B', C['amber'], [('CDR→SHM', 'copy'), ('ref', 'ptr'), ('deser.', 'copy')], 2, 'serialize straight into pool'),
        ('loaned · data-sharing · iceoryx', 'plain / fixed-size types', C['green'], [('borrow', 'ptr'), ('write in place', 'ptr'), ('take', 'ptr')], 0, 'Fast DDS: off by default in rmw'),
        ('rosidl::Buffer (CUDA)', 'uint8[] backend · new in Lyrical', C['gdeep'], [('descriptor ≤ 4 KiB', 'msg'), ('GPU memory', 'stays')], 0, 'payload never touches host RAM path'),
    ]
    y0, lh = 98, 96
    x_src, x_dst = 260, 900
    dur = 5
    for k, (name, sub, col, steps, copies, note) in enumerate(lanes):
        y = y0 + k * lh
        o += [rect(30, y, 940, lh - 10, C['card'], C['line'], 12, 1.2), rect(30, y, 8, lh - 10, col, rx=4),
              text(50, y + 28, name, 14, col, 700), text(50, y + 47, sub, 10.6, C['ink'], family=MONO),
              text(50, y + 70, note, 10.3, C['faint'], family=MONO)]
        cy = y + 36
        o += [line(x_src, cy, x_dst, cy, col, 2, 'opacity=".35"')]
        n = len(steps)
        xs = [x_src + (x_dst - x_src) * (i + 0.5) / n for i in range(n)]
        for i, (s, kind) in enumerate(steps):
            is_copy = kind == 'copy'
            fill = C['rsoft'] if is_copy else (C['gsoft'] if kind in ('ptr', 'move', 'stays') else C['bsoft'])
            stroke = C['red'] if is_copy else col
            bw = max(84, len(s) * 7.6 + 20)
            o += [rect(xs[i] - bw / 2, cy - 15, bw, 30, fill, stroke, 7, 1.4),
                  text(xs[i], cy + 4, s, 11, C['navy'], 700, family=MONO, anchor='middle')]
            if is_copy:
                a = (i + 0.5) / n
                o.append(f'<text x="{xs[i]}" y="{cy - 20}" font-family="{MONO}" font-size="10.5" font-weight="700" fill="{C["red"]}" '
                         f'text-anchor="middle" opacity="0">copy<animate attributeName="opacity" dur="{dur}s" repeatCount="indefinite" '
                         f'calcMode="discrete" keyTimes="0;{a * 0.8:.3f};{min(a * 0.8 + 0.25, 0.99):.3f};1" values="0;1;0;0"/></text>')
        p = f'M{x_src - 10} {cy} L{x_dst + 10} {cy}'
        o.append(f'<circle r="7" fill="{col}" stroke="#fff" stroke-width="2"><animateMotion dur="{dur}s" repeatCount="indefinite" '
                 f'keyPoints="0;1;1" keyTimes="0;0.8;1" calcMode="linear" path="{p}"/></circle>')
        badge = C['red'] if copies >= 3 else (C['amber'] if copies else C['green'])
        o += [f'<circle cx="{x_dst + 40}" cy="{cy + 6}" r="20" fill="{badge}"/>',
              text(x_dst + 40, cy + 12, str(copies), 17, '#fff', 700, anchor='middle'),
              text(x_dst + 40, cy + 40, 'copies', 9.5, C['ink'], family=MONO, anchor='middle')]
    o += [text(40, H - 22, 'red = payload copy in user or kernel space · green = pointer / descriptor only · counts exclude NIC DMA and cache traffic', 10.8, C['ink'], family=MONO)]
    o.append('</svg>')
    return '\n'.join(o)


# ---------------------------------------------------------------- 5. deployment / fleet
def deployment_svg():
    W, H = 1000, 820
    o = head(W, H, 'Deployment architectures: one robot → fleet → cloud',
             'left: DDS on the robot LAN · right: Zenoh routers across NAT · bottom: micro-ROS on MCUs',
             'ROS 2 deployment architectures: multi-host robot, multi-robot fleet with domain bridge, Zenoh router mesh to the cloud, micro-ROS agent')

    def host(x, y, w, h, title, lines, col, soft):
        out = [rect(x, y, w, h, soft, col, 9, 1.5), text(x + 10, y + 20, title, 12.5, col, 700)]
        for i, s in enumerate(lines):
            out.append(text(x + 10, y + 38 + i * 16, s, 10.4, C['navy'], family=MONO))
        return out

    # ---- left panel: DDS LAN robot + domain bridge
    lx, ly, lw, lh = 30, 92, 460, 470
    o += [rect(lx, ly, lw, lh, C['card'], C['line'], 14, 1.5)] + tag(lx + 14, ly + 12, 230, 'A · DDS on a robot LAN', C['accent'])
    # robot 1
    o += [rect(lx + 14, ly + 52, 210, 300, '#fff', C['accent'], 12, 1.4, 'stroke-dasharray="5 4"'),
          text(lx + 24, ly + 72, 'robot_1 · ROS_DOMAIN_ID=11', 11.5, C['adeep'], 700, family=MONO)]
    o += host(lx + 26, ly + 84, 186, 82, 'compute (x86)', ['nav2 · perception', 'SHM inside host'], C['accent'], C['asoft'])
    o += host(lx + 26, ly + 182, 186, 82, 'sensor box (arm64)', ['lidar · camera drivers', 'UDP to compute'], C['accent'], C['asoft'])
    o += [line(lx + 119, ly + 166, lx + 119, ly + 182, C['accent'], 3, 'class="march"'),
          text(lx + 24, ly + 290, 'switch · multicast OK', 10.5, C['ink'], family=MONO),
          text(lx + 24, ly + 306, 'SPDP/SEDP stay inside', 10.5, C['ink'], family=MONO),
          text(lx + 24, ly + 322, 'the domain', 10.5, C['ink'], family=MONO)]
    # robot 2
    o += [rect(lx + 236, ly + 52, 210, 150, '#fff', C['accent'], 12, 1.4, 'stroke-dasharray="5 4"'),
          text(lx + 246, ly + 72, 'robot_2 · DOMAIN_ID=12', 11.5, C['adeep'], 700, family=MONO)]
    o += host(lx + 248, ly + 84, 186, 98, 'single computer', ['all nodes', 'ROS_AUTOMATIC_DISCOVERY', '_RANGE=LOCALHOST'], C['accent'], C['asoft'])
    # fleet manager + domain_bridge
    o += host(lx + 236, ly + 226, 210, 126, 'fleet server · DOMAIN 0', ['domain_bridge', '  11:/robot_1/odom → 0', '  12:/robot_2/odom → 0', 'only chosen topics cross'], C['blue'], C['bsoft'])
    p1 = f'M{lx + 212} {ly + 120} C {lx + 230} {ly + 160}, {lx + 230} {ly + 260}, {lx + 236} {ly + 280}'
    p2 = f'M{lx + 341} {ly + 202} L{lx + 341} {ly + 226}'
    o += [f'<path d="{p1}" fill="none" stroke="{C["blue"]}" stroke-width="2" class="march"/>', dot(p1, C['blue'], 2.2),
          f'<path d="{p2}" fill="none" stroke="{C["blue"]}" stroke-width="2" class="march"/>', dot(p2, C['blue'], 1.2)]
    o += [text(lx + 14, ly + 376, 'Isolation by ROS_DOMAIN_ID (ports 7400+250·id).', 10.8, C['navy'], family=MONO),
          text(lx + 14, ly + 394, 'Safe range on Linux: 0–101 (ephemeral ports).', 10.8, C['navy'], family=MONO),
          text(lx + 14, ly + 412, 'Namespaces (/robot_1/…) keep names unique when', 10.8, C['navy'], family=MONO),
          text(lx + 14, ly + 430, 'topics are bridged into one shared domain.', 10.8, C['navy'], family=MONO),
          text(lx + 14, ly + 452, 'Across routers: Discovery Server or ROS_STATIC_PEERS.', 10.8, C['adeep'], 700, family=MONO)]

    # ---- right panel: Zenoh router mesh with cloud
    rx, ry, rw, rh = 510, 92, 460, 470
    o += [rect(rx, ry, rw, rh, C['card'], C['line'], 14, 1.5)] + tag(rx + 14, ry + 12, 260, 'B · Zenoh routers to the cloud', C['amber'])
    # cloud
    o += [rect(rx + 130, ry + 52, 200, 92, C['amsoft'], C['amber'], 40, 1.6),
          text(rx + 230, ry + 82, 'cloud / edge', 13, C['amdeep'], 700, anchor='middle'),
          text(rx + 230, ry + 100, 'rmw_zenohd', 11, C['navy'], family=MONO, anchor='middle'),
          text(rx + 230, ry + 116, 'listen tls/0.0.0.0:7447', 10.5, C['navy'], family=MONO, anchor='middle'),
          text(rx + 230, ry + 132, 'ACL per robot', 10.5, C['navy'], family=MONO, anchor='middle')]
    # NAT line
    o += [line(rx + 20, ry + 186, rx + rw - 20, ry + 186, C['red'], 1.5, 'stroke-dasharray="8 6"'),
          rect(rx + rw / 2 - 90, ry + 176, 180, 20, C['rsoft'], C['red'], 10),
          text(rx + rw / 2, ry + 190, 'NAT · firewall · 4G/5G', 10.5, C['red'], 700, family=MONO, anchor='middle')]
    for i, nm in enumerate(['robot_1', 'robot_2', 'robot_3']):
        bx = rx + 20 + i * 146
        o += [rect(bx, ry + 226, 130, 170, '#fff', C['amber'], 12, 1.4, 'stroke-dasharray="5 4"'),
              text(bx + 10, ry + 246, nm, 12, C['amdeep'], 700, family=MONO),
              f'<circle cx="{bx + 65}" cy="{ry + 280}" r="20" fill="{C["amber"]}" class="pulse"/>',
              text(bx + 65, ry + 284, 'router', 10.5, '#fff', 700, anchor='middle')]
        for j in range(3):
            nx, ny = bx + 25 + j * 40, ry + 350
            o += [line(bx + 65, ry + 300, nx, ny - 12, C['amber'], 1.2),
                  f'<circle cx="{nx}" cy="{ny}" r="12" fill="#fff" stroke="{C["navy"]}" stroke-width="1.5"/>',
                  text(nx, ny + 4, 'n', 10, C['navy'], 700, anchor='middle')]
        o.append(text(bx + 65, ry + 386, 'peers on host', 9.8, C['ink'], family=MONO, anchor='middle'))
        p = f'M{bx + 65} {ry + 260} L{rx + 230} {ry + 144}'
        o += [f'<path d="{p}" fill="none" stroke="{C["amber"]}" stroke-width="2.4" class="march"/>', dot(p, C['amber'], 1.8 + i * 0.3)]
    o += [text(rx + 14, ry + 420, 'robot router: connect/endpoints=["tls/<cloud>:7447"]', 10.6, C['navy'], family=MONO),
          text(rx + 14, ry + 438, 'outbound TCP/TLS only → works behind NAT', 10.6, C['navy'], family=MONO),
          text(rx + 14, ry + 456, 'alt: zenoh-bridge-ros2dds next to a DDS robot', 10.6, C['amdeep'], 700, family=MONO)]

    # ---- bottom: micro-ROS
    by = 580
    o += [rect(30, by, 940, 210, C['card'], C['line'], 14, 1.5)] + tag(44, by + 12, 270, 'C · micro-ROS on microcontrollers', C['purple'])
    o += host(60, by + 56, 220, 112, 'MCU (STM32 · ESP32 · RP2040)', ['rclc + micro-ROS client', 'Micro XRCE-DDS client', 'no OS / FreeRTOS / Zephyr'], C['purple'], C['psoft'])
    o += host(390, by + 56, 220, 112, 'micro_ros_agent (Linux)', ['XRCE-DDS agent', 'creates real DDS entities', 'on behalf of the MCU'], C['purple'], C['psoft'])
    o += host(720, by + 56, 220, 112, 'ROS 2 graph', ['normal DDS participants', 'see the MCU as a node', '(DDS RMW only)'], C['accent'], C['asoft'])
    p1 = f'M280 {by + 112} L390 {by + 112}'
    p2 = f'M610 {by + 112} L720 {by + 112}'
    o += [line(280, by + 112, 390, by + 112, C['purple'], 2.4, 'class="march"'), dot(p1, C['purple'], 1.4),
          text(335, by + 102, 'serial · UDP', 10.5, C['purple'], 700, family=MONO, anchor='middle'),
          text(335, by + 132, 'XRCE', 10.5, C['purple'], family=MONO, anchor='middle'),
          line(610, by + 112, 720, by + 112, C['accent'], 2.4, 'class="march"'), dot(p2, C['accent'], 1.4),
          text(665, by + 102, 'RTPS', 10.5, C['adeep'], 700, family=MONO, anchor='middle'),
          text(60, by + 192, 'Lyrical status of micro-ROS packages not verified here: check the micro-ROS repos for a lyrical branch before planning on it.', 10.6, C['ink'], family=MONO)]
    o.append('</svg>')
    return '\n'.join(o)


# ---------------------------------------------------------------- 6. security
def security_svg():
    W, H = 1000, 640
    o = head(W, H, 'Security architecture: SROS2 (DDS-Security) and Zenoh',
             'identity per enclave · policy as signed XML · encryption in the middleware, not the kernel',
             'ROS 2 security architecture: SROS2 keystore and DDS-Security plugins compared with Zenoh TLS and ACL')
    # keystore
    o += [rect(30, 96, 300, 500, C['card'], C['line'], 14, 1.5)] + tag(44, 108, 200, 'keystore (ros2 security)', C['navy'])
    files = [('public/', 'ca / identity_ca / permissions_ca certs'), ('private/', 'CA keys (keep offline)'),
             ('enclaves/', 'governance.xml · governance.p7s'), ('enclaves/<name>/', 'cert.pem · key.pem'),
             ('enclaves/<name>/', 'permissions.xml · permissions.p7s'), ('enclaves/<name>/', 'governance.p7s · CA certs')]
    for i, (a, b) in enumerate(files):
        y = 150 + i * 42
        o += [rect(46, y, 268, 34, C['gysoft'], 'none', 6), text(56, y + 15, a or '·', 10.5, C['ink'], 700, family=MONO),
              text(56, y + 28, b, 10.5, C['navy'], family=MONO)]
    o += [text(46, 432, 'ROS_SECURITY_KEYSTORE=<dir>', 10.8, C['navy'], 700, family=MONO),
          text(46, 450, 'ROS_SECURITY_ENABLE=true', 10.8, C['navy'], 700, family=MONO),
          text(46, 468, 'ROS_SECURITY_STRATEGY=Enforce', 10.8, C['navy'], 700, family=MONO),
          text(46, 492, 'node --ros-args --enclave /robot/nav', 10.8, C['adeep'], 700, family=MONO),
          text(46, 520, 'Fast DDS .deb for Lyrical is built', 10.4, C['ink'], family=MONO),
          text(46, 536, 'with -DSECURITY=ON (see part 2 §3.7)', 10.4, C['ink'], family=MONO),
          text(46, 560, 'source build w/o flag → no security', 10.4, C['red'], 700, family=MONO)]
    # DDS security plugins
    o += [rect(350, 96, 330, 500, C['card'], C['line'], 14, 1.5)] + tag(364, 108, 230, 'DDS-Security plugins (OMG)', C['accent'])
    plugins = [('Authentication', 'DDS:Auth:PKI-DH', 'X.509 cert + DH handshake', C['accent']),
               ('Access Control', 'DDS:Access:Permissions', 'governance + permissions XML', C['blue']),
               ('Cryptographic', 'DDS:Crypto:AES-GCM-GMAC', 'encrypt / sign submessages', C['purple']),
               ('Logging (optional)', 'DDS:Logging:DDS_LogTopic', 'security events', C['grey'])]
    for i, (a, b, c, col) in enumerate(plugins):
        y = 150 + i * 84
        o += [rect(366, y, 298, 72, '#fff', col, 9, 1.6), rect(366, y, 7, 72, col, rx=3),
              text(384, y + 22, a, 13.5, col, 700), text(384, y + 42, b, 10.6, C['navy'], family=MONO), text(384, y + 60, c, 10.4, C['ink'], family=MONO)]
    o += [text(366, 506, 'on the wire: SRTPS_PREFIX / SEC_PREFIX', 10.8, C['navy'], 700, family=MONO),
          text(366, 524, 'wrap encrypted RTPS submessages; UDP,', 10.6, C['ink'], family=MONO),
          text(366, 542, 'IP and port numbers stay in clear text.', 10.6, C['ink'], family=MONO),
          text(366, 566, 'Discovery itself can be protected via', 10.6, C['ink'], family=MONO),
          text(366, 582, 'governance (enable_discovery_protection).', 10.6, C['ink'], family=MONO)]
    # handshake animation keystore -> plugins
    for i, b in enumerate((0, 0.6, 1.2)):
        p = f'M314 {192 + i * 84} L366 {186 + i * 84}'
        o += [line(314, 192 + i * 84, 366, 186 + i * 84, C['line'], 1.5, 'stroke-dasharray="3 4"'), dot(p, C['navy'], 1.8, 4, f'{b}s')]
    # Zenoh column
    o += [rect(700, 96, 270, 500, C['card'], C['line'], 14, 1.5)] + tag(714, 108, 200, 'rmw_zenoh_cpp', C['amber'])
    z = [('link', 'TLS / mTLS (tls/… endpoints)', C['amber']), ('auth', 'usrpwd or certificate', C['amber']),
         ('ACL', 'allow/deny per key expr', C['amber']), ('tool', 'zenoh_security_tools', C['amdeep'])]
    for i, (a, b, col) in enumerate(z):
        y = 150 + i * 70
        o += [rect(716, y, 238, 58, C['amsoft'], col, 9, 1.4), text(728, y + 22, a, 13, col, 700), text(728, y + 42, b, 10.4, C['navy'], family=MONO)]
    o += [text(716, 448, 'zenoh_security_tools builds Zenoh', 10.5, C['ink'], family=MONO),
          text(716, 464, 'configs from SROS2-style policies', 10.5, C['ink'], family=MONO),
          text(716, 480, '[package exists in Lyrical; behaviour', 10.5, C['ink'], family=MONO),
          text(716, 496, ' not verified here]', 10.5, C['ink'], family=MONO),
          text(716, 526, 'encryption is per TCP/TLS link,', 10.5, C['navy'], 700, family=MONO),
          text(716, 542, 'not per message: the router can', 10.5, C['navy'], 700, family=MONO),
          text(716, 558, 'read payloads it forwards.', 10.5, C['navy'], 700, family=MONO)]
    o.append('</svg>')
    return '\n'.join(o)


SVGS = {
    'anim-arch-rmw-plugin.svg': rmw_svg,
    'anim-arch-discovery.svg': discovery_svg,
    'anim-arch-comm-patterns.svg': patterns_svg,
    'anim-arch-intrahost-datapaths.svg': intrahost_svg,
    'anim-arch-deployment.svg': deployment_svg,
    'anim-arch-security.svg': security_svg,
}
for name, fn in SVGS.items():
    with open(f'{OUT}/{name}', 'w') as f:
        f.write(fn())
print('ok', len(SVGS))
