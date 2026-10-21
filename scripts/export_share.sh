#!/bin/zsh
# 打包可分享版本：排除 personal/，並檢查有沒有殘留個人路徑。
# 用法: scripts/export_share.sh [輸出資料夾，預設 ~/Desktop；如果是 git repo 就直接同步進去]
set -e
SK="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-$HOME/Desktop}"
TMP="$(mktemp -d)/3d-print-advisor"
mkdir -p "$TMP"
rsync -a --exclude 'personal/' --exclude '.DS_Store' --exclude '__pycache__' "$SK/" "$TMP/"
# 檢查目前這台電腦的使用者名稱、家目錄路徑有沒有出現在要分享的檔案裡
PATTERN="/Users/|/home/|$USER"
if grep -rn -E "$PATTERN" "$TMP" --include='*.md' --include='*.py' --include='*.yaml' --include='*.sh' | grep -v 'export_share.sh'; then
  echo "⚠️ 上面這些地方還有個人資訊，請先改掉再分享。"; exit 1
fi
if [ -d "$OUT/.git" ]; then
  # 目標是 git repo：同步內容（保留 .git），之後再自己 commit／push
  rsync -a --delete --exclude '.git/' --exclude '.gitignore' "$TMP/" "$OUT/"
  echo "已同步到 repo：$OUT（不含 personal/），請 commit 後 push"
else
  (cd "$(dirname "$TMP")" && zip -qr "$OUT/3d-print-advisor.zip" 3d-print-advisor)
  echo "已輸出：$OUT/3d-print-advisor.zip（不含 personal/）"
fi
