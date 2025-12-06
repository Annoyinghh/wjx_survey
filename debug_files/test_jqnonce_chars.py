"""测试不同 jqnonce 生成的 jqsign 字符"""

def dataenc(e, ktimes):
    t = ktimes % 10
    if t == 0:
        t = 1
    result = []
    for char in e:
        n = ord(char) ^ t
        result.append(chr(n))
    return ''.join(result)

# 测试不同的 jqnonce
test_cases = [
    ('abcdef01', 100),  # 只用字母和0-1
    ('23456789', 100),  # 只用数字2-9
    ('aaaaaaaa', 100),  # 全是a
    ('01234567', 100),  # 数字0-7
]

print("测试 jqnonce 生成的 jqsign 字符:")
print()

for jqnonce, ktimes in test_cases:
    t = ktimes % 10
    if t == 0:
        t = 1
    jqsign = dataenc(jqnonce, ktimes)
    
    # 检查是否有特殊字符
    special_chars = []
    for i, c in enumerate(jqsign):
        if not c.isalnum():
            special_chars.append(f"位置{i}: '{c}' (ASCII {ord(c)})")
    
    print(f"jqnonce: {jqnonce}, ktimes: {ktimes}, t: {t}")
    print(f"jqsign:  {jqsign}")
    if special_chars:
        print(f"特殊字符: {', '.join(special_chars)}")
    else:
        print("✓ 无特殊字符")
    print()

# 找出哪些字符 XOR 1 后是字母数字
print("=" * 50)
print("哪些字符 XOR 1 后仍是字母数字:")
safe_chars = []
for c in '0123456789abcdef':
    xor_result = chr(ord(c) ^ 1)
    if xor_result.isalnum():
        safe_chars.append(c)
        print(f"  '{c}' (ASCII {ord(c)}) XOR 1 = '{xor_result}' (ASCII {ord(xor_result)})")

print(f"\n安全字符集 (XOR 1): {' '.join(safe_chars)}")
