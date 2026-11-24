#!/usr/bin/env python3
"""Animated SVGs built from REAL captured frames (ros2_lyrical/captures/*.pcap) + the rcvbuf experiment."""
import sys
from xml.sax.saxutils import escape as esc
OUT = sys.argv[1]
FONT = "'Segoe UI','Helvetica Neue',Arial,sans-serif"
MONO = "'JetBrains Mono',Consolas,Menlo,monospace"
def t(x, y, s, size=12, fill='#0f2239', w=400, fam=FONT, anchor='start', extra=''):
    return f'<text x="{x}" y="{y}" font-family="{fam}" font-size="{size}" font-weight="{w}" fill="{fill}" text-anchor="{anchor}" {extra}>{esc(str(s))}</text>'
def r(x, y, w, h, fill, stroke='none', rx=6, sw=1, extra=''):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'
H = lambda s: bytes.fromhex(s.replace(' ', '').replace('\n', ''))

# ---- exp1 frame 136: Fast DDS (Lyrical .deb) demo talker -> listener, 198 B
RTPS = H('''
62 1b 4b 57 a2 ac 42 8d e7 ce ea 36 08 00 45 00 00 b8 10 29 40 00 40 11 d1 de ac 14 00 03 ac 14
00 02 b0 4f 1c f3 00 a4 58 e3 52 54 50 53 02 03 01 0f 01 0f 11 31 1a 00 bc 0d 00 00 00 00 0e 01
0c 00 01 0f 2c 17 1d 00 1c 48 00 00 00 00 09 01 08 00 b1 58 05 6b 63 88 85 8b 15 05 2c 00 00 00
10 00 00 00 13 04 00 00 13 03 00 00 00 00 01 00 00 00 00 01 00 00 0f 00 00 00 48 65 6c 6c 6f 20
57 6f 72 6c 64 3a 20 31 00 00 80 01 38 00 01 00 00 00 f3 1c 00 00 00 00 00 00 00 00 00 00 00 00
00 00 ac 14 00 02 b1 58 05 6b 07 49 88 8b 05 00 00 00 00 00 00 00 94 02 00 00 00 00 00 00 00 00
00 00 00 00 00 00''')
RTPS_F = [
 ('eth',0,6,'dst MAC','62:1b:4b:57:a2:ac'),('eth',6,6,'src MAC','42:8d:e7:ce:ea:36'),('eth',12,2,'EtherType','0x0800'),
 ('ip',14,2,'ver/IHL · DSCP','45 00'),('ip',16,2,'total length','184'),('ip',18,4,'id · flags','0x1029 · DF'),
 ('ip',22,2,'TTL · proto','64 · 17 UDP'),('ip',24,2,'checksum','0xd1de'),('ip',26,4,'src IP','172.20.0.3 (talker)'),('ip',30,4,'dst IP','172.20.0.2 (listener)'),
 ('udp',34,2,'src port','45135'),('udp',36,2,'dst port','7411'),('udp',38,2,'length','164'),('udp',40,2,'checksum','0x58e3'),
 ('rtps',42,4,'magic','"RTPS"'),('rtps',46,2,'version','2.3 (SECURITY=ON)'),('rtps',48,2,'vendorId','01.0f eProsima'),('rtps',50,12,'guidPrefix','01.0f.11.31.1a.00.bc.0d…'),
 ('dst',62,4,'INFO_DST hdr','0x0e · E · len 12'),('dst',66,12,'dst guidPrefix','01.0f.2c.17.1d.00.1c.48…'),
 ('ts',78,4,'INFO_TS hdr','0x09 · E · len 8'),('ts',82,8,'timestamp','2026-11-24 09:28:17.545'),
 ('data',90,4,'DATA hdr','0x15 · E|D · len 44'),('data',94,4,'extraFlags · toQos','0 · 16'),('data',98,4,'readerId','00.00.13.04'),
 ('data',102,4,'writerId','00.00.13.03'),('data',106,8,'writerSN','1'),
 ('cdr',114,4,'encapsulation','CDR_LE · options 0'),('cdr',118,4,'length','15'),('cdr',122,16,'data + pad','"Hello World: 1\\0" 00'),
 ('stat',138,4,'submsg hdr','0x80 vendor · len 56'),('stat',142,24,'dst locator','UDPv4 172.20.0.2:7411'),
 ('stat',166,8,'timestamp',''),('stat',174,24,'sequence data','statistics counters'),
]
RTPS_L = {'eth':('Ethernet II · 14 B','#0f2239','#e3e7ee'),'ip':('IPv4 · 20 B','#3a6aa6','#e3ecf7'),'udp':('UDP · 8 B','#2c5f9e','#dde8f5'),
 'rtps':('RTPS header · 20 B','#8250df','#efe7fb'),'dst':('INFO_DST · 16 B','#6639ba','#ece4fb'),'ts':('INFO_TS · 12 B','#a371f7','#f3ecfd'),
 'data':('DATA header · 24 B','#bf3989','#fbe9f3'),'cdr':('CDR payload · 24 B','#e2962a','#fdf1dc'),'stat':('Statistics 0x80 · 60 B','#57606a','#eaeef2')}
