"""把 G-code 最上層（或指定高度以上）的走線畫成「實心足跡」，模擬凸字／印章面印出來的樣子。
用法: python3 bambu_footprint_plot.py out.png --box x0,x1,y0,y1 [--zmin 10.0] [--mirror] a/plate_1.gcode:標籤 b/plate_1.gcode:標籤 ...
- 線寬用 E 值換算：w = E·2.4053/(L·h) + h(1−π/4)（1.75mm 線材、圓角端）；G1、G2/G3 弧線都算
- 只取 z ≥ zmin 的最高一層；不畫熨燙
- --mirror：左右翻轉（印章面是反字時，翻回來比較好讀）
- 足跡斷開的地方 = 印出來會斷；比只畫中心線準確（線看起來連著，實心足跡可能斷）
需要 matplotlib、shapely（用 scratchpad venv）。
"""
import re, math, sys
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from shapely.geometry import LineString
from shapely.ops import unary_union
A = sys.argv[1:]
def opt(name, default=None, flag=False):
    if name in A:
        i = A.index(name)
        if flag: del A[i]; return True
        v = A[i + 1]; del A[i:i + 2]; return v
    return default
box = [float(v) for v in opt('--box').split(',')]; zmin = float(opt('--zmin', '0')); mirror = opt('--mirror', flag=True)
h = float(opt('--h', '0.2')); out, items = A[0], A[1:]
def num(l, c):
    m = re.search(rf'{c}(-?[\d.]+)', l); return float(m.group(1)) if m else None
def foot(g):
    x0, x1, y0, y1 = box; z = 0; x = y = None; typ = ''; shapes = {}
    for l in open(g, errors='ignore'):
        if l.startswith('; Z_HEIGHT:'): z = float(l.split(':')[1])
        elif l.startswith('; FEATURE:'): typ = l.split(':', 1)[1].strip()
        s = l.split(';')[0].strip()
        if not re.match(r'G[123]\b', s): continue
        nx, ny, e = num(s, 'X'), num(s, 'Y'), num(s, 'E')
        nx = x if nx is None else nx; ny = y if ny is None else ny
        if e and e > 0 and x is not None and z >= zmin and typ != 'Ironing' and x0 <= x <= x1 and y0 <= y <= y1:
            if s.startswith('G1'): pts = [(x, y), (nx, ny)]
            else:
                i, j = num(s, 'I'), num(s, 'J'); cx, cy = x + i, y + j; r = math.hypot(i, j)
                a0 = math.atan2(y - cy, x - cx); a1 = math.atan2(ny - cy, nx - cx); cw = s.startswith('G2')
                if cw and a1 >= a0: a1 -= 2 * math.pi
                if not cw and a1 <= a0: a1 += 2 * math.pi
                pts = [(cx + r * math.cos(a0 + (a1 - a0) * k / 12), cy + r * math.sin(a0 + (a1 - a0) * k / 12)) for k in range(13)]
            ls = LineString(pts); L = ls.length
            if L > 0.01:
                w = min(e * 2.4053 / (L * h) + h * (1 - math.pi / 4), 1.0)
                shapes.setdefault(z, []).append(ls.buffer(w / 2, cap_style=1))
        x, y = nx, ny
    return unary_union(shapes[max(shapes)])
sx = -1 if mirror else 1
fig, axs = plt.subplots(len(items), 1, figsize=(14, 1.9 * len(items)), squeeze=False)
for ax, it in zip(axs[:, 0], items):
    g, _, lab = it.partition(':'); U = foot(g)
    for gg in (U.geoms if hasattr(U, 'geoms') else [U]):
        xs, ys = gg.exterior.xy; ax.fill([sx * q for q in xs], ys, color='k')
        for hh in gg.interiors: xs, ys = hh.xy; ax.fill([sx * q for q in xs], ys, color='w')
    xa, xb = sorted([sx * box[0], sx * box[1]])
    ax.set_xlim(xa, xb); ax.set_ylim(box[2], box[3]); ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([]); ax.set_title(lab or g, fontsize=9)
plt.tight_layout(); plt.savefig(out, dpi=100); print('ok', out)
