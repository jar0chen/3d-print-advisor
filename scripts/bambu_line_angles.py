"""逐層分析 Bambu G-code 的填充/表面走線角度。
用法: python3 -I bambu_line_angles.py plate_1.gcode [--tool]
輸出: 每層 x 特徵(或耗材) 的總長與前 2-3 名角度 (0-180°, 5° 一格, 只計 >3mm 的擠出線)
"""
import re,sys,math,collections
by_tool='--tool' in sys.argv
layer=0;feat='';tool='T?';x=y=None
stat=collections.defaultdict(collections.Counter)
for line in open(sys.argv[1]):
    if line.startswith('; CHANGE_LAYER'): layer+=1
    elif line.startswith('; FEATURE:'): feat=line.split(':',1)[1].strip()
    elif re.match(r'^T\d+\s',line): tool=line.split()[0]
    elif line.startswith(('G1','G0')):
        m=dict((k,float(v)) for k,v in re.findall(r'([XYE])([-\d.]+)',line.split(';')[0]))
        nx,ny=m.get('X',x),m.get('Y',y)
        if 'E' in m and m['E']>0 and x is not None and any(w in feat.lower() for w in ('infill','surface','bridge')) and 'gap' not in feat.lower():
            L=math.hypot(nx-x,ny-y)
            if L>3: stat[(layer,tool if by_tool else feat)][round(math.degrees(math.atan2(ny-y,nx-x))%180/5)*5%180]+=L
        x,y=nx,ny
for (l,f),c in sorted(stat.items()):
    tot=sum(c.values())
    print(f'L{l:2d} {f:22s} {tot:7.0f}mm  '+'  '.join(f'{a}°:{v/tot:.0%}' for a,v in c.most_common(3)))
