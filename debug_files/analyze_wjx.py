"""深入分析问卷星的签名算法"""
import requests
import re

# 获取问卷星的JS文件
url = "https://v.wjx.cn/vm/mR4RDSc.aspx"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

response = requests.get(url, headers=headers)
html = response.text

# 查找所有外部JS文件
js_files = re.findall(r'src=["\']([^"\']*\.js[^"\']*)["\']', html)
print("外部JS文件:")
for js in js_files:
    print(f"  {js}")

# 查找内联脚本中的关键函数
print("\n查找 dataenc 相关代码:")
dataenc_patterns = [
    r'dataenc\s*[=:]\s*function[^{]*\{([^}]+)\}',
    r'function\s+dataenc[^{]*\{([^}]+)\}',
    r'dataenc\([^)]*\)',
]

for pattern in dataenc_patterns:
    matches = re.findall(pattern, html, re.DOTALL)
    if matches:
        print(f"  Pattern: {pattern[:30]}...")
        for m in matches[:3]:
            print(f"    {m[:200]}...")

# 查找 jqsign 相关代码
print("\n查找 jqsign 相关代码:")
jqsign_context = re.findall(r'.{0,100}jqsign.{0,100}', html, re.IGNORECASE)
for ctx in jqsign_context[:5]:
    print(f"  {ctx[:150]}")

# 查找提交相关代码
print("\n查找 submit 相关代码:")
submit_patterns = [
    r'submitdata\s*[=:][^;]+',
    r'processjq[^;]+',
]
for pattern in submit_patterns:
    matches = re.findall(pattern, html)
    for m in matches[:3]:
        print(f"  {m[:150]}")

# 下载并分析主要的JS文件
print("\n\n=== 分析外部JS文件 ===")
for js_url in js_files[:5]:
    if not js_url.startswith('http'):
        if js_url.startswith('//'):
            js_url = 'https:' + js_url
        elif js_url.startswith('/'):
            js_url = 'https://v.wjx.cn' + js_url
    
    try:
        js_response = requests.get(js_url, headers=headers, timeout=10)
        js_content = js_response.text
        
        # 查找签名相关代码
        if 'dataenc' in js_content.lower() or 'jqsign' in js_content.lower():
            print(f"\n{js_url} 包含签名相关代码:")
            
            # 查找 dataenc 函数
            dataenc_match = re.search(r'dataenc\s*[:=]\s*function[^{]*\{[^}]+\}', js_content)
            if dataenc_match:
                print(f"  dataenc: {dataenc_match.group(0)[:300]}")
            
            # 查找签名计算
            sign_match = re.search(r'jqsign[^;]{0,200}', js_content)
            if sign_match:
                print(f"  jqsign: {sign_match.group(0)[:200]}")
    except Exception as e:
        print(f"  Error loading {js_url}: {e}")
