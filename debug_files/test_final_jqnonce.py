"""测试最终的安全 jqnonce 生成"""
import random

def dataenc(e, ktimes):
    t = ktimes % 10
    if t == 0:
        t = 1
    result = []
    for char in e:
        n = ord(char) ^ t
        result.append(chr(n))
    return ''.join(result)

# 生成20个测试用例
chars = '01'  # 只使用 0 和 1

print("测试最终的安全 jqnonce 生成 (只使用 0 和 1):")
print()

all_safe = True
for i in range(20):
    jqnonce = ''.join(random.choice(chars) for _ in range(8))
    ktimes = random.randint(60, 180)
    t = ktimes % 10
    if t == 0:
        t = 1
    jqsign = dataenc(jqnonce, ktimes)
    
    # 检查是否有特殊字符
    has_special = any(not c.isalnum() for c in jqsign)
    
    if has_special:
        all_safe = False
        print(f"✗ 测试 {i+1}: jqnonce={jqnonce}, ktimes={ktimes}, t={t}, jqsign={jqsign} - 有特殊字符!")
    else:
        print(f"✓ 测试 {i+1}: jqnonce={jqnonce}, ktimes={ktimes}, t={t}, jqsign={jqsign}")

print()
if all_safe:
    print("✓✓✓ 所有测试通过！jqsign 都是安全的字母数字字符")
else:
    print("✗✗✗ 有测试失败")
