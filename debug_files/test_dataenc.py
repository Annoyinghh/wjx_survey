"""测试 dataenc 函数"""

def dataenc(jqnonce, ktimes):
    """问卷星的 dataenc 签名算法"""
    t = int(ktimes) % 10
    if t == 0:
        t = 1
    
    result = []
    for char in jqnonce:
        n = ord(char) ^ t
        result.append(chr(n))
    
    return ''.join(result)

# 测试用例
test_cases = [
    ("70a641ec", 106),  # 从日志中的例子
    ("abcd1234", 100),  # ktimes%10=0, 应该用1
    ("test", 5),
]

for jqnonce, ktimes in test_cases:
    t = ktimes % 10
    if t == 0:
        t = 1
    jqsign = dataenc(jqnonce, ktimes)
    print(f"jqnonce: {jqnonce}, ktimes: {ktimes}, t: {t}")
    print(f"jqsign: {jqsign}")
    print(f"jqsign bytes: {[ord(c) for c in jqsign]}")
    print()
