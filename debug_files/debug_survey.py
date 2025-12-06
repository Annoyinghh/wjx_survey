"""调试脚本：获取问卷页面HTML并查找关键参数"""
import requests
import re

url = "https://v.wjx.cn/vm/mR4RDSc.aspx"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

response = requests.get(url, headers=headers, timeout=30)
response.encoding = 'utf-8'
html = response.text

# 保存完整HTML
with open('survey_page_debug.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f"✓ 页面已保存到 survey_page_debug.html ({len(html)} 字节)")

# 查找所有可能的ID
print("\n=== 查找数字ID ===")
patterns = [
    (r'activityId["\s:=]+(\d+)', 'activityId'),
    (r'activity["\s:=]+(\d+)', 'activity'),
    (r'curID["\s:=]+["\']?(\d+)', 'curID'),
    (r'shortid["\s:=]+["\']?([a-zA-Z0-9]+)', 'shortid'),
    (r'/jq/(\d+)\.aspx', 'jq路径'),
    (r'dataId["\s:=]+(\d+)', 'dataId'),
    (r'"id"\s*:\s*(\d+)', 'JSON id'),
    (r'surveyId["\s:=]+(\d+)', 'surveyId'),
]

for pattern, name in patterns:
    matches = re.findall(pattern, html, re.IGNORECASE)
    if matches:
        print(f"  {name}: {matches[:5]}")  # 只显示前5个

# 查找script标签中的关键变量
print("\n=== 查找JavaScript变量 ===")
script_patterns = [
    r'var\s+(\w+)\s*=\s*(\d{5,})',  # var xxx = 123456
    r'(\w+)\s*:\s*(\d{5,})',  # xxx: 123456
]

for pattern in script_patterns:
    matches = re.findall(pattern, html)
    for name, value in matches[:10]:
        if len(value) >= 5:  # 只显示5位以上的数字
            print(f"  {name} = {value}")

# 查找form action
print("\n=== 查找表单提交地址 ===")
form_matches = re.findall(r'action=["\']([^"\']+)["\']', html, re.IGNORECASE)
for m in form_matches:
    print(f"  action: {m}")

# 查找隐藏字段
print("\n=== 查找隐藏字段 ===")
hidden_matches = re.findall(r'<input[^>]*type=["\']hidden["\'][^>]*name=["\']([^"\']+)["\'][^>]*value=["\']([^"\']*)["\']', html, re.IGNORECASE)
for name, value in hidden_matches:
    print(f"  {name}: {value[:50] if len(value) > 50 else value}")

print("\n完成！请检查 survey_page_debug.html 文件")
