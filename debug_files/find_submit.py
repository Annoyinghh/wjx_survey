"""查找完整的提交逻辑"""
import re

js = open('jqmobo2.js', 'r', encoding='utf-8').read()

# 查找 jqnonce 和 jqsign 的完整上下文
print("=== 查找 jqnonce 和 jqsign 的使用 ===")
idx = js.find('jqnonce&&')
if idx > 0:
    print(js[idx:idx+300])

print("\n=== 查找 submitdata 的构建 ===")
# 查找 submitdata 的构建逻辑
idx = js.find('submitdata:')
if idx > 0:
    print(js[idx-100:idx+200])

print("\n=== 查找 POST 请求 ===")
# 查找 ajax 或 post 请求
ajax_matches = re.findall(r'\.ajax\([^)]{0,500}\)', js)
for m in ajax_matches[:3]:
    if 'processjq' in m or 'submit' in m.lower():
        print(m[:300])
        print("---")

print("\n=== 查找 form 提交 ===")
form_matches = re.findall(r'\.submit\([^)]*\)', js)
for m in form_matches[:5]:
    print(m)
