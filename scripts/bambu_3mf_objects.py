"""改 Bambu 3mf 裡的物件（另存新檔，不改原檔）。實測 Bambu Studio 02.09（A1 mini）。

子指令:
  swap   in.3mf out.3mf mesh.stl [--file object_23.model]
         換掉網格，盤上位置、旋轉、設定都不動。新網格會照舊網格的方式置中（XY 中心、Z 中心對齊舊網格），
         所以 mesh.stl 要跟原本匯入的 STL 用同一個座標系（例如同一份 *_PRINT.stl 的新版）。
  add    in.3mf out.3mf mesh.stl x,y [x,y ...]
         加入新物件（每個座標一顆，不旋轉、平放在熱床上）。用全域唯一的 object id。
  drop   in.3mf out.3mf id[,id...]
         刪除物件（id 是 3dmodel.model 裡 <item objectid>）。
  move   in.3mf out.3mf '{"id":[x,y],...}'
         只改物件在熱床上的 XY，旋轉不變。
  list   in.3mf
         列出物件 id、名稱、耗材、位置。

注意:
- Objects/*.model 裡的 object id 在整個 3mf 內要唯一。撞號時 Bambu 會讀到別的檔案的網格（實測：加入的圓蓋變成被切半的後殼）。
- 3dmodel.model 的 <item transform> 才是真正的擺放方向，不要只看 STL 檔名（*_outer_up 可能在 Bambu 裡又被翻過）。
- 改完一定要用 CLI 切片確認（見 references/tools.md）。
"""
import sys, re, json, uuid, zipfile

U = lambda: str(uuid.uuid4())


def rw(src, out, edit):
    zin = zipfile.ZipFile(src)
    files = {i.filename: zin.read(i.filename) for i in zin.infolist()}
    extra = edit(files) or {}
    z = zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED)
    for i in zin.infolist():
        z.writestr(i, files[i.filename])
    for k, v in extra.items():
        z.writestr(k, v)
    z.close()


def load_mesh(stl):
    import trimesh
    m = trimesh.load(stl, process=False)
    m.merge_vertices(digits_vertex=6)
    assert m.is_watertight and m.is_volume, f'{stl} 不是封閉實體'
    return m


def mesh_xml(v, f):
    return ('<mesh>\n    <vertices>\n'
            + ''.join(f'     <vertex x="{a:.7g}" y="{b:.7g}" z="{c:.7g}"/>\n' for a, b, c in v)
            + '    </vertices>\n    <triangles>\n'
            + ''.join(f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>\n' for a, b, c in f)
            + '    </triangles>\n   </mesh>')


def verts_of(s):
    import numpy as np
    return np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', s), float)


def cmd_swap(src, out, stl, only=None):
    import numpy as np
    m = load_mesh(stl)

    def edit(F):
        n = 0
        for k in list(F):
            if not k.startswith('3D/Objects/') or b'<mesh>' not in F[k]:
                continue
            if only and not k.endswith(only):
                continue
            s = F[k].decode()
            old = verts_of(s)
            oc = (old.min(0) + old.max(0)) / 2
            nc = (m.vertices.min(0) + m.vertices.max(0)) / 2
            v = m.vertices - nc + oc
            s, k2 = re.subn(r'<mesh>.*?</mesh>', lambda _: mesh_xml(v, m.faces), s, flags=re.S)
            F[k] = s.encode(); n += k2
        ms = F['Metadata/model_settings.config'].decode()
        ms = re.sub(r'face_count="\d+"', f'face_count="{len(m.faces)}"', ms)
        F['Metadata/model_settings.config'] = ms.encode()
        print('換掉網格', n, '個；面數', len(m.faces))
        assert n, '沒有找到網格'
    rw(src, out, edit)


def cmd_add(src, out, stl, pos):
    import os
    m = load_mesh(stl)
    h = m.bounds[1][2] - m.bounds[0][2]
    c = (m.bounds[0] + m.bounds[1]) / 2
    v = m.vertices - c
    name = os.path.basename(stl)

    def edit(F):
        model = F['3D/3dmodel.model'].decode()
        allids = [int(x) for k, b in F.items() if k.endswith('.model') for x in re.findall(r'<object id="(\d+)"', b.decode())]
        mesh_id = max(allids) + 100
        lp = f'3D/Objects/object_add{mesh_id}.model'
        objfile = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
                   'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
                   'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">\n'
                   ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n'
                   f'  <object id="{mesh_id}" p:UUID="{U()}" type="model">\n   ' + mesh_xml(v, m.faces) +
                   '\n  </object>\n </resources>\n <build/>\n</model>\n')
        top = [int(x) for x in re.findall(r'<item objectid="(\d+)"', model)]
        nid = max(top) + 1
        ms = F['Metadata/model_settings.config'].decode()
        idents = [int(x) for x in re.findall(r'key="identify_id" value="(\d+)"', ms)] or [100]
        res = items = cfg = inst = asm = ''
        for k, (x, y) in enumerate(pos):
            oid = nid + k
            res += (f'  <object id="{oid}" p:UUID="{U()}" type="model">\n   <components>\n'
                    f'    <component p:path="/{lp}" objectid="{mesh_id}" p:UUID="{U()}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n'
                    '   </components>\n  </object>\n')
            items += f'  <item objectid="{oid}" p:UUID="{U()}" transform="1 0 0 0 1 0 0 0 1 {x} {y} {h/2}" printable="1"/>\n'
            cfg += (f'  <object id="{oid}">\n    <metadata key="name" value="{name} {k+1}"/>\n'
                    '    <metadata key="extruder" value="1"/>\n'
                    f'    <metadata face_count="{len(m.faces)}"/>\n'
                    f'    <part id="1" subtype="normal_part" uuid="{U()}">\n'
                    f'      <metadata key="name" value="{name}"/>\n'
                    '      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n'
                    f'      <metadata key="source_file" value="{name}"/>\n'
                    '      <metadata key="source_object_id" value="0"/>\n      <metadata key="source_volume_id" value="0"/>\n'
                    '      <metadata key="source_offset_x" value="0"/>\n      <metadata key="source_offset_y" value="0"/>\n'
                    f'      <metadata key="source_offset_z" value="{h/2}"/>\n'
                    f'      <mesh_stat face_count="{len(m.faces)}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>\n'
                    '    </part>\n  </object>\n')
            inst += ('    <model_instance>\n'
                     f'      <metadata key="object_id" value="{oid}"/>\n      <metadata key="instance_id" value="0"/>\n'
                     f'      <metadata key="identify_id" value="{max(idents)+100+k}"/>\n    </model_instance>\n')
            asm += (f'   <assemble_item object_id="{oid}" instance_id="0" transform="1 0 0 0 1 0 0 0 1 {x} {y} {h/2}" offset="0 0 0" />\n'
                    f'   <assemble_item object_id="{oid}" volume_id="0" transform="1 0 0 0 1 0 0 0 1 0 0 0" />\n')
        model = model.replace(' </resources>', res + ' </resources>', 1)
        model = model.replace(' </build>', items + ' </build>', 1)
        ms = ms.replace('  <plate>', cfg + '  <plate>', 1).replace('  </plate>', inst + '  </plate>', 1)
        ms = ms.replace('  </assemble>', asm + '  </assemble>', 1)
        rels = F['3D/_rels/3dmodel.model.rels'].decode().replace(
            '</Relationships>',
            f' <Relationship Target="/{lp}" Id="rel-add{mesh_id}" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n</Relationships>')
        F['3D/3dmodel.model'] = model.encode(); F['Metadata/model_settings.config'] = ms.encode()
        F['3D/_rels/3dmodel.model.rels'] = rels.encode()
        print(f'加入 {len(pos)} 個物件，id {nid}–{nid+len(pos)-1}，網格 id {mesh_id}')
        return {lp: objfile}
    rw(src, out, edit)


