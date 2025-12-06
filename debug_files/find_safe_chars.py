"""找出对所有 t 值(1-9)都安全的字符"""

# 测试所有十六进制字符
hex_chars = '0123456789abcdef'

print("分析每个字符对不同 t 值的 XOR 结果:")
print()

safe_chars_all_t = []

for char in hex_chars:
    print(f"字符 '{char}' (ASCII {ord(char)}):")
    is_safe_for_all = True
    
    for t in range(1, 10):
        xor_result = chr(ord(char) ^ t)
        is_alnum = xor_result.isalnum()
        status = "✓" if is_alnum else "✗"
        
        print(f"  t={t}: XOR = '{xor_result}' (ASCII {ord(xor_result)}) {status}")
        
        if not is_alnum:
            is_safe_for_all = False
    
    if is_safe_for_all:
        safe_chars_all_t.append(char)
        print(f"  ✓✓✓ 对所有 t 值都安全")
    
    print()

print("=" * 60)
print(f"对所有 t 值(1-9)都安全的字符: {' '.join(safe_chars_all_t)}")
print(f"安全字符集: {''.join(safe_chars_all_t)}")