RTPS_O = ['eth','ip','udp','rtps','dst','ts','data','cdr','stat']

# ---- exp3 frame 158: rmw_zenoh_cpp peer-to-peer TCP, 161 B
ZEN = H('''
8a 93 a7 c1 eb d7 8e 97 af 36 6e eb 08 00 45 00 00 93 1b e9 40 00 40 06 c6 4c ac 14 00 04 ac 14
00 03 8a d9 df b4 af 36 53 f1 7e bb cc 0a 80 18 00 3f 58 b5 00 00 01 01 08 0a 9a 1b e1 6e 91 8a
72 d6 5d 00 25 e8 91 b6 08 1d 02 a1 a0 97 d2 e8 ba ae d6 82 6b 10 24 7c cf 5d f0 b0 51 a8 4e a7
82 d1 9c f6 f2 f9 43 21 02 00 00 00 00 00 00 00 3a 1d 0f b1 47 f1 ea 18 10 c5 89 fb 05 d4 36 e0
a1 d6 3d 56 87 be 42 25 fe 17 00 01 00 00 0f 00 00 00 48 65 6c 6c 6f 20 57 6f 72 6c 64 3a 20 32
00''')
ZEN_F = [
 ('eth',0,14,'Ethernet II','dst · src · 0x0800'),
 ('ip',14,20,'IPv4','172.20.0.4 → 172.20.0.3 · proto 6'),
 ('tcp',34,4,'ports','35545 → 57268'),('tcp',38,8,'seq · ack',''),('tcp',46,4,'offset · flags · win','32 B hdr · PSH|ACK'),('tcp',50,4,'checksum · urg',''),('tcp',54,12,'options','NOP NOP timestamps'),
 ('len',66,2,'batch length (u16 LE)','0x005d = 93'),
 ('frame',68,1,'FRAME header','0x25 = id 0x05 + R (reliable)'),('frame',69,4,'sequence number','zint e8 91 b6 08'),
 ('push',73,1,'PUSH header','0x1d'),('push',74,1,'wire expr id','2 (declared earlier)'),
 ('put',75,1,'PUT header','0xa1 = id 0x01 + T + Z'),('put',76,9,'timestamp NTP64','zint'),('put',85,17,'ZenohId','len 16 + id'),
 ('att',102,2,'ext attachment','0x43 · len 33'),('att',104,8,'sequence number','2'),('att',112,8,'source timestamp','ns since epoch'),('att',120,17,'publisher GID','len 16 + gid'),
 ('cdr',137,1,'payload length','23'),('cdr',138,23,'CDR payload','00 01 00 00 · 15 · "Hello World: 2\\0"'),
]
ZEN_L = {'eth':('Ethernet II · 14 B','#0f2239','#e3e7ee'),'ip':('IPv4 · 20 B','#3a6aa6','#e3ecf7'),'tcp':('TCP · 32 B (with timestamps)','#2c5f9e','#dde8f5'),
 'len':('Zenoh batch length · 2 B','#9a5b00','#fdf1dc'),'frame':('Zenoh FRAME · 5 B','#c77d10','#fdf1dc'),'push':('Zenoh PUSH · 2 B','#d4900f','#fdf4e3'),
 'put':('Zenoh PUT + timestamp · 27 B','#e2962a','#fdf1dc'),'att':('rmw_zenoh attachment · 35 B','#8250df','#efe7fb'),'cdr':('CDR payload · 24 B','#bf3989','#fbe9f3')}