def cmd_drop(src, out, ids):
    def edit(F):
        model = F['3D/3dmodel.model'].decode(); ms = F['Metadata/model_settings.config'].decode()
        for d in ids:
            model = re.sub(r'  <object id="%s" [^>]*>.*?</object>\n' % d, '', model, flags=re.S)
            model = re.sub(r'  <item objectid="%s" [^>]*/>\n' % d, '', model)
            ms = re.sub(r'  <object id="%s">.*?</object>\n' % d, '', ms, flags=re.S)
            ms = re.sub(r'    <model_instance>\n      <metadata key="object_id" value="%s"/>.*?</model_instance>\n' % d, '', ms, flags=re.S)
            ms = re.sub(r'   <assemble_item object_id="%s" [^\n]*\n' % d, '', ms)
        F['3D/3dmodel.model'] = model.encode(); F['Metadata/model_settings.config'] = ms.encode()
        print('剩下物件', re.findall(r'<item objectid="(\d+)"', model))
    rw(src, out, edit)


def cmd_move(src, out, pos):
    def edit(F):
        s = F['3D/3dmodel.model'].decode()

        def f(m):
            t = m.group(3).split()
            if m.group(2) in pos:
                t[9], t[10] = str(pos[m.group(2)][0]), str(pos[m.group(2)][1])
            return m.group(1) + ' '.join(t) + '"'
        F['3D/3dmodel.model'] = re.sub(r'(<item objectid="(\d+)" [^>]*?transform=")([^"]*)"', f, s).encode()
    rw(src, out, edit)


def cmd_list(src):
    z = zipfile.ZipFile(src)
    model = z.read('3D/3dmodel.model').decode(); ms = z.read('Metadata/model_settings.config').decode()
    names = dict(re.findall(r'<object id="(\d+)">\s*<metadata key="name" value="([^"]*)"', ms))
    ext = dict(re.findall(r'<object id="(\d+)">\s*<metadata key="name" value="[^"]*"/>\s*<metadata key="extruder" value="(\d+)"', ms))
    for oid, t in re.findall(r'<item objectid="(\d+)" [^>]*?transform="([^"]*)"', model):
        t = t.split()
        print(oid, names.get(oid, '?'), '耗材', ext.get(oid, '?'), '位置', t[9], t[10], 'Z軸翻轉' if float(t[8]) < 0 else '')


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(1)
    c = a[0]
    if c == 'swap':
        cmd_swap(a[1], a[2], a[3], a[a.index('--file') + 1] if '--file' in a else None)
    elif c == 'add':
        cmd_add(a[1], a[2], a[3], [tuple(map(float, p.split(','))) for p in a[4:]])
    elif c == 'drop':
        cmd_drop(a[1], a[2], a[3].split(','))
    elif c == 'move':
        cmd_move(a[1], a[2], json.loads(a[3]))
    elif c == 'list':
        cmd_list(a[1])
    else:
        print(__doc__); sys.exit(1)
