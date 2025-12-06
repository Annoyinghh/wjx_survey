"""查找签名相关代码"""
import re

html = open('survey_page_debug.html', 'r', encoding='utf-8').read()

# 查找所有script标签
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE)
print(f"找到 {len(scripts)} 个script标签")

# 查找签名相关代码
keywords = ['jqsign', 'dataenc', 'encrypt', 'sign', 'nonce', 'submitdata']
for i, script in enumerate(scripts):
    for kw in keywords:
        if kw.lower() in script.lower():
            print(f"\n=== Script {i+1} 包含 '{kw}' ===")
            # 找到包含关键词的行
            lines = script.split('\n')
            for j, line in enumerate(lines):
                if kw.lower() in line.lower():
                    # 打印上下文
                    start = max(0, j-2)
                    end = min(len(lines), j+3)
                    for k in range(start, end):
                        marker = ">>>" if k == j else "   "
                        print(f"{marker} {lines[k][:150]}")
            break

# 查找 dataenc 函数
dataenc_match = re.search(r'function\s+dataenc[^{]*\{[^}]+\}', html, re.DOTALL)
if dataenc_match:
    print("\n=== dataenc 函数 ===")
    print(dataenc_match.group(0)[:500])

# 查找 jqnonce 相关
nonce_match = re.search(r'jqnonce["\s:=]+["\']?([a-zA-Z0-9]+)', html)
if nonce_match:
    print(f"\njqnonce: {nonce_match.group(1)}")