ZEN_O = ['eth','ip','tcp','len','frame','push','put','att','cdr']

def anatomy(frame, F, LAY, ORDER, title, sub, notes):
    W = 1000; N = len(ORDER) + 1; dur = 2*N
    for (_, o, s, *_ ) in F: pass
    assert F[-1][1] + F[-1][2] == len(frame), (F[-1], len(frame))
    def hl(i, a, b, attr):
        kt = f'0;{i/N:.4f};{(i+1)/N:.4f};1'
        return f'<animate attributeName="{attr}" dur="{dur}s" repeatCount="indefinite" calcMode="discrete" keyTimes="{kt}" values="{a};{b};{a};{a}"/>'
    rh = 16.5; top = 100; tx = 30; y = top; body = []
    for li, L in enumerate(ORDER):
        lab, col, light = LAY[L]; rows = [x for x in F if x[0] == L]
        gh = 21 + len(rows)*rh + 5
        body.append(f'<rect x="{tx}" y="{y}" width="540" height="{gh}" rx="8" fill="#ffffff" stroke="#d0d7de" stroke-width="1.4">{hl(li,"#ffffff",light,"fill")}{hl(li,"#d0d7de",col,"stroke")}</rect>')
        body += [r(tx, y, 6, gh, col, rx=3), t(tx+16, y+15, lab, 12, col, 700)]
        yy = y + 21
        for (_, off, size, name, val) in rows:
            body += [t(tx+16, yy+12, f'{off:>3}', 10.5, '#8c959f', fam=MONO), t(tx+50, yy+12, name, 11, '#0f2239', 600),
                     t(tx+238, yy+12, f'{size} B', 10.5, '#8c959f', fam=MONO, anchor='end'), t(tx+252, yy+12, val, 10.5, '#57606a', fam=MONO)]
            yy += rh
        y += gh + 5
    owner = []
    for (L, off, size, *_ ) in F: owner += [L]*size
    rows_hex = (len(frame)+15)//16
    hx0, hy0, cw, chh = 600, 100, 21.5, 22
    hexh = rows_hex*chh + 14
    by = hy0 + hexh + 26
    ly = by + 44
    ey = ly + len(ORDER)*19 + 12
    Hh = max(y + 16, ey + 24 + len(notes)*16 + 20)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {Hh}" width="{W}" height="{Hh}" role="img">', f'<title>{esc(title)}</title>',
         r(0, 0, W, Hh, '#f6f8fa', rx=18), t(30, 44, title, 23, w=700), t(30, 68, sub, 11.5, '#8c959f', fam=MONO),
         r(W-178, 24, 148, 24, '#d9f0e8', '#27a689', 12), t(W-104, 40, 'REAL CAPTURE', 11, '#17765f', 700, anchor='middle', extra='letter-spacing="1.5"'),
         t(30, 90, 'OFF  FIELD                       SIZE  VALUE', 10.5, '#8c959f', 700, fam=MONO)] + body
    o += [t(hx0, 90, 'HEX DUMP (from pcap)', 10.5, '#8c959f', 700, fam=MONO), r(hx0-10, hy0-6, 390, hexh, '#ffffff', '#d0d7de', 10, 1.4)]
    for row in range(rows_hex):
        yr = hy0 + row*chh
        o.append(t(hx0, yr+15, f'{row*16:03x}', 10.5, '#8c959f', fam=MONO))
        for c in range(16):
            i = row*16 + c
            if i >= len(frame): break
            L = owner[i]; lab, col, light = LAY[L]; li = ORDER.index(L); x = hx0 + 34 + c*cw
            o.append(f'<rect x="{x}" y="{yr+2}" width="{cw-2}" height="{chh-4}" rx="3" fill="{light}">{hl(li,light,col,"fill")}</rect>')
            o.append(f'<text x="{x+(cw-2)/2}" y="{yr+15}" font-family="{MONO}" font-size="10" font-weight="600" fill="{col}" text-anchor="middle">{frame[i]:02x}{hl(li,col,"#ffffff","fill")}</text>')
    o.append(t(hx0-10, by-8, 'BYTES PER LAYER', 10.5, '#8c959f', 700, fam=MONO))
    x = hx0-10; sc = 390/len(frame)
    for L in ORDER:
        n = sum(s for (LL, _, s, *_ ) in F if LL == L); w = n*sc; lab, col, light = LAY[L]
        o += [r(x, by, max(w-1.5, 1), 24, col, rx=3)]
        if w > 16: o.append(t(x+w/2, by+16, n, 10, '#fff', 700, fam=MONO, anchor='middle'))
        x += w
    for k, L in enumerate(ORDER):
        lab, col, light = LAY[L]
        o += [r(hx0-10, ly+k*19, 11, 11, col, rx=3), t(hx0+8, ly+k*19+10, lab, 11, '#0f2239')]
    o.append(r(hx0-10, ey, 390, 24 + len(notes)*16, '#ffffff', '#d0d7de', 10, 1.4))
    for k, (s, c) in enumerate(notes):
        o.append(t(hx0+4, ey+20+k*16, s, 10.5, c, 600 if c != '#57606a' else 400, fam=MONO))
    o.append('</svg>')
    return '\n'.join(o)

