# 工具：命令列切片與 G-code 分析

## Bambu Studio 命令列切片（macOS）
```bash
/Applications/BambuStudio.app/Contents/MacOS/BambuStudio --slice 1 --outputdir OUT file.3mf > log.txt 2>&1
```
- `--slice 0` 會切所有 plate。產出 `OUT/plate_1.gcode` 和 `OUT/result.json`。
- macOS 沒有 `timeout` 指令，不要加。
- 失敗時看 log 的 `[error]`。例：`gcode path conflicts found between A and B` 代表物件在盤上重疊，要請使用者按 A（自動擺放）。

## 從 G-code 讀資料
- 檔頭 `; key = value` 是實際使用的設定，例如 `; ironing_direction = 90`。
- `; total estimated time`：總時間。
- `; Z_HEIGHT:` 每層高度；`; FEATURE:` 特徵類型；換料是 `M620 S{n}A` … `M621`。
- `result.json` → `sliced_plates[0].feature_type_times`（秒）、`filament_change_times`。
- 每個物件的走線在 `; start printing object, unique label id: N` 和 `; stop printing object` 之間。
- 量尺寸：外牆走線端點到圓心的距離，再加減半個線寬。開了圓弧擬合時圓是 G2/G3，要一起算；內部填充是長直線，只有端點，不能拿來量。
- 暫停：`M400 U1`。要確認暫停在哪層，往前找最近的 `; Z_HEIGHT`。
- 逐件列印間距不夠時，CLI 會直接失敗（exit 193），log 有 `got error when validate: … is too close to others`。

- 換料碼要比對 `T0`～`T9`。`T1000` 這類是換料巨集，不是耗材編號。
- **`enable_arc_fitting` 開著時有大量 G2/G3**。只解析 G1 會漏掉小圈，曾因此把「有一小圈」誤判成「沒有線」。

## scripts/
| 腳本 | 用途 |
|---|---|
| `bambu_3mf_set.py in.3mf out.3mf '{"key":"val"}' [--strip-paint]` | 改專案參數後另存新檔；list 型參數給單值會自動複製成每個耗材一份；`--strip-paint` 清除分色 |
| `bambu_line_angles.py plate_1.gcode [--tool]` | 逐層列出各特徵（或各耗材）的主要走線角度 |
| `bambu_ironing_angle.py plate_1.gcode` | 熨燙走線的實際角度 |
| `bambu_region_coverage.py plate_1.gcode region.json` | 每層在指定區域（例如刻字範圍）的出料長度，用來確認刻字實際深度；座標要換成熱床座標 |
| `bambu_3mf_diff.py a.3mf b.3mf [--all]` | 比對兩個專案的參數，先列出各自套的設定名稱 |
| `bambu_3mf_objects.py list/swap/add/drop/move …` | 換網格（位置不動）、加物件、刪物件、移位置。說明在檔頭 |
| `bambu_gcode_objects.py plate_1.gcode [--circle X,Y --z Z --min/--max]` | 每個物件的實際範圍和高度；量孔或圓柱印出來的半徑（含圓孔校正） |
| `bambu_top_layer_plot.py out.png a.gcode:標籤 b.gcode:標籤` | 多個 G-code 的最上層走線上下對照（含弧線），看字洞、細節；用眼睛比，不要只靠自動計數 |
| `bambu_3mf_scale_xy.py in.3mf out.3mf 1.08` | 只放大 XY，保留設定、部件和厚度 |
| `bambu_footprint_plot.py out.png --box x0,x1,y0,y1 [--zmin Z] [--mirror] a.gcode:標籤 …` | 頂層走線畫成實心足跡（依 E 值算線寬），模擬凸字／印章面印出來會不會斷、字洞會不會被填 |
| `bambu_feature_grid.py plate_1.gcode Ironing "X:欄,…" "Y:列,…" [--ref E/mm:值]` | 測試片逐格量某特徵的 E/mm 和速度，對照刻的數字；設定錯位時切片照樣成功，只有這樣才抓得到 |

