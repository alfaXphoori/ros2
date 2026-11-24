#!/usr/bin/env python3
"""Generate two animated SVGs for the Lyrical docs (GitHub-safe: inline CSS + SMIL, no external assets)."""
import sys
from xml.sax.saxutils import escape as esc

OUT = sys.argv[1]

FONT = "'Segoe UI','Helvetica Neue',Arial,sans-serif"
MONO = "'JetBrains Mono',Consolas,Menlo,monospace"
C = dict(bg='#f6f8fa', card='#ffffff', line='#d0d7de', navy='#0f2239', ink='#57606a', faint='#8c959f',
         accent='#f86b1d', adeep='#dc5812', asoft='#fdecdd', blue='#2c5f9e', blue2='#3a6aa6', green='#27a689',
         gsoft='#d9f0e8', amber='#e2962a', purple='#8250df', bsoft='#e3ecf7', nsoft='#e6e9ef')

def text(x, y, s, size=13, fill=C['navy'], weight=400, family=FONT, anchor='start', extra=''):
    return f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" {extra}>{esc(s)}</text>'

def rect(x, y, w, h, fill, stroke='none', rx=8, sw=1.2, extra=''):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'

# ---------------------------------------------------------------- 1. stack diagram
def stack_svg():
    W, H = 1000, 1020
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img">',
         '<title>ROS 2 Lyrical Luth network stack: user space, kernel space, between hosts</title>',
         '<style>.march{stroke-dasharray:6 6;animation:m 1s linear infinite}@keyframes m{to{stroke-dashoffset:-24}}'
         '.pulse{animation:p 1.6s ease-in-out infinite}@keyframes p{50%{opacity:.35}}</style>',
         rect(0, 0, W, H, C['bg'], rx=18),
         text(40, 46, 'ROS 2 Lyrical Luth · network stack', 24, weight=700),
         text(40, 70, 'user space → syscalls → kernel → wire → other hosts   (Fast DDS 3.6 default · Cyclone 11 · Zenoh · Connext 7.7)', 12.5, C['faint'], family=MONO)]

    # USER SPACE panel
    ux, uy, uw, uh = 30, 92, 940, 480
    o += [rect(ux, uy, uw, uh, C['card'], C['line'], 14, 1.5),
          rect(ux, uy, 250, 30, C['accent'], rx=14), rect(ux, uy+14, 250, 16, C['accent'], rx=0),
          text(ux+16, uy+21, 'USER SPACE · node process', 13, '#fff', 700)]
    rows = [
        ('Application code', 'rclcpp / rclpy · topics · services · actions', '#ffffff'),
        ('Executor', 'SingleThreaded · MultiThreaded · EventsExecutor · EventsCBGExecutor (new)', '#ffffff'),
        ('rcl', 'graph · QoS · wait set · guard condition · CFT capability query (new)', '#eef1f4'),
        ('rmw', 'C ABI: rmw_publish · rmw_take · rmw_wait · rmw_borrow_loaned_message', '#fde3cd'),
        ('rosidl typesupport', 'serialize → CDR  (Fast-CDR 2.3.x · Cyclone serdata · Zenoh CDR)', '#fde3cd'),
        ('rosidl::Buffer backend', 'CPU | CUDA | …  → send a descriptor (≤ 4096 B) instead of the payload  (new)', C['gsoft']),
    ]
    ry = uy + 46
    rx0, rw = ux + 120, 700
    for i, (t, d, f) in enumerate(rows):
        y = ry + i*52
        o += [rect(rx0, y, rw, 42, f, C['line'], 8), text(rx0+14, y+18, t, 13.5, weight=700), text(rx0+14, y+34, d, 11.5, C['ink'], family=MONO)]
    # intra-process shortcut on the left
    loop = f'M{rx0-4} {ry+12} C {ux+30} {ry+4}, {ux+30} {ry+38}, {rx0-4} {ry+32}'
    o += [f'<path d="{loop}" fill="none" stroke="{C["purple"]}" stroke-width="2" class="march"/>',
          text(ux+14, ry+70, 'intra-process', 11.5, C['purple'], 700), text(ux+14, ry+85, 'unique_ptr', 11, C['purple'], family=MONO),
          text(ux+14, ry+100, 'skips rmw', 11, C['purple'], family=MONO)]
    o += [f'<circle r="5" fill="{C["purple"]}"><animateMotion dur="1.6s" repeatCount="indefinite" path="{loop}"/></circle>']
    # right column: what is new tag
    o += [rect(rx0+rw+14, ry, 92, 302, C['asoft'], '#f6c9a8', 8),
          text(rx0+rw+60, ry+24, 'Lyrical', 12, C['adeep'], 700, anchor='middle'),
          text(rx0+rw+60, ry+40, 'changes', 12, C['adeep'], 700, anchor='middle')]
    for k, s in enumerate(['EventsCBG', 'executor', '', 'CFT query', '', 'uint8[] →', 'rosidl::', 'Buffer']):
        o.append(text(rx0+rw+60, ry+70+k*16, s, 11, C['ink'], family=MONO, anchor='middle'))
    # divider + middleware
    my = ry + 6*52 + 10
    o += [f'<line x1="{ux+20}" y1="{my}" x2="{ux+uw-20}" y2="{my}" stroke="{C["line"]}" stroke-width="1.5"/>',
          text(ux+20, my+26, 'Middleware', 14, weight=700)]
    vend = [('Fast DDS 3.6', 'default', C['accent']), ('Cyclone DDS 11', '+ iceoryx', C['blue']), ('Zenoh (zenoh-c)', 'router 7447', C['amber']), ('Connext 7.7', 'not arm64', C['ink'])]
    for k, (n, s, col) in enumerate(vend):
        x = ux + 120 + k*172
        o += [rect(x, my+10, 160, 44, '#fff', col, 8, 1.8), text(x+14, my+30, n, 13.5, col, 700), text(x+14, my+46, s, 11, C['ink'], family=MONO)]
    o += [text(ux+20, my+82, 'Transports', 14, weight=700),
          text(ux+130, my+82, 'UDPv4/v6 · TCP · SHM · Data-sharing   |   Zenoh: tcp · udp · quic · tls · shm', 12, C['ink'], family=MONO)]

    # syscall bridges
    by0, by1 = uy + uh, 660
    lx, rx = 260, 857
    o += [f'<line x1="{lx}" y1="{by0}" x2="{lx}" y2="{by1}" stroke="{C["blue"]}" stroke-width="3" class="march"/>',
          f'<line x1="{rx}" y1="{by0}" x2="{rx}" y2="{by1}" stroke="{C["green"]}" stroke-width="3" class="march"/>',
          text(lx+14, by0+22, 'sendmsg / sendmmsg · recvmsg', 12, C['blue'], 700, family=MONO),
          text(lx+14, by0+40, 'epoll_wait · setsockopt', 12, C['blue'], family=MONO),
          text(rx-14, by0+28, 'mmap(/dev/shm) · futex', 12, C['green'], 700, family=MONO, anchor='end'),
          text(rx-14, by0+46, 'eventfd / semaphore', 12, C['green'], family=MONO, anchor='end'),
          f'<line x1="{ux}" y1="{by0+68}" x2="{ux+uw}" y2="{by0+68}" stroke="{C["adeep"]}" stroke-width="1.5" stroke-dasharray="8 6" opacity=".7"/>',
          rect(500-90, by0+58, 180, 20, C['asoft'], '#f6c9a8', 10), text(500, by0+72, 'user / kernel boundary', 11.5, C['adeep'], 700, anchor='middle')]

    # KERNEL panel
    kx, ky, kw, kh = 30, 660, 940, 200
    o += [rect(kx, ky, kw, kh, '#ffffff', C['line'], 14, 1.5),
          rect(kx, ky, 200, 30, C['blue'], rx=14), rect(kx, ky+14, 200, 16, C['blue'], rx=0),
          text(kx+16, ky+21, 'KERNEL SPACE', 13, '#fff', 700)]
    krow = [
        ('TX', 'socket (sk_buff · SO_SNDBUF) → UDP / TCP → IPv4/IPv6 (fragment) → netfilter → qdisc → driver → NIC DMA'),
        ('RX', 'NIC → IRQ → NAPI poll → GRO → ip_rcv (reassembly) → udp_rcv → socket queue (SO_RCVBUF) → wake epoll'),
    ]
    for k, (tag, s) in enumerate(krow):
        y = ky + 46 + k*52
        col = C['blue'] if tag == 'TX' else C['blue2']
        o += [rect(kx+20, y, 40, 40, col, rx=8), text(kx+40, y+25, tag, 13, '#fff', 700, anchor='middle'),
              rect(kx+70, y, 650, 40, C['bsoft'], '#c4d4ea', 8), text(kx+82, y+25, s, 10.1, C['navy'], family=MONO)]
    # shm pages box
    o += [rect(760, ky+46, 190, 92, C['gsoft'], C['green'], 8, 1.5),
          text(855, ky+82, 'tmpfs / shm pages', 13.5, '#17765f', 700, anchor='middle'),
          text(855, ky+102, 'no socket · no copy_to_user', 11, '#17765f', family=MONO, anchor='middle'),
          text(855, ky+120, 'same host only', 11, '#17765f', family=MONO, anchor='middle')]
    o += [text(kx+20, ky+180, 'drops show up as  UdpRcvbufErrors · ReasmFails · kfree_skb(reason)', 11.5, C['ink'], family=MONO)]

    # wire
    wy0, wy1 = ky+kh, 910
    o += [f'<line x1="{lx}" y1="{wy0}" x2="{lx}" y2="{wy1}" stroke="{C["navy"]}" stroke-width="4"/>',
          text(lx+16, wy0+30, 'Ethernet · Wi-Fi · TSN · 5G', 12.5, C['navy'], 700, family=MONO)]
    # INTER-HOST panel
    ix, iy, iw, ih = 30, 910, 940, 92
    o += [rect(ix, iy, iw, ih, '#ffffff', C['line'], 14, 1.5),
          rect(ix, iy, 210, 30, C['navy'], rx=14), rect(ix, iy+14, 210, 16, C['navy'], rx=0),
          text(ix+16, iy+21, 'BETWEEN HOSTS', 13, '#fff', 700),
          text(ix+230, iy+21, 'L2 switch (IGMP snooping) · L3 router (no multicast without PIM) · VPN / NAT', 11.5, C['ink'], family=MONO),
          rect(ix+20, iy+42, 440, 36, C['asoft'], '#f6c9a8', 8), text(ix+34, iy+65, 'DDS: SPDP multicast 239.255.0.1:7400 + unicast', 11.5, C['adeep'], 700, family=MONO),
          rect(ix+480, iy+42, 440, 36, '#fdf1dc', '#f0cf94', 8), text(ix+494, iy+65, 'Zenoh: router ↔ router TCP 7447 (gossip)', 11.5, '#9a5b00', 700, family=MONO)]
    # SPDP ring pulse
    o += [f'<circle cx="{ix+455}" cy="{iy+60}" r="4" fill="none" stroke="{C["accent"]}" stroke-width="2"><animate attributeName="r" values="4;16" dur="1.6s" repeatCount="indefinite"/><animate attributeName="opacity" values="1;0" dur="1.6s" repeatCount="indefinite"/></circle>']

    # moving packets: network path (left bridge) and SHM path (right bridge)
    vx = rx0 - 12
    net = f'M{rx0+30} {ry+21} L{vx} {ry+21} L{vx} {my+66} L{lx} {my+66} L{lx} {ky+44} L{kx+720} {ky+44} L{kx+720} {ky+98} L{lx} {ky+98} L{lx} {iy+60} L{ix+455} {iy+60}'
    o += [f'<path d="{net}" fill="none" stroke="{C["accent"]}" stroke-width="1.5" stroke-dasharray="2 6" opacity=".5"/>',
          f'<circle r="11" fill="{C["accent"]}" opacity=".25"><animateMotion dur="7s" repeatCount="indefinite" path="{net}"/></circle>',
          f'<circle r="7" fill="{C["accent"]}" stroke="#fff" stroke-width="2"><animateMotion dur="7s" repeatCount="indefinite" path="{net}"/>'
          f'<animate attributeName="fill" dur="7s" repeatCount="indefinite" values="{C["accent"]};{C["amber"]};{C["amber"]}" keyTimes="0;0.16;1"/></circle>']
    shm = f'M{rx0+rw} {ry+3*52+21} L{rx} {ry+3*52+21} L{rx} {ky+60} L{rx} {ry+3*52+21} L{rx0+rw} {ry+3*52+21}'
    o += [f'<circle r="6" fill="{C["green"]}" stroke="#fff" stroke-width="2"><animateMotion dur="5s" repeatCount="indefinite" path="{shm}"/></circle>']
    o.append('</svg>')
    return '\n'.join(o)

