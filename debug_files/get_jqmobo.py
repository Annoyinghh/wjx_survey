"""下载并分析 jqmobo2.js"""
import requests
import re

url = "https://image.wjx.cn/joinnew/js/jqmobo2.js?v=6703"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

response = requests.get(url, headers=headers)
js = response.text

# 保存完整JS
with open('jqmobo2.js', 'w', encoding='utf-8') as f:
    f.write(js)
print(f"JS文件已保存 ({len(js)} 字节)")

# 查找关键函数
print("\n=== 查找 dataenc ===")
dataenc_matches = re.findall(r'dataenc[^;]{0,500}', js)
for m in dataenc_matches[:5]:
    print(m[:200])
    print("---")

print("\n=== 查找 jqsign ===")
jqsign_matches = re.findall(r'jqsign[^;]{0,300}', js)
for m in jqsign_matches[:5]:
    print(m[:200])
    print("---")

print("\n=== 查找 submitdata ===")
submitdata_matches = re.findall(r'submitdata[^;]{0,300}', js)
for m in submitdata_matches[:5]:
    print(m[:200])
    print("---")

print("\n=== 查找 nonce ===")
nonce_matches = re.findall(r'nonce[^;]{0,200}', js)
for m in nonce_matches[:5]:
    print(m[:150])
    print("---")

print("\n=== 查找加密函数 ===")
encrypt_matches = re.findall(r'(encrypt|encode|hash|md5|sha)[^;]{0,200}', js, re.IGNORECASE)
for m in encrypt_matches[:10]:
    print(m[:150])
    print("---")
