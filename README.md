# 3d-print-advisor

給 AI 程式助理（**Codex**、**Claude Code**）用的 FDM 3D 列印顧問技能，以 **Bambu Studio／Bambu Lab 印表機**為主。

裝好之後，直接跟助理對話就會自動用到，例如：
- 「幫我看這份 3mf 的參數哪裡可以優化」
- 「透明 PETG 要怎麼讓每層走線都同方向」
- 「這個刻字印得出來嗎？」
- 「圓柱塞不進孔，幫我改模型」

助理會用 Bambu Studio 的命令列切片，從 G-code 讀出實際的溫度、層高、走線角度、刻字深度和時間分配，**驗證過再回報**，而不是用猜的。

## 內容
| 檔案 | 說明 |
|---|---|
| `SKILL.md` | 入口：什麼時候用、必守規則、回報方式 |
| `references/bambu-slicing.md` | Bambu Studio 設定的坑：走線方向、熨燙方向、層高對齊、支撐、封孔、圓孔校正 |
| `references/calibration.md` | 校正與排查：牽絲、附著、橋接、支撐 Top Z、透明 PETG |
| `references/modeling-for-fdm.md` | 為了好印而改模型：線寬檢查、刻字、彈片、模型板澆口、外殼受力 |
| `references/tools.md` | 命令列切片、G-code 和 3mf 結構 |
| `scripts/` | G-code 分析（走線角度、熨燙角度、刻字區出料）、3mf 參數修改 |

## 安裝
```bash
# Codex
git clone https://github.com/jar0chen/3d-print-advisor ~/.codex/skills/3d-print-advisor
# Claude Code
git clone https://github.com/jar0chen/3d-print-advisor ~/.claude/skills/3d-print-advisor
```
裝好後開一個新對話就會生效。

**需求**：macOS 上安裝 Bambu Studio（命令列切片用）；Python 3（腳本只用標準函式庫）。

## 個人設定（選用）
在技能資料夾裡建 `personal/profile.md`，寫下你的機型、噴嘴、列印板、線材校正值和偏好，助理開工時會先讀。沒有這個檔案時，助理會先問你的機型和線材。

## 注意
- 實測數值來自 **Bambu Lab A1 mini＋Bambu Studio 02.08**。像「熨燙實際角度＝設定值＋45°」「開圓孔校正時小孔會大 0.4–0.5mm」這類結果，換機型或版本時要重新驗證。
- 「切片成功」不等於「印得好」；技能會區分 G-code 已驗證的部分和需要實印確認的部分。

## 維護者用
- 個人紀錄 `personal/knowledge-log.md` 不會被分享。
- `scripts/export_share.sh <目的地>`：打包分享版（排除 `personal/`，並檢查有沒有殘留個人路徑）。目的地是 git repo 時，會直接同步進去。
