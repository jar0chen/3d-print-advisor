"""把多個 G-code 的最上層走線畫成上下對照圖，用來目視確認細節（例：字洞裡有沒有另一色的走線）。
用法: python3 bambu_top_layer_plot.py out.png a/plate_1.gcode:標籤 b/plate_1.gcode:標籤 [--z 4.0] [--pad 1]
- 畫面自動裁到第二色（T1）的範圍；只有單色時裁到全部走線
- 不畫熨燙和擦料塔；G1 與 G2/G3 弧線都會畫
- 自動數字容易誤判（周圍的走線會被算進去），這張圖要用眼睛看
需要 matplotlib。
"""
import re,sys,math,collections
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
A=sys.argv[1:]; Zarg=None; pad=1.0
if '--z' in A: i=A.index('--z'); Zarg=float(A[i+1]); del A[i:i+2]
if '--pad' in A: i=A.index('--pad'); pad=float(A[i+1]); del A[i:i+2]
out,items=A[0],A[1:]
COL=['#e8692a','#111111','#2a7de8','#2aa84f']
def num(l,c):
    m=re.search(rf'{c}(-?[\d.]+)',l); return float(m.group(1)) if m else None
def arc(x,y,nx,ny,i,j,cw,n=24):
    cx,cy=x+i,y+j; r=math.hypot(i,j); a0=math.atan2(y-cy,x-cx); a1=math.atan2(ny-cy,nx-cx)
    if cw and a1>=a0: a1-=2*math.pi
    if not cw and a1<=a0: a1+=2*math.pi
    return [(cx+r*math.cos(a0+(a1-a0)*k/n),cy+r*math.sin(a0+(a1-a0)*k/n)) for k in range(n+1)]
def load(gc):
    tool=None;z=0.;x=y=None;typ='';L=collections.defaultdict(list)
    for l in open(gc,errors='ignore'):
        if l.startswith('; Z_HEIGHT:'): z=float(l.split(':')[1])
        elif l.startswith('; FEATURE:'): typ=l.split(':',1)[1].strip()
        s=l.split(';')[0].strip()
        if re.fullmatch(r'T\d',s): tool=int(s[1])   # T1000 之類是換料巨集，不是耗材編號
        if not re.match(r'G[123]\b',s): continue
        nx,ny,e=num(s,'X'),num(s,'Y'),num(s,'E')
        nx=x if nx is None else nx; ny=y if ny is None else ny
        if e and e>0 and x is not None and (nx,ny)!=(x,y) and typ not in('Ironing','Prime tower'):
            pts=[(x,y),(nx,ny)] if s[:2]=='G1' else arc(x,y,nx,ny,num(s,'I') or 0,num(s,'J') or 0,s[:2]=='G2')
            L[round(z,3)].append((tool,pts))
        x,y=nx,ny
    return L
fig,ax=plt.subplots(len(items),1,figsize=(13,2.8*len(items)),squeeze=False)
for a,it in zip(ax[:,0],items):
    gc,_,label=it.partition(':'); L=load(gc); z=Zarg if Zarg is not None else max(L)
    keep=[p for t,p in L[round(z,3)] if t==1] or [p for t,p in L[round(z,3)]]
    xs=[q[0] for p in keep for q in p]; ys=[q[1] for p in keep for q in p]
    for t,p in L[round(z,3)]: a.plot(*zip(*p),color=COL[(t or 0)%4],lw=1.6)
    a.set_aspect('equal'); a.set_xlim(min(xs)-pad,max(xs)+pad); a.set_ylim(min(ys)-pad,max(ys)+pad); a.axis('off'); a.set_title(f'{label or gc}  z={z}')
plt.savefig(out,dpi=110,bbox_inches='tight'); print('ok',out)