open(f'{OUT}/anim-capture-rtps-198b.svg','w').write(anatomy(RTPS, RTPS_F, RTPS_L, RTPS_O,
  'Real capture: one ROS 2 sample over Fast DDS · 198 B',
  'ros2_lyrical/captures/exp1_fastdds_default.pcap · frame 95 · demo talker → listener · example_interfaces/String · Lyrical .deb',
  [('UDP payload 156 B = RTPS 20 + INFO_DST 16 + INFO_TS 12', '#57606a'), ('  + DATA 24 + CDR 24 + statistics 0x80 60', '#57606a'),
   ('useful text 14 chars · CDR 24 B · headers 174 B', '#57606a'), ('on wire 198 + FCS 4 + preamble 8 + IFG 12 = 222', '#57606a'),
   ('confirms: RTPS 2.3, INFO_DST 16 B, stats 60 B', '#17765f')]))
open(f'{OUT}/anim-capture-zenoh-161b.svg','w').write(anatomy(ZEN, ZEN_F, ZEN_L, ZEN_O,
  'Real capture: the same sample over rmw_zenoh · 161 B',
  'ros2_lyrical/captures/exp3_zenoh.pcap · frame 145 · peer-to-peer TCP (not via router) · zenoh-c 1.10.x',
  [('TCP payload 95 B = length 2 + FRAME 5 + PUSH 2 + PUT 27', '#57606a'), ('  + attachment 35 + payload length 1 + CDR 23', '#57606a'),
   ('CDR has no trailing pad here (23 B vs 24 B in RTPS)', '#57606a'), ('vs RTPS 198 B: −37 B per small sample', '#17765f'),
   ('field split decoded by hand; verify with zenoh plugin', '#dc5812')]))

