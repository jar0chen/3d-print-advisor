"""從 Bambu G-code 量每個物件的實際走線。
用法:
  python3 -I bambu_gcode_objects.py plate_1.gcode
      每個物件（label id）的 XY 範圍和最高 Z。用來確認物件真的在預期位置、高度對（例：圓蓋應該只有 1mm 高）。
  python3 -I bambu_gcode_objects.py plate_1.gcode --circle X,Y [--z 2.28] [--min|--max] [--width 0.42] [--within 20]
      以 (X,Y) 為圓心，逐層列出外牆走線到圓心的最小或最大距離，再加減半個線寬，推算孔或圓柱的實際半徑
      （已包含圓孔校正、象腳補償等切片器的調整，不含實際列印的收縮）。
      --min：孔（量內側邊緣）；--max：圓柱、圓蓋（量外側邊緣）。
      --within：只看離圓心這個距離內的走線（預設 20mm），避免量到旁邊的物件。
注意:
- 開了圓弧擬合時，圓是用 G2/G3 印的，這支程式有一起算進來。
- 只量線段端點：長直線（內部填充）中間經過的位置不會出現，所以只拿「外牆」來量。
"""
import sys, re, math, collections


def parse(path):
    z = 0; x = y = None; feat = ''; lab = None
    pts = collections.defaultdict(list)
    for L in open(path):
        if L.startswith('; Z_HEIGHT:'):
            z = float(L.split(':')[1])
        elif L.startswith('; FEATURE:'):
            feat = L[10:].strip()
        elif L.startswith('; start printing object, unique label id:'):
            lab = L.split()[-1]
        elif L.startswith('; stop printing object'):
            lab = None
        elif L[:2] in ('G1', 'G2', 'G3'):
            mx = re.search(r'X([-\d.]+)', L); my = re.search(r'Y([-\d.]+)', L)
            nx = float(mx.group(1)) if mx else x; ny = float(my.group(1)) if my else y
            if re.search(r'E[\d.]+', L) and x is not None and lab:
                pts[lab].append((nx, ny, z, feat))
            x, y = nx, ny
    return pts


if __name__ == '__main__':
    a = sys.argv[1:]
    P = parse(a[0])
    if '--circle' not in a:
        for lab, ps in sorted(P.items()):
            xs = [p[0] for p in ps]; ys = [p[1] for p in ps]; zs = [p[2] for p in ps]
            print(lab, f'X {min(xs):.1f}–{max(xs):.1f}  Y {min(ys):.1f}–{max(ys):.1f}  最高 Z {max(zs)}')
        sys.exit()
    cx, cy = map(float, a[a.index('--circle') + 1].split(','))
    w = float(a[a.index('--width') + 1]) if '--width' in a else 0.42
    zf = float(a[a.index('--z') + 1]) if '--z' in a else None
    use_max = '--max' in a
    within = float(a[a.index('--within') + 1]) if '--within' in a else 20
    by_z = collections.defaultdict(list)
    for ps in P.values():
        for px, py, pz, f in ps:
            if f == 'Outer wall' and (zf is None or abs(pz - zf) < 1e-3):
                r = math.hypot(px - cx, py - cy)
                if r < within:
                    by_z[pz].append(r)
    for pz in sorted(by_z):
        rs = by_z[pz]
        r = max(rs) + w / 2 if use_max else min(rs) - w / 2
        print(f'z {pz}: {"外緣" if use_max else "內緣"}半徑 約 {r:.3f}（{len(rs)} 個點）')
