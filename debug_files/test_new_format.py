"""测试新的提交格式 - 使用 } 分隔符"""
import requests
import random
import re
import time

def get_jqsign(ktimes, jqnonce):
    """生成 jqsign"""
    result = []
    b = ktimes % 10 if ktimes % 10 != 0 else 1
    for char in list(jqnonce):
        f = ord(char) ^ b
        result.append(chr(f))
    return ''.join(result)

# 问卷URL
survey_url = "https://www.wjx.cn/vm/mR4RDSc.aspx"
submit_url = "https://www.wjx.cn/joinnew/processjq.ashx"

# 创建session
session = requests.Session()

# 1. 访问问卷页面
print("1. 访问问卷页面...")
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}
response = session.get(survey_url, headers=headers)
content = response.text
print(f"   状态码: {response.status_code}")

# 2. 从页面提取参数
print("\n2. 提取页面参数...")

# 提取 jqnonce (UUID格式)
jqnonce_match = re.search(r'.{8}-.{4}-.{4}-.{4}-.{12}', content)
jqnonce = jqnonce_match.group() if jqnonce_match else ''
print(f"   jqnonce: {jqnonce}")

# 提取 rndnum
rndnum_match = re.search(r'\d{9,10}\.\d{8}', content)
rndnum = rndnum_match.group() if rndnum_match else ''
print(f"   rndnum: {rndnum}")

# 提取 starttime
starttime_match = re.search(r'\d+?/\d+?/\d+?\s\d+?:\d{2}:\d{2}', content)
starttime = starttime_match.group() if starttime_match else ''
print(f"   starttime: {starttime}")

# 3. 准备提交数据
print("\n3. 准备提交数据...")
ktimes = random.randint(57, 143) + int(random.random() * 286)
jqsign = get_jqsign(ktimes, jqnonce)

# 使用 } 分隔符的答案格式
# 问卷有20题
answers = {
    1: "1",  # 单选
    2: "1",  # 单选
    3: "1000",  # 填空
    4: "父母",  # 填空
    5: "1",  # 单选
    6: "6个月",  # 填空
    7: "500",  # 填空
    8: "1|2",  # 多选
    9: "1",  # 单选
    10: "1",  # 单选
    11: "1",  # 单选
    12: "1",  # 单选
    13: "1",  # 单选
    14: "1|2",  # 多选
    15: "1",  # 单选
    16: "无",  # 填空
    17: "1.7",  # 填空
    18: "3",  # 填空
    19: "2小时",  # 填空
    20: "1",  # 单选
}

submitdata = "}".join([f"{i}${answers[i]}" for i in range(1, 21)])

print(f"   ktimes: {ktimes}")
print(f"   jqsign: {jqsign}")
print(f"   submitdata: {submitdata[:80]}...")

# 4. 构建请求参数
url_params = {
    'shortid': 'mR4RDSc',
    'starttime': starttime,
    'submittype': '1',
    'ktimes': str(ktimes),
    'hlv': '1',
    'rn': rndnum,
    'nw': '1',
    'jwt': '4',
    'jpm': '83',
    't': str(int(time.time() * 1000)),
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

# 5. 提交
print("\n4. 提交问卷...")
print(f"   URL参数: {url_params}")
response = session.post(
    submit_url,
    params=url_params,
    data=post_data,
    headers=submit_headers,
    timeout=30
)

print(f"   状态码: {response.status_code}")
print(f"   响应: {response.text}")

# 判断结果
if 'wjx/join' in response.text:
    print("\n✓✓✓ 提交成功！")
elif response.text == '22':
    print("\n✗ 提交失败: 错误代码 22")
elif '9〒' in response.text:
    print(f"\n✗ 提交失败: {response.text}")
else:
    print(f"\n? 未知响应")
