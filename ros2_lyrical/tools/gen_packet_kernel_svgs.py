#!/usr/bin/env python3
"""Read a real captured frame (example_interfaces/msg/String over Fast DDS / RTPS / UDP / IPv4 / Ethernet,
frame 95 of captures/exp1_fastdds_default.pcap) and render two animated SVGs:
packet anatomy + Linux kernel TX/RX call path."""
import struct, sys
from xml.sax.saxutils import escape as esc

OUT = sys.argv[1]
FONT = "'Segoe UI','Helvetica Neue',Arial,sans-serif"
MONO = "'JetBrains Mono',Consolas,Menlo,monospace"

def csum(b):
    if len(b) % 2: b += b'\0'
    s = sum(struct.unpack('!%dH' % (len(b)//2), b))
    while s >> 16: s = (s & 0xffff) + (s >> 16)
    return (~s) & 0xffff

# ---------------- load the real frame ----------------
# Frame 95 of captures/exp1_fastdds_default.pcap (Part 3, experiment 1): demo_nodes_cpp talker,
# example_interfaces/msg/String "Hello World: 1", rmw_fastrtps_cpp (Fast DDS 3.6.2 .deb), UDPv4 unicast.
import os
PCAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'captures', 'exp1_fastdds_default.pcap')
FRAME_NO = 95
def read_frame(path, want):
    data = open(path, 'rb').read()
    assert data[:4] == b'\xd4\xc3\xb2\xa1' and struct.unpack('<I', data[20:24])[0] == 1, 'expect LE pcap, Ethernet'
    off, n = 24, 0
    while off + 16 <= len(data):
        incl = struct.unpack('<I', data[off+8:off+12])[0]; n += 1
        if n == want: return data[off+16:off+16+incl]
        off += 16 + incl
    raise SystemExit(f'frame {want} not found')
frame = read_frame(PCAP, FRAME_NO)
assert len(frame) == 198, len(frame)
assert frame[42:46] == b'RTPS' and frame[62] == 0x0e and frame[78] == 0x09 and frame[90] == 0x15 and frame[138] == 0x80
u16 = lambda o: struct.unpack('!H', frame[o:o+2])[0]
le16 = lambda o: struct.unpack('<H', frame[o:o+2])[0]
ip4 = lambda o: '.'.join(str(x) for x in frame[o:o+4])
mac = lambda o: ':'.join(f'{x:02x}' for x in frame[o:o+6])
eid = lambda o: '.'.join(f'{x:02x}' for x in frame[o:o+4])
gp = lambda o: '.'.join(f'{x:02x}' for x in frame[o:o+6]) + '…'
tot, ipck, sport, dport, ulen, uck = u16(16), u16(24), u16(34), u16(36), u16(38), u16(40)
src_ip, dst_ip = ip4(26), ip4(30)
slen = struct.unpack('<I', frame[118:122])[0]
text_s = frame[122:122+slen]
pad = 4 - (4 + slen) % 4 if (4 + slen) % 4 else 0
assert text_s == b'Hello World: 1\0' and 122 + slen + pad == 138
stat_len = le16(140)

hx = lambda b: ' '.join(f'{x:02x}' for x in b)
# field table: (layer, offset, size, name, value)
F = []
def f(layer, off, size, name, val): F.append((layer, off, size, name, val))
f('eth', 0, 6, 'dst MAC', mac(0)); f('eth', 6, 6, 'src MAC', mac(6)); f('eth', 12, 2, 'EtherType', '0x0800 IPv4')
o = 14
f('ip', o, 1, 'version · IHL', '4 · 5 (20 B)'); f('ip', o+1, 1, 'DSCP · ECN', f'0x{frame[15]:02x}'); f('ip', o+2, 2, 'total length', f'{tot}')
f('ip', o+4, 2, 'identification', f'0x{u16(18):04x}'); f('ip', o+6, 2, 'flags · frag offset', 'DF · 0')
f('ip', o+8, 1, 'TTL', f'{frame[22]}'); f('ip', o+9, 1, 'protocol', '17 UDP'); f('ip', o+10, 2, 'header checksum', f'0x{ipck:04x}')
f('ip', o+12, 4, 'src IP', f'{src_ip} (talker)'); f('ip', o+16, 4, 'dst IP', f'{dst_ip} (listener)')
o = 34
f('udp', o, 2, 'src port', f'{sport} (ephemeral)'); f('udp', o+2, 2, 'dst port', f'{dport} user unicast d0 p0')
f('udp', o+4, 2, 'length', f'{ulen}'); f('udp', o+6, 2, 'checksum', f'0x{uck:04x}')
o = 42
f('rtps', o, 4, 'magic', '"RTPS"'); f('rtps', o+4, 2, 'protocol version', f'{frame[46]}.{frame[47]}'); f('rtps', o+6, 2, 'vendorId', '0x010f eProsima')
f('rtps', o+8, 12, 'guidPrefix', gp(50))
o = 62
f('dst', o, 4, 'INFO_DST hdr', f'id 0x0e · flags E · len {le16(64)}'); f('dst', o+4, 12, 'guidPrefix (listener)', gp(66))
o = 78
f('ts', o, 4, 'INFO_TS hdr', f'id 0x09 · flags E · len {le16(80)}'); f('ts', o+4, 8, 'timestamp', 'sec · fraction (NTP-style)')
o = 90
f('data', o, 4, 'DATA hdr', f'id 0x15 · flags E|D · len {le16(92)}'); f('data', o+4, 4, 'extraFlags · toInlineQos', f'0 · {le16(96)}')
f('data', o+8, 4, 'readerId', f'{eid(98)} user reader'); f('data', o+12, 4, 'writerId', f'{eid(102)} user writer')
f('data', o+16, 8, 'writerSN', f'{struct.unpack("<I", frame[110:114])[0]}')
o = 114
f('cdr', o, 4, 'encapsulation', '0x0001 CDR_LE · options'); f('cdr', o+4, 4, 'string length', f'{slen} (incl. NUL)')
f('cdr', o+8, slen, 'data', '"Hello World: 1\\0"'); f('cdr', o+8+slen, pad, 'padding', f'{pad} B (4-byte align)')
o = 138
f('stat', o, 4, 'submsg hdr', f'id 0x80 · flags E · len {stat_len}'); f('stat', o+4, 24, 'destination locator', f'UDPv4 {dst_ip}:{dport}')
f('stat', o+28, 8, 'timestamp', 'sec · fraction'); f('stat', o+36, 24, 'sequence', 'statistics counters')
assert F[-1][1] + F[-1][2] == len(frame) == 198
FLEN = len(frame)

LAY = {  # key: (label, color, light)
 'eth': ('Ethernet II · 14 B', '#0f2239', '#e3e7ee'),
 'ip':  ('IPv4 · 20 B', '#3a6aa6', '#e3ecf7'),
 'udp': ('UDP · 8 B', '#2c5f9e', '#dde8f5'),
 'rtps':('RTPS header · 20 B', '#8250df', '#efe7fb'),
 'dst': ('INFO_DST submsg · 16 B', '#6e40c9', '#ebe3fa'),
 'ts':  ('INFO_TS submsg · 12 B', '#a371f7', '#f3ecfd'),
 'data':('DATA submsg header · 24 B', '#bf3989', '#fbe9f3'),
 'cdr': ('serializedPayload (CDR) · 24 B', '#e2962a', '#fdf1dc'),
 'stat':('statistics submsg 0x80 · 60 B', '#57606a', '#eef1f4'),
}
ORDER = ['eth','ip','udp','rtps','dst','ts','data','cdr','stat']

def t(x, y, s, size=12, fill='#0f2239', w=400, fam=FONT, anchor='start', extra=''):
    return f'<text x="{x}" y="{y}" font-family="{fam}" font-size="{size}" font-weight="{w}" fill="{fill}" text-anchor="{anchor}" {extra}>{esc(str(s))}</text>'
def r(x, y, w, h, fill, stroke='none', rx=6, sw=1, extra=''):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'

# ---------------- SVG 1: packet anatomy ----------------
def anatomy():
    W = 1000
    N = len(ORDER) + 1; dur = 14
    def hl(i, a, b):  # animate attr: b while step i active else a
        kt = f'0;{i/N:.4f};{(i+1)/N:.4f};1'
        return f'<animate attributeName="{{attr}}" dur="{dur}s" repeatCount="indefinite" calcMode="discrete" keyTimes="{kt}" values="{a};{b};{a};{a}"/>'
    o = []
    top = 100; rh = 17.5
    tx = 30
    rows_y = {}
    y = top
    out_rows = []
    for li, L in enumerate(ORDER):
        lab, col, light = LAY[L]
        rows = [x for x in F if x[0] == L]
        gh = 22 + len(rows)*rh + 6
        anim_fill = hl(li, '#ffffff', light).replace('{attr}', 'fill')
        anim_st = hl(li, '#d0d7de', col).replace('{attr}', 'stroke')
        out_rows.append(f'<rect x="{tx}" y="{y}" width="540" height="{gh}" rx="8" fill="#ffffff" stroke="#d0d7de" stroke-width="1.4">{anim_fill}{anim_st}</rect>')
        out_rows.append(r(tx, y, 6, gh, col, rx=3))
        out_rows.append(t(tx+16, y+16, lab, 12.5, col, 700))
        yy = y + 22
        for (_, off, size, name, val) in rows:
            out_rows += [t(tx+16, yy+12, f'{off:>3}', 11, '#8c959f', fam=MONO),
                         t(tx+50, yy+12, name, 11.5, '#0f2239', 600),
                         t(tx+230, yy+12, f'{size} B', 11, '#8c959f', fam=MONO, anchor='end'),
                         t(tx+246, yy+12, val, 11, '#57606a', fam=MONO)]
            yy += rh
        rows_y[L] = (y, gh)
        y += gh + 6
    H = max(y + 20, 760)
    o += [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img">',
          '<title>Byte-level anatomy of one ROS 2 topic sample on the wire</title>',
          r(0, 0, W, H, '#f6f8fa', rx=18),
          t(30, 44, f'One ROS 2 sample on the wire · {FLEN} bytes (+4 FCS)', 24, w=700),
          t(30, 68, "talker → /chatter · example_interfaces/msg/String \"Hello World: 1\" · rmw_fastrtps_cpp · RTPS 2.3 · real capture: exp1 frame 95", 12, '#8c959f', fam=MONO),
          t(30, 90, 'OFF  FIELD                     SIZE  VALUE', 11, '#8c959f', 700, fam=MONO)]
    o += out_rows
    # hex dump
    hx0, hy0 = 600, 100
    cw, chh = 21.5, 24
    o += [t(hx0, 90, 'HEX DUMP (offset · 16 bytes per row)', 11, '#8c959f', 700, fam=MONO),
          r(hx0-10, hy0-6, 390, (FLEN + 15)//16*chh + 14, '#ffffff', '#d0d7de', 10, 1.4)]
    owner = []
    for (L, off, size, *_ ) in F:
        owner += [L]*size
    for row in range((FLEN + 15)//16):
        yrow = hy0 + row*chh
        o.append(t(hx0, yrow+16, f'{row*16:03x}', 11, '#8c959f', fam=MONO))
        for c in range(16):
            i = row*16 + c
            if i >= len(frame): break
            L = owner[i]; lab, col, light = LAY[L]; li = ORDER.index(L)
            x = hx0 + 34 + c*cw
            fill_anim = hl(li, light, col).replace('{attr}', 'fill')
            txt_anim = hl(li, col, '#ffffff').replace('{attr}', 'fill')
            o.append(f'<rect x="{x}" y="{yrow+2}" width="{cw-2}" height="{chh-4}" rx="3" fill="{light}">{fill_anim}</rect>')
            o.append(f'<text x="{x+(cw-2)/2}" y="{yrow+16}" font-family="{MONO}" font-size="10.5" font-weight="600" fill="{col}" text-anchor="middle">{frame[i]:02x}{txt_anim}</text>')
    # size bar
    by = hy0 + (FLEN + 15)//16*chh + 34
    o.append(t(hx0-10, by-8, 'BYTES PER LAYER', 11, '#8c959f', 700, fam=MONO))
    x = hx0-10; scale = 390/FLEN
    sizes = {L: sum(s for (LL, _, s, *_ ) in F if LL == L) for L in ORDER}
    for L in ORDER:
        w = sizes[L]*scale; lab, col, light = LAY[L]
        o += [r(x, by, w-1.5, 26, col, rx=4), t(x+w/2, by+17, sizes[L], 10.5, '#fff', 700, fam=MONO, anchor='middle')]
        x += w
    # legend
    ly = by + 46
    for k, L in enumerate(ORDER):
        lab, col, light = LAY[L]
        yy = ly + k*20
        o += [r(hx0-10, yy, 12, 12, col, rx=3), t(hx0+8, yy+11, lab, 11.5, '#0f2239')]
    # efficiency note
    ey = ly + len(ORDER)*20 + 18
    o += [r(hx0-10, ey, 390, 138, '#ffffff', '#d0d7de', 10, 1.4),
          t(hx0+4, ey+22, 'Overhead', 13, '#0f2239', 700),
          t(hx0+4, ey+42, 'useful text: 14 chars · ROS payload (CDR): 24 B', 11, '#57606a', fam=MONO),
          t(hx0+4, ey+60, 'headers: 14+20+8+20+16+12+24 = 114 B', 11, '#57606a', fam=MONO),
          t(hx0+4, ey+78, 'statistics submsg: 60 B (FASTDDS_STATISTICS)', 11, '#57606a', fam=MONO),
          t(hx0+4, ey+96, f'on wire: {FLEN} + 4 FCS + 8 preamble + 12 IFG', 11, '#57606a', fam=MONO),
          t(hx0+4, ey+114, f'       = {FLEN+24} byte-times per sample', 11, '#57606a', fam=MONO)]
    o.append('</svg>')
    return '\n'.join(o)

# ---------------- SVG 2: Linux kernel call path ----------------
TX = [
 ('user', 'Fast DDS UDP transport', 'setsockopt(SO_SNDTIMEO) · send_to() → sendmsg()', ''),
 ('sys',  '__sys_sendmsg → ____sys_sendmsg', 'syscall entry, copy msghdr', 'syscalls:sys_enter_sendmsg'),
 ('sock', 'sock_sendmsg → inet_sendmsg', 'socket layer (AF_INET)', ''),
 ('udp',  'udp_sendmsg', 'route: ip_route_output_flow', ''),
 ('udp',  'ip_make_skb → __ip_append_data', 'ip_generic_getfrag: copy_from_user ②', ''),
 ('udp',  'udp_send_skb', 'UDP header + checksum / offload', ''),
 ('ip',   'ip_send_skb → ip_local_out', 'netfilter OUTPUT', ''),
 ('ip',   'ip_output → ip_finish_output', 'netfilter POSTROUTING · > MTU → ip_do_fragment', ''),
 ('ip',   'ip_finish_output2', 'neighbour/ARP: write Ethernet header', ''),
 ('dev',  '__dev_queue_xmit → __dev_xmit_skb', 'enqueue to qdisc (fq_codel …)', 'net:net_dev_queue'),
 ('dev',  'sch_direct_xmit · validate_xmit_skb', 'GSO / checksum offload', 'qdisc:qdisc_dequeue'),
 ('dev',  'dev_hard_start_xmit', 'hand skb to driver', 'net:net_dev_xmit'),
 ('drv',  'rtl8169_start_xmit (r8169)', 'DMA map → TX ring → doorbell', ''),
 ('hw',   'NIC → wire', 'FCS added · TX-done IRQ → napi_consume_skb', 'skb:consume_skb'),
]
RX = [
 ('hw',   'NIC DMA → RX ring', 'frame written to RAM', ''),
 ('drv',  'rtl8169_interrupt', 'IRQ → napi_schedule', 'irq:irq_handler_entry'),
 ('napi', 'net_rx_action → __napi_poll', 'softirq NET_RX', 'irq:softirq_entry · napi:napi_poll'),
 ('drv',  'rtl8169_poll → rtl_rx', 'copy into new skb (no page pool) · eth_type_trans', ''),
 ('napi', 'gro_receive_skb → dev_gro_receive', 'inet_gro_receive · udp4_gro_receive', 'net:napi_gro_receive_entry'),
 ('dev',  'netif_receive_skb_list_internal', '__netif_receive_skb_list_core · AF_PACKET tap (tcpdump)', 'net:netif_receive_skb'),
 ('ip',   'ip_list_rcv → ip_sublist_rcv', 'netfilter PREROUTING · ip_route_input_noref', ''),
 ('ip',   'ip_local_deliver', 'ip_defrag if fragmented · netfilter INPUT', ''),
 ('ip',   'ip_local_deliver_finish', 'ip_protocol_deliver_rcu → proto 17', ''),
 ('udp',  'udp_rcv → __udp4_lib_rcv', '__udp4_lib_lookup: port 7411 → socket', ''),
 ('udp',  'udp_unicast_rcv_skb → udp_queue_rcv_skb', 'udp_queue_rcv_one_skb', ''),
 ('udp',  '__udp_enqueue_schedule_skb', 'rcvbuf full → sk_skb_reason_drop', 'skb:kfree_skb (SOCKET_RCVBUFF)'),
 ('sock', 'sock_def_readable', 'wake Fast DDS receive thread', ''),
 ('sys',  'udp_recvmsg → __skb_recv_udp', 'skb_copy_datagram_iter: copy_to_user ④', 'syscalls:sys_exit_recvmsg'),
 ('user', 'Fast DDS MessageReceiver', 'parse RTPS submessages → reader → rmw', ''),
]
SUB = {'user':('#f86b1d','#fdecdd','user space'), 'sys':('#dc5812','#fde3cd','syscall'), 'sock':('#57606a','#eef1f4','socket'),
       'udp':('#2c5f9e','#dde8f5','UDP'), 'ip':('#3a6aa6','#e3ecf7','IPv4'), 'dev':('#1f6feb','#ddebff','net core / qdisc'),
       'napi':('#8250df','#efe7fb','softirq / NAPI'), 'drv':('#0f2239','#e3e7ee','driver'), 'hw':('#24292f','#d0d7de','hardware')}

def kpath():
    W = 1000; rh = 56; top = 112
    n = max(len(TX), len(RX)); H = top + n*rh + 96
    colx = {'TX': 24, 'RX': 512}; cw = 464
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img">',
         '<title>Linux kernel path of a ROS 2 UDP datagram: TX and RX</title>',
         r(0, 0, W, H, '#f6f8fa', rx=18),
         t(24, 44, 'Linux kernel path of one RTPS/UDP datagram', 24, w=700),
         t(24, 68, 'names checked against /proc/kallsyms (Linux 7.0) · driver example: r8169 · ⌁ = tracepoint · dashed = user/kernel', 12, '#8c959f', fam=MONO),
         t(colx['TX'], 98, 'TX · Host A (sendmsg)  ↓', 13, '#dc5812', 700), t(colx['RX'], 98, 'RX · Host B (recvmsg)  ↑ read bottom-up', 13, '#27a689', 700)]
    def column(rows, side, reverse):
        x0 = colx[side]
        seq = rows if not reverse else list(reversed(rows))
        centers = []
        for i, (sub, fn, note, tp) in enumerate(seq):
            y = top + i*rh
            col, light, lab = SUB[sub]
            o.extend([r(x0, y, cw, rh-6, '#ffffff', '#d0d7de', 7, 1.2), r(x0, y, 6, rh-6, col, rx=3),
                      r(x0+14, y+(rh-6)/2-10, 92, 20, light, rx=10), t(x0+60, y+(rh-6)/2+4, lab, 10, col, 700, anchor='middle'),
                      t(x0+116, y+16, fn, 11.6, '#0f2239', 700, fam=MONO),
                      t(x0+116, y+32, note, 10.4, '#57606a', fam=MONO)])
            if tp:
                o.append(t(x0+116, y+45, '⌁ ' + tp, 10, '#8250df', 600, fam=MONO))
            centers.append(y + (rh-6)/2)
        return centers
    ctx = column(TX, 'TX', False)
    crx = column(RX, 'RX', True)   # draw RX top=user ... bottom=hw (so packet goes up)
    # boundary lines (user/kernel) per column
    o.append(f'<line x1="20" y1="{top+rh-3}" x2="980" y2="{top+rh-3}" stroke="#dc5812" stroke-width="1.5" stroke-dasharray="7 5"/>')
    # dot path: down TX rail, across bottom (wire), up RX rail
    rx_tx = colx['TX'] + 108; rx_rx = colx['RX'] + 108
    # place rail just right of the subsystem pill (x0+106..110)
    ybot_tx = ctx[-1]; ybot_rx = crx[-1]
    wire_y = top + n*rh + 18
    path = f'M{rx_tx} {ctx[0]} L{rx_tx} {ybot_tx} L{rx_tx} {wire_y} L{rx_rx} {wire_y} L{rx_rx} {ybot_rx} L{rx_rx} {crx[0]}'
    o += [f'<path d="M{rx_tx} {ybot_tx} L{rx_tx} {wire_y} L{rx_rx} {wire_y} L{rx_rx} {ybot_rx}" fill="none" stroke="#24292f" stroke-width="4" stroke-linecap="round"/>',
          t(500, wire_y+20, f'Ethernet · {FLEN} B frame', 11.5, '#24292f', 700, fam=MONO, anchor='middle'),
          f'<circle r="12" fill="#f86b1d" opacity=".25"><animateMotion dur="12s" repeatCount="indefinite" path="{path}"/></circle>',
          f'<circle r="6.5" fill="#f86b1d" stroke="#fff" stroke-width="2"><animateMotion dur="12s" repeatCount="indefinite" path="{path}"/></circle>']
    o.append(t(24, H-34, 'Notes: inlined helpers (e.g. __udp_queue_rcv_skb) are not in kallsyms; non-list RX uses', 10.5, '#57606a', fam=MONO))
    o.append(t(24, H-18, '__netif_receive_skb_one_core → ip_rcv. Function names change between kernel versions.', 10.5, '#57606a', fam=MONO))
    o.append('</svg>')
    return '\n'.join(o)

open(f'{OUT}/anim-rtps-packet-anatomy.svg', 'w').write(anatomy())
open(f'{OUT}/anim-linux-kernel-packet-path.svg', 'w').write(kpath())
# also dump hex for the doc
print('frame', FRAME_NO, len(frame), 'B', 'ipck', hex(ipck), 'udpck', hex(uck))
for i in range(0, len(frame), 16):
    print(f'{i:04x}  ' + hx(frame[i:i+16]))
