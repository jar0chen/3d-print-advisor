"""只放大 3mf 內所有網格的 XY（Z 不動），另存新檔。設定、部件、耗材都保留。
用法: python3 -I bambu_3mf_scale_xy.py in.3mf out.3mf 1.08
- 網格座標要以物件中心為原點（Bambu 存的專案通常是）；吊孔等功能孔也會跟著放大，要原尺寸得另外補回
- Z 不動，才能維持分色薄片對齊切片層
"""
import re,sys,zipfile
src,dst,f=sys.argv[1],sys.argv[2],float(sys.argv[3])
zin=zipfile.ZipFile(src); z=zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED)
V=re.compile(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"')
for i in zin.infolist():
    b=zin.read(i.filename)
    if i.filename.startswith('3D/Objects/'):
        b=V.sub(lambda m:f'<vertex x="{float(m[1])*f:.6f}" y="{float(m[2])*f:.6f}" z="{m[3]}"',b.decode()).encode()
    z.writestr(i,b)
z.close(); print('ok',dst)
