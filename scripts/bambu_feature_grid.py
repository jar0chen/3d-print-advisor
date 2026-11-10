"""測試片逐格驗證：每一格某個特徵（熨燙、頂面…）的實際出料 E/mm 與速度。
用法: python3 -I bambu_feature_grid.py plate_1.gcode "Ironing" "77:20,99:15,121:10" "119:20,97:30,75:40" [--ref 0.00178:15]
- 第 3 個參數：X 中心:欄標籤（熱床座標），第 4 個：Y 中心:列標籤。每段線依中點歸到最近的格子。
- --ref E/mm:數值  用已知的一格換算成百分比（例：熨燙 15% 時 E/mm 0.00178 → 其他格直接印出 ≈x%）。
- 只算 G1 直線且長度 > 2mm 的段，避開回抽、短段；結果 ±1% 屬正常誤差。
- 欄列標籤要跟模型上刻的數字對照，對不上就是設定錯位（例如 part id 被重新編號）。
"""
import re, math, sys, collections
g, feat_want, xs, ys = sys.argv[1:5]
cx = {float(k): v for k, v in (p.split(':') for p in xs.split(','))}
cy = {float(k): v for k, v in (p.split(':') for p in ys.split(','))}
ref = None
if '--ref' in sys.argv:
    a, b = sys.argv[sys.argv.index('--ref') + 1].split(':'); ref = (float(a), float(b))
x = y = 0.0; feat = ''; F = 0.0
st = collections.defaultdict(lambda: [0.0, 0.0, collections.Counter()])
for l in open(g):
    if l.startswith('; FEATURE:'): feat = l[10:].strip()
    elif l.startswith('G1 '):
        f = re.search(r'F([\d.]+)', l); F = float(f.group(1)) if f else F
        X = re.search(r'X([-\d.]+)', l); Y = re.search(r'Y([-\d.]+)', l); E = re.search(r'E([\d.]+)', l)
        nx = float(X.group(1)) if X else x; ny = float(Y.group(1)) if Y else y
        L = math.hypot(nx - x, ny - y)
        if feat == feat_want and E and L > 2:
            mx, my = (x + nx) / 2, (y + ny) / 2
            k = (cy[min(cy, key=lambda c: abs(c - my))], cx[min(cx, key=lambda c: abs(c - mx))])
            s = st[k]; s[0] += float(E.group(1)); s[1] += L; s[2][F / 60] += L
        x, y = nx, ny
for k in sorted(st):
    e, L, fs = st[k]; epm = e / L
    extra = f'  ≈{epm / ref[0] * ref[1]:.0f}' if ref else ''
    print(f'列 {k[0]:>6}  欄 {k[1]:>6}  E/mm {epm:.5f}{extra}  速度 {fs.most_common(1)[0][0]:g}')
