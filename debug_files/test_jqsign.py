"""测试 jqsign 生成"""

def dataenc(jqnonce, ktimes):
    t = int(ktimes) % 10
    if t == 0:
        t = 1
    result = []
    for char in jqnonce:
        n = ord(char) ^ t
        result.append(chr(n))
    return ''.join(result)

# 测试用例
print("Test 1: 8位十六进制 jqnonce")
jqnonce1 = '70a641ec'
ktimes1 = 106
t1 = ktimes1 % 10
jqsign1 = dataenc(jqnonce1, ktimes1)
print(f"jqnonce: {jqnonce1}")
print(f"ktimes: {ktimes1}, t: {t1}")
print(f"jqsign: {jqsign1}")
print(f"jqsign length: {len(jqsign1)}")
print()

print("Test 2: 8位十六进制 jqnonce")
jqnonce2 = 'abcd1234'
ktimes2 = 151
t2 = ktimes2 % 10
jqsign2 = dataenc(jqnonce2, ktimes2)
print(f"jqnonce: {jqnonce2}")
print(f"ktimes: {ktimes2}, t: {t2}")
print(f"jqsign: {jqsign2}")
print(f"jqsign length: {len(jqsign2)}")
print()

print("Test 3: UUID 格式 jqnonce (错误示例)")
jqnonce3 = '8b2fe274-d6a7-4ce3-8029-697bc94b6035'
ktimes3 = 151
t3 = ktimes3 % 10
jqsign3 = dataenc(jqnonce3, ktimes3)
print(f"jqnonce: {jqnonce3}")
print(f"ktimes: {ktimes3}, t: {t3}")
print(f"jqsign: {jqsign3}")
print(f"jqsign length: {len(jqsign3)}")
print(f"包含特殊字符: {any(c in jqsign3 for c in ',`')}")
