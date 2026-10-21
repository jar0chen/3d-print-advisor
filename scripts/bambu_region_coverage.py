"""檢查 G-code 每一層在指定區域（例如刻字範圍）裡有沒有出料，用來確認刻字實際深度。
用法: python3 bambu_region_coverage.py plate_1.gcode region.json
region.json: {"名稱": [[x,y],[x,y],...], ...}  多邊形座標要用熱床座標（模型座標＋物件在盤上的位移，看 Metadata/plate_1.json 的 bbox）
輸出: 每個區域、每個層高的出料長度 (mm)。某層出料長度接近整層的量 → 那層是實心；只剩零星幾 mm → 是刻字的空層。
"""
import sys, re, math, json
def inside(pt, poly):
    x, y = pt; c = False; n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i+1) % n]
        if (y1 > y) != (y2 > y) and x < (x2-x1)*(y-y1)/(y2-y1)+x1: c = not c
    return c
regions = json.load(open(sys.argv[2])); z = None; x = y = None; out = {}
for line in open(sys.argv[1]):
    if line.startswith('; Z_HEIGHT:'): z = float(line.split(':')[1])
    elif line.startswith(('G1', 'G0')):
        m = dict((k, float(v)) for k, v in re.findall(r'([XYE])([-\d.]+)', line.split(';')[0])); nx, ny = m.get('X', x), m.get('Y', y)
        if m.get('E', 0) > 0 and x is not None and z is not None:
            mid = ((x+nx)/2, (y+ny)/2)
            for name, poly in regions.items():
                if inside(mid, poly): out[(name, z)] = out.get((name, z), 0)+math.hypot(nx-x, ny-y)
        x, y = nx, ny
for (name, zz), v in sorted(out.items()): print(f'{name}  z={zz:<5}  {v:8.1f} mm')