## 3mf 結構
- 3mf 是 zip。參數在 `Metadata/project_settings.config`（JSON），改過的 key 要加進 `different_settings_to_system[0]`（分號分隔；有些檔案沒有這個欄位，要能容忍）。
- 物件層級的覆寫設定在 `Metadata/model_settings.config` 的 `<object>` 底下（`<metadata key="..." value="..."/>`）。
- 分色資訊在 `3D/Objects/*.model` 的 `paint_color` 屬性。
- `.gcode.3mf`（匯出切片檔）不一定有可編輯的模型；要改模型請使用者用「儲存專案」。
- **多部件物件（分色薄片）**：`3D/Objects/object_N.model` 放多個 `<object>` 網格；`3D/3dmodel.model` 的 `<components>` 各列一個；`model_settings.config` 用 `<part>` 加 `<metadata key="extruder" value="n"/>` 指定耗材。頂點座標以 `source_offset_x/y/z` 為原點。
- 物件在盤上的位置：`Metadata/plate_1.json` 的 `bbox_objects`；正確的擺放（含旋轉）是 `3D/3dmodel.model` 的 `<item transform>`（3×3 旋轉＋XYZ 位移）。Z 軸是 −1 代表在 Bambu 裡被翻過面，**不要只看 STL 檔名判斷列印方向**。
- 網格在 `3D/Objects/*.model`，以自己的中心點置中。同一個 STL 複製多份時，多個物件會共用同一份網格。
- **`Objects/*.model` 裡的 object id 在整個 3mf 內要唯一**：加物件時如果用了跟別的檔案一樣的 id，Bambu 會讀到別的網格（實測：加入的圓蓋變成被切半的後殼）。加物件要同時改 `3dmodel.model`（resources＋build item）、`model_settings.config`（object、plate 的 model_instance、assemble）、`_rels`。用 `scripts/bambu_3mf_objects.py`。
- 加完物件一定要切片，用 `bambu_gcode_objects.py` 確認每個物件的高度和位置。
- **高度範圍修改器（只改某幾層的設定）**：寫進 `Metadata/layer_config_ranges.xml`（實測 02.08 CLI 有效）。`<object id>` 要用**物件在 `3D/3dmodel.model` 裡的順序（從 1 開始）**，不是 resource id（用 id 6 沒效果，用順序 3 才有效）。`min_z`／`max_z` 是熱床上的列印高度。驗證方法：比較該層的 Bridge E/mm。
  ```xml
  <objects><object id="3"><range min_z="16.1" max_z="16.25">
    <option opt_key="extruder">0</option><option opt_key="layer_height">0.16</option>
    <option opt_key="bridge_flow">1</option></range></object></objects>
  ```

## 從多零件 3mf 刪零件（2026-11-10 實測）

- 有 `3D/Objects/object_1.model` 的 3mf（元件模式），`model_settings.config` 的 `<part id="N">` 是對到 **`component objectid="N"`**，不是第 N 個零件。
- 刪零件時：刪掉 component 和對應的 `<part>`，**不要重新編號 part id**。重新編號會讓每片的熨燙／流量設定套到錯的零件或失效，切片照樣成功，不會報錯。
- 換掉某個零件的網格後，順手更新 `mesh_stat face_count` 和物件的 `face_count`（沒驗證是否必要，但無害）。
- 交付前一定要用 G-code 逐片量（熨燙用 E/mm 對比 15% 的基準、F 值讀速度），只看切片成功不夠。

## 改模型網格的小技巧（2026-11-10）
- 裁切、搬移、切掉底部：用 `manifold3d`（`Manifold ^ box` 交集、`.translate`、`+` 聯集），在元件的局部座標裡算，寫回 `3D/Objects/object_1.model` 的同一個 object id。
- 把物件往下沉（item 的 Z 平移變小）切片也能少印底部，但 Bambu 介面開檔可能把它拉回板上；**直接把網格底部切掉比較可靠**。
- 只縮 XY：改 build item 的矩陣。注意有旋轉的 item（STEP 匯入常見 Y 朝上），要縮的是對應到熱床 X、Y 的那兩個係數，高度係數不動。
- **`bambu_3mf_objects.py swap` 沒加 `--file` 會換掉 3mf 裡所有物件檔的網格**（盤上多個不同模型時會全部變成同一個）。只換一個模型時一定要加 `--file object_N.model`；同一個 object 檔被兩個物件共用時，兩個會一起換（正好適合「盤上兩顆同款」）。
