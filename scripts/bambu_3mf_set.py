"""改 Bambu 3mf 的切片參數(另存新檔)，可選擇清除分色上色。
用法: python3 -I bambu_3mf_set.py in.3mf out.3mf '{"key":"value",...}' [--strip-paint]
- list 型參數給單值會自動複製成每個耗材一份
- 改過的 key 會加進 different_settings_to_system[0]
"""
import json,sys,zipfile,re
src,out=sys.argv[1],sys.argv[2]; ch=json.loads(sys.argv[3]); strip='--strip-paint' in sys.argv
zin=zipfile.ZipFile(src); p='Metadata/project_settings.config'; d=json.loads(zin.read(p))
for k,v in ch.items():
    if k not in d: print('WARN 未知參數:',k)
    if isinstance(d.get(k),list) and not isinstance(v,list): v=[v]*len(d[k])
    d[k]=v
if d.get('different_settings_to_system'):   # some saved projects do not carry this field
    ds=set(filter(None,d['different_settings_to_system'][0].split(';')))|set(ch)
    d['different_settings_to_system'][0]=';'.join(sorted(ds))
z=zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED)
for i in zin.infolist():
    b=zin.read(i.filename)
    if i.filename==p: b=json.dumps(d,indent=4,ensure_ascii=False).encode()
    elif strip and i.filename.startswith('3D/Objects/'): b=re.sub(rb' paint_color="[^"]*"',b'',b)
    z.writestr(i,b)
z.close(); print('ok', out)
