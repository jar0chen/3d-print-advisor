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

## scripts/
| 腳本 | 用途 |
|---|---|
| `bambu_3mf_set.py in.3mf out.3mf '{"key":"val"}' [--strip-paint]` | 改專案參數後另存新檔；list 型參數給單值會自動複製成每個耗材一份；`--strip-paint` 清除分色 |
| `bambu_line_angles.py plate_1.gcode [--tool]` | 逐層列出各特徵（或各耗材）的主要走線角度 |
| `bambu_ironing_angle.py plate_1.gcode` | 熨燙走線的實際角度 |
| `bambu_region_coverage.py plate_1.gcode region.json` | 每層在指定區域（例如刻字範圍）的出料長度，用來確認刻字實際深度；座標要換成熱床座標 |

## 3mf 結構
- 3mf 是 zip。參數在 `Metadata/project_settings.config`（JSON），改過的 key 要加進 `different_settings_to_system[0]`（分號分隔；有些檔案沒有這個欄位，要能容忍）。
- 物件層級的覆寫設定在 `Metadata/model_settings.config` 的 `<object>` 底下（`<metadata key="..." value="..."/>`）。
- 分色資訊在 `3D/Objects/*.model` 的 `paint_color` 屬性。
- `.gcode.3mf`（匯出切片檔）不一定有可編輯的模型；要改模型請使用者用「儲存專案」。
- 物件在盤上的位置：`Metadata/plate_1.json` 的 `bbox_objects`。
- **高度範圍修改器（只改某幾層的設定）**：寫進 `Metadata/layer_config_ranges.xml`（實測 02.08 CLI 有效）。`<object id>` 要用**物件在 `3D/3dmodel.model` 裡的順序（從 1 開始）**，不是 resource id（用 id 6 沒效果，用順序 3 才有效）。`min_z`／`max_z` 是熱床上的列印高度。驗證方法：比較該層的 Bridge E/mm。
  ```xml
  <objects><object id="3"><range min_z="16.1" max_z="16.25">
    <option opt_key="extruder">0</option><option opt_key="layer_height">0.16</option>
    <option opt_key="bridge_flow">1</option></range></object></objects>
  ```
