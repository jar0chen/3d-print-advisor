"""量 G-code 裡熨燙（Ironing）走線的實際角度。用法: python3 bambu_ironing_angle.py plate_1.gcode"""
import sys,re,math,collections
feat='';x=y=None;c=collections.Counter()
for line in open(sys.argv[1]):
    if line.startswith('; FEATURE:'): feat=line.split(':',1)[1].strip()
    elif line.startswith(('G1','G0')):
        m=dict((k,float(v)) for k,v in re.findall(r'([XYE])([-\d.]+)',line.split(';')[0])); nx,ny=m.get('X',x),m.get('Y',y)
        if feat=='Ironing' and x is not None and nx is not None:
            L=math.hypot(nx-x,ny-y)
            if L>3: c[round(math.degrees(math.atan2(ny-y,nx-x))%180/5)*5%180]+=L
        x,y=nx,ny
tot=sum(c.values()) or 1; print({k:f'{v/tot:.0%}' for k,v in c.most_common(3)})
