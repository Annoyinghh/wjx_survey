"""测试提交格式"""
import random
import time

# 模拟参考代码的格式
def dataenc(e, ktimes):
    t = ktimes % 10
    if t == 0:
        t = 1
    result = []
    for char in e:
        n = ord(char) ^ t
        result.append(chr(n))
    return ''.join(result)

# 生成测试数据
ktimes = random.randint(60, 180)
current_ts = int(time.time() * 1000)
starttime = str(current_ts - ktimes * 1000)

# 生成 jqnonce (8位十六进制)
import random
chars = '0123456789abcdef'
jqnonce = ''.join(random.choice(chars) for _ in range(8))

# 生成 jqsign
jqsign = dataenc(jqnonce, ktimes)

# 构建答案数据
submitdata = "1$2;2$1;3$测试;4$测试"

print("=== 提交参数 ===")
print(f"ktimes: {ktimes}")
print(f"starttime: {starttime}")
print(f"jqnonce: {jqnonce}")
print(f"jqsign: {jqsign}")
print(f"jqsign length: {len(jqsign)}")
print(f"submitdata: {submitdata}")
print()

print("=== URL 参数 ===")
url_params = {
    'starttime': starttime,
    'shortid': 'mR4RDSc',
    'ktimes': str(ktimes),
    'jqnonce': jqnonce,
    'jqsign': jqsign,
}
for k, v in url_params.items():
    print(f"{k}: {v}")

print()
print("=== POST 数据 ===")
print(f"submitdata: {submitdata}")
