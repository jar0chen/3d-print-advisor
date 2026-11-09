"""比對兩個 Bambu 3mf 的專案參數。
用法: python3 -I bambu_3mf_diff.py a.3mf b.3mf [--all]
先印出兩邊的 print_settings_id／filament_settings_id，再列出不同的參數。
預設略過跟列印無關的雜項（耗材烘乾資訊、價格、版本），加 --all 全部列出。
常見發現：同系列的檔案裡，有一份其實套的是原廠預設（例："0.16mm High Quality @BBL A1M"），
檔名寫的流量、速度都沒有寫進去。
"""
import sys, json, zipfile

SKIP = ('filament_dev_', 'filament_cost', 'version', 'upward_compatible_machine', 'different_settings_to_system')


def load(p):
    return json.loads(zipfile.ZipFile(p).read('Metadata/project_settings.config'))


a, b = load(sys.argv[1]), load(sys.argv[2])
show_all = '--all' in sys.argv
for k in ('print_settings_id', 'filament_settings_id', 'printer_settings_id'):
    print(f'{k}:\n  A: {a.get(k)}\n  B: {b.get(k)}')
print()
for k in sorted(set(a) | set(b)):
    if a.get(k) == b.get(k):
        continue
    if not show_all and (k.startswith(SKIP) or a.get(k) is None or b.get(k) is None):
        continue
    print(f'{k}\n  A: {str(a.get(k))[:120]}\n  B: {str(b.get(k))[:120]}')