# ---- rcvbuf experiment animation
def rcvbuf():
    W, Hh = 1000, 560; dur = 6
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {Hh}" width="{W}" height="{Hh}" role="img">',
         '<title>Experiment: SO_RCVBUF decides whether a best-effort image survives</title>', r(0, 0, W, Hh, '#f6f8fa', rx=18),
         t(30, 44, 'Experiment: socket receive buffer vs. 640×480 images (BEST_EFFORT)', 22, w=700),
         t(30, 68, '20 images × 15 DATA_FRAG × 45 IP fragments · capture saw all 15/15 fragments of every image · drops happen after the AF_PACKET tap', 11.5, '#8c959f', fam=MONO),
         r(W-178, 24, 148, 24, '#d9f0e8', '#27a689', 12), t(W-104, 40, 'REAL RESULT', 11, '#17765f', 700, anchor='middle', extra='letter-spacing="1.5"')]
    panels = [(30, 'default · rmem_default → rb 212 992 B (ss -uam)', 0.62, 13, 45, '#d64545', 'exp5_image_besteffort.pcap'),
              (515, 'XML receiveBufferSize 4 MiB → rb 8 388 608 (doubled)', 0.06, 20, 0, '#27a689', 'exp6 (FASTDDS_DEFAULT_PROFILES_FILE)')]
    for (x0, lab, fill_ratio_overflow, got, drops, col, src) in panels:
        o += [r(x0, 90, 455, 440, '#ffffff', '#d0d7de', 14, 1.5), t(x0+20, 118, lab, 13, '#0f2239', 700), t(x0+20, 138, src, 10.5, '#8c959f', fam=MONO)]
        # bucket
        bx, byy, bw, bh = x0+150, 190, 150, 210
        cap_h = bh if drops else bh*0.55
        o += [f'<path d="M{bx} {byy} L{bx} {byy+bh} L{bx+bw} {byy+bh} L{bx+bw} {byy}" fill="none" stroke="#0f2239" stroke-width="3"/>',
              t(bx+bw/2, byy+bh+22, 'socket receive queue', 11, '#57606a', anchor='middle', fam=MONO)]
        # filling level animation
        level_to = bh if drops else bh*0.45
        o.append(f'<rect x="{bx+3}" width="{bw-6}" fill="{col}" opacity=".35"><animate attributeName="height" dur="{dur}s" repeatCount="indefinite" values="0;{level_to};{level_to};0" keyTimes="0;0.5;0.85;1"/><animate attributeName="y" dur="{dur}s" repeatCount="indefinite" values="{byy+bh};{byy+bh-level_to};{byy+bh-level_to};{byy+bh}" keyTimes="0;0.5;0.85;1"/></rect>')
        # incoming datagrams
        for k in range(15):
            begin = k*0.22
            dx = bx + 20 + (k % 5)*26
            o.append(f'<rect x="{dx}" y="150" width="20" height="12" rx="3" fill="#e2962a"><animate attributeName="y" dur="{dur}s" begin="{begin}s" repeatCount="indefinite" values="150;{byy+bh-20};{byy+bh-20}" keyTimes="0;0.25;1"/><animate attributeName="opacity" dur="{dur}s" begin="{begin}s" repeatCount="indefinite" values="1;1;0;0" keyTimes="0;0.25;0.3;1"/></rect>')
        if drops:
            for k in range(6):
                begin = 1.6 + k*0.3
                o.append(f'<g opacity="0"><animate attributeName="opacity" dur="{dur}s" begin="{begin}s" repeatCount="indefinite" values="0;1;0;0" keyTimes="0;0.06;0.2;1"/>'
                         f'<rect x="{bx+bw+16}" y="{byy+20+k*26}" width="20" height="12" rx="3" fill="#d64545"/>'
                         + t(bx+bw+44, byy+31+k*26, 'drop: SOCKET_RCVBUFF', 10, '#d64545', 600, fam=MONO) + '</g>')
        # results
        o += [r(x0+20, 440, 415, 74, '#f6f8fa', '#d0d7de', 10),
              t(x0+36, 468, f'received {got}/20 images', 17, col, 700),
              t(x0+36, 492, f'UDP RcvbufErrors = {drops}', 12.5, '#0f2239', 600, fam=MONO),
              t(x0+300, 492, f'loss {round((20-got)/20*100)}%', 12.5, col, 700, fam=MONO), t(x0+300, 468, 'same in 2/2 runs', 11, '#8c959f', fam=MONO)]
    o.append('</svg>')
    return '\n'.join(o)
open(f'{OUT}/anim-experiment-rcvbuf.svg','w').write(rcvbuf())
print('ok')
