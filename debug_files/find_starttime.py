"""查找 starttime 的设置"""
import re

js = open('jqmobo2.js', 'r', encoding='utf-8').read()

print("=== 查找 #starttime ===")
idx = js.find('#starttime')
if idx > 0:
    print(js[idx-200:idx+200])

print("\n=== 查找 starttime 赋值 ===")
matches = re.findall(r'starttime[^;]{0,200}', js)
for m in matches[:10]:
    if 'val(' in m or '=' in m:
        print(m)
        print("---")

print("\n=== 查找页面加载时间 ===")
matches = re.findall(r'(new Date|Date\.now|getTime)[^;]{0,100}', js)
for m in matches[:10]:
    print(m)
    print("---")