# ---------------------------------------------------------------- 2. OSI vs ROS 2 Lyrical
def osi_svg():
    W, H = 1000, 760
    rows = [  # L, OSI name, osi sub, PDU segments, ROS title, ROS detail, space
        (7, 'Application', 'HTTP · MQTT', [('msg', C['accent'])], 'App · rclcpp / rclpy · rcl', 'topic · service · action · executor', 'user'),
        (6, 'Presentation', 'encoding · TLS', [('CDR', C['amber'])], 'rosidl typesupport', 'CDR serialize · rosidl::Buffer descriptor', 'user'),
        (5, 'Session', 'session · sync', [('RTPS', C['purple']), ('CDR', C['amber'])], 'Middleware (DDS-RTPS / Zenoh)', 'SPDP/SEDP · QoS match · HEARTBEAT/ACKNACK', 'user'),
        (4, 'Transport', 'TCP · UDP', [('UDP', C['blue']), ('RTPS', C['purple']), ('CDR', C['amber'])], 'UDP / TCP · SHM bypass', 'ports 7400+250·domain · Zenoh TCP 7447', 'kernel'),
        (3, 'Network', 'IP · routing', [('IP', C['blue2']), ('UDP', C['blue']), ('RTPS', C['purple']), ('CDR', C['amber'])], 'IPv4 / IPv6', 'fragment @ MTU · multicast 239.255.0.1', 'kernel'),
        (2, 'Data Link', 'Ethernet · Wi-Fi MAC', [('ETH', C['navy']), ('IP', C['blue2']), ('UDP', C['blue']), ('RTPS', C['purple']), ('CDR', C['amber']), ('FCS', C['navy'])], 'Driver · NIC · switch', 'NAPI · GRO · VLAN · TSN 802.1Qbv', 'kernel'),
        (1, 'Physical', 'cable · radio', [('0 1 1 0 1 0 0 1 …', '#57606a')], 'PHY · cable · Wi-Fi · 5G', 'bits on the medium', 'hw'),
    ]
    top, rh = 118, 80
    ox, ow = 24, 220
    lx, lw = 276, 324
    gx, gw = 636, 300
    bx = 950
    N = 16  # animation steps: 0-6 TX down, 7-13 RX up, 14-15 hold
    dur = 13
    yc = lambda L: top + (7-L)*rh + rh/2 - 6

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img">',
         '<title>OSI 7-layer model compared with ROS 2 Lyrical Luth</title>',
         rect(0, 0, W, H, C['bg'], rx=18),
         text(40, 44, 'OSI 7 layers  vs  ROS 2 Lyrical Luth', 24, weight=700),
         text(40, 68, 'one message: encapsulate on the way down (TX), decapsulate on the way up (RX) · mapping is approximate', 12.5, C['faint'], family=MONO),
         text(ox, top-14, 'OSI MODEL', 12, C['faint'], 700, extra='letter-spacing="2"'),
         text(lx, top-14, 'WHAT IS ON THE WIRE AT THIS LAYER', 12, C['faint'], 700, extra='letter-spacing="2"'),
         text(gx, top-14, 'ROS 2 LYRICAL', 12, C['faint'], 700, extra='letter-spacing="2"')]

    def active_vals(L):
        s1, s2 = 7-L, 6+L
        if s1 + 1 >= s2:  # L1: contiguous
            return f'0;{s1/N:.4f};{(s2+1)/N:.4f};1', '0;1;0;0'
        return f'0;{s1/N:.4f};{(s1+1)/N:.4f};{s2/N:.4f};{(s2+1)/N:.4f};1', '0;1;0;1;0;0'

    for (L, name, sub, segs, rt, rd, space) in rows:
        y = top + (7-L)*rh
        kt, vals = active_vals(L)
        def anim(attr, a, b):
            vv = ';'.join(b if v == '1' else a for v in vals.split(';'))
            return f'<animate attributeName="{attr}" dur="{dur}s" repeatCount="indefinite" calcMode="discrete" keyTimes="{kt}" values="{vv}"/>'
        # OSI box
        o += [f'<rect x="{ox}" y="{y}" width="{ow}" height="{rh-12}" rx="10" fill="#ffffff" stroke="{C["line"]}" stroke-width="1.5">{anim("stroke", C["line"], C["accent"])}{anim("fill", "#ffffff", C["asoft"])}</rect>',
              rect(ox+12, y+14, 40, 40, C['navy'], rx=8), text(ox+32, y+40, str(L), 18, '#fff', 700, anchor='middle'),
              text(ox+64, y+32, name, 16, weight=700), text(ox+64, y+50, sub, 11.5, C['ink'], family=MONO)]
        # PDU lane
        o.append(f'<g opacity=".28">{anim("opacity", ".28", "1")}')
        if L == 1:
            o += [rect(lx, y+18, lw, 32, '#ffffff', C['line'], 6), text(lx+lw/2, y+39, segs[0][0], 13, segs[0][1], 700, family=MONO, anchor='middle')]
        else:
            total = sum(max(44, len(s)*9+18) for s, _ in segs)
            x = lx + (lw - total)/2
            for s, col in segs:
                w = max(44, len(s)*9+18)
                o += [rect(x, y+18, w-3, 32, col, rx=5), text(x+(w-3)/2, y+39, s, 12, '#fff', 700, family=MONO, anchor='middle')]
                x += w
        o.append('</g>')
        # ROS box
        o += [f'<rect x="{gx}" y="{y}" width="{gw}" height="{rh-12}" rx="10" fill="#ffffff" stroke="{C["line"]}" stroke-width="1.5">{anim("stroke", C["line"], C["accent"])}{anim("fill", "#ffffff", C["asoft"])}</rect>',
              text(gx+14, y+30, rt, 14, weight=700), text(gx+14, y+50, rd, 10.4, C['ink'], family=MONO)]
        # connectors
        o += [f'<line x1="{ox+ow}" y1="{y+34}" x2="{lx}" y2="{y+34}" stroke="{C["line"]}" stroke-width="1.5" stroke-dasharray="3 4"/>',
              f'<line x1="{lx+lw}" y1="{y+34}" x2="{gx}" y2="{y+34}" stroke="{C["line"]}" stroke-width="1.5" stroke-dasharray="3 4"/>']

    # space band
    bands = [('USER SPACE', 7, 5, C['accent']), ('KERNEL', 4, 2, C['blue']), ('HW', 1, 1, C['navy'])]
    for lab, a, b, col in bands:
        y0 = top + (7-a)*rh; y1 = top + (7-b)*rh + rh - 12
        cy = (y0+y1)/2
        o += [rect(bx, y0, 22, y1-y0, col, rx=6),
              f'<text x="{bx+11}" y="{cy}" font-family="{FONT}" font-size="11" font-weight="700" fill="#fff" text-anchor="middle" dominant-baseline="middle" letter-spacing="1.5" transform="rotate(-90 {bx+11} {cy})">{lab}</text>']
    # boundary line between L5 and L4
    yb = top + 3*rh - 6
    o += [f'<line x1="{ox}" y1="{yb}" x2="{bx-6}" y2="{yb}" stroke="{C["adeep"]}" stroke-width="1.6" stroke-dasharray="8 6"/>',
          f'<rect x="{lx+lw/2-96}" y="{yb-10}" width="192" height="20" rx="10" fill="{C["asoft"]}" stroke="#f6c9a8"/>',
          text(lx+lw/2, yb+4, 'syscall: sendmsg / recvmsg', 11, C['adeep'], 700, family=MONO, anchor='middle')]

    # moving marker on the rail between OSI and lane
    railx = (ox+ow+lx)/2
    ys = [yc(L)+6 for L in range(7, 0, -1)]
    seq = ys + ys[::-1] + [ys[0], ys[0]]
    kts = ';'.join(f'{i/(len(seq)-1):.4f}' for i in range(len(seq)))
    o += [f'<line x1="{railx}" y1="{ys[0]}" x2="{railx}" y2="{ys[-1]}" stroke="{C["line"]}" stroke-width="3"/>',
          f'<circle cx="{railx}" r="12" fill="{C["accent"]}" opacity=".25"><animate attributeName="cy" dur="{dur}s" repeatCount="indefinite" values="{";".join(f"{v:.1f}" for v in seq)}" keyTimes="{kts}"/></circle>',
          f'<circle cx="{railx}" r="7" fill="{C["accent"]}" stroke="#fff" stroke-width="2"><animate attributeName="cy" dur="{dur}s" repeatCount="indefinite" values="{";".join(f"{v:.1f}" for v in seq)}" keyTimes="{kts}"/></circle>']
    # direction captions
    def cap(s, a, b, col):
        return (f'<g opacity="0"><animate attributeName="opacity" dur="{dur}s" repeatCount="indefinite" calcMode="discrete" keyTimes="0;{a/N:.4f};{b/N:.4f};1" values="0;1;0;0"/>'
                + rect(lx+lw/2-120, top+7*rh+2, 240, 30, col, rx=15) + text(lx+lw/2, top+7*rh+22, s, 13, '#fff', 700, anchor='middle') + '</g>')
    o += [cap('TX ↓  Host A encapsulates', 0, 7, C['accent']), cap('RX ↑  Host B decapsulates', 7, 14, C['green']), cap('callback() runs on Host B', 14, 16, C['navy'])]
    o += [text(40, H-34, 'Notes: DDS-RTPS spans OSI 5–7 in practice; RTPS reliability (HEARTBEAT/ACKNACK) runs in user space over UDP.', 11, C['ink'], family=MONO),
          text(40, H-18, 'SHM / loaned messages and rosidl::Buffer backends skip layers 1–4 between processes on the same host.', 11, C['ink'], family=MONO)]
    o.append('</svg>')
    return '\n'.join(o)

open(f'{OUT}/anim-lyrical-stack-layers.svg', 'w').write(stack_svg())
open(f'{OUT}/anim-osi-vs-ros2-lyrical.svg', 'w').write(osi_svg())
print('ok')
