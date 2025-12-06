"""测试安全的 jqnonce 生成"""
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

# 生成10个测试用例
chars = '0123456789bcdef'  # 不包括 'a'

print("测试安全的 jqnonce 生成:")
print()

for i in range(10):
    jqnonce = ''.join(random.choice(chars) for _ in range(8))
    ktimes = random.randint(60, 180)
    t = ktimes % 10
    if t == 0:
        t = 1
    jqsign = dataenc(jqnonce, ktimes)
    
    # 检查是否有特殊字符
    has_special = any(not c.isalnum() for c in jqsign)
    
    print(f"测试 {i+1}:")
    print(f"  jqnonce: {jqnonce}, ktimes: {ktimes}, t: {t}")
    print(f"  jqsign:  {jqsign}")
    print(f"  状态: {'✗ 有特殊字符' if has_special else '✓ 安全'}")
    print()
