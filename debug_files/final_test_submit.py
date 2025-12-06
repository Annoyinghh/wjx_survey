"""最终测试问卷提交 - 使用安全的 jqnonce"""
import requests
import random
import time

def dataenc(e, ktimes):
    t = ktimes % 10
    if t == 0:
        t = 1
    result = []
    for char in e:
        n = ord(char) ^ t
        result.append(chr(n))
    return ''.join(result)

# 问卷URL
survey_url = "https://v.wjx.cn/vm/mR4RDSc.aspx"
submit_url = "https://www.wjx.cn/joinnew/processjq.ashx"

# 创建session
session = requests.Session()

# 1. 先访问问卷页面获取cookies
print("1. 访问问卷页面...")
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}
response = session.get(survey_url, headers=headers)
print(f"   状态码: {response.status_code}")

# 2. 准备提交数据
print("\n2. 准备提交数据...")
ktimes = random.randint(60, 180)
current_ts = int(time.time() * 1000)
starttime = str(current_ts - ktimes * 1000)

# 生成 jqnonce (8位，只使用 0 和 1)
chars = '01'
jqnonce = ''.join(random.choice(chars) for _ in range(8))
jqsign = dataenc(jqnonce, ktimes)

# 最简单的答案：所有题都选第1个选项
submitdata = ";".join([f"{i}$1" for i in range(1, 21)])

print(f"   ktimes: {ktimes}")
print(f"   starttime: {starttime}")
print(f"   jqnonce: {jqnonce}")
print(f"   jqsign: {jqsign}")
print(f"   jqsign 是否安全: {all(c.isalnum() for c in jqsign)}")
print(f"   submitdata前50字符: {submitdata[:50]}...")

# 3. 构建请求
url_params = {
    'starttime': starttime,
    'shortid': 'mR4RDSc',
    'ktimes': str(ktimes),
    'jqnonce': jqnonce,
    'jqsign': jqsign,
}

post_data = {
    'submitdata': submitdata
}

submit_headers = {
    'Host': 'www.wjx.cn',
    'Origin': 'https://www.wjx.cn',
    'Referer': 'https://www.wjx.cn/vm/mR4RDSc.aspx',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'X-Requested-With': 'XMLHttpRequest',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

# 4. 提交
print("\n3. 提交问卷...")
response = session.post(
    submit_url,
    params=url_params,
    data=post_data,
    headers=submit_headers,
    timeout=30
)

print(f"   状态码: {response.status_code}")
print(f"   响应: {response.text}")

# 5. 判断结果
if 'wjx/join' in response.text:
    print("\n✓✓✓ 提交成功！")
elif response.text == '22':
    print("\n✗ 提交失败: 错误代码 22")
elif '9〒' in response.text:
    print(f"\n✗ 提交失败: {response.text}")
else:
    print(f"\n? 未知响应: {response.text[:200]}")
