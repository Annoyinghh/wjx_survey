"""测试正确的答案格式"""
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

# 1. 先访问问卷页面
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

# 生成 jqnonce
chars = '01'
jqnonce = ''.join(random.choice(chars) for _ in range(8))
jqsign = dataenc(jqnonce, ktimes)

# 正确的答案格式
# 根据问卷结构：
# 1-2: 单选
# 3-4: 填空
# 5-7: 单选/填空
# 8: 多选（至少2项）
# 9-15: 单选
# 16-19: 填空
# 20: 单选

answers = {
    1: "1",  # 单选
    2: "1",  # 单选
    3: "1000",  # 填空 - 生活费
    4: "父母",  # 填空 - 来源
    5: "1",  # 单选
    6: "6个月",  # 填空 - 时长
    7: "500",  # 填空 - 花费
    8: "1|2",  # 多选 - 至少2项
    9: "1",  # 单选
    10: "1",  # 单选
    11: "1",  # 单选
    12: "1",  # 单选
    13: "1",  # 单选
    14: "1|2",  # 多选 - 至少2项
    15: "1",  # 单选
    16: "无",  # 填空
    17: "1.7",  # 填空 - 身高
    18: "3",  # 填空 - 次数
    19: "2小时",  # 填空 - 时间
    20: "1",  # 单选
}

submitdata = ";".join([f"{i}${answers[i]}" for i in range(1, 21)])

print(f"   ktimes: {ktimes}")
print(f"   jqnonce: {jqnonce}")
print(f"   jqsign: {jqsign}")
print(f"   submitdata: {submitdata[:100]}...")

# 3. 提交
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

# 判断结果
if 'wjx/join' in response.text:
    print("\n✓✓✓ 提交成功！")
elif response.text == '22':
    print("\n✗ 提交失败: 错误代码 22")
elif '9〒' in response.text:
    print(f"\n✗ 提交失败: {response.text}")
else:
    print(f"\n? 未知响应")
