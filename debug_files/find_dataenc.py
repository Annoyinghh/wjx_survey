"""查找 dataenc 函数的完整实现"""
import re

js = open('jqmobo2.js', 'r', encoding='utf-8').read()

# 查找 dataenc 函数定义
print("=== 查找 dataenc 函数 ===")

# 方法1: function dataenc
match = re.search(r'function\s+dataenc\s*\([^)]*\)\s*\{[^}]+\}', js)
if match:
    print("方法1:", match.group(0)[:500])

# 方法2: dataenc = function
match = re.search(r'dataenc\s*=\s*function\s*\([^)]*\)\s*\{[^}]+\}', js)
if match:
    print("方法2:", match.group(0)[:500])

# 方法3: 查找包含 dataenc 的更大上下文
# 找到 dataenc(e) 的定义
match = re.search(r'dataenc\(e\)\{[^}]+\}', js)
if match:
    print("方法3:", match.group(0)[:500])

# 方法4: 查找 ktimes%10 相关代码（从之前的输出看到）
match = re.search(r'dataenc[^{]*\{[^}]*ktimes[^}]*\}', js)
if match:
    print("方法4:", match.group(0)[:500])

# 方法5: 更宽松的搜索
print("\n=== 搜索 ktimes%10 上下文 ===")
idx = js.find('ktimes%10')
if idx > 0:
    print(js[idx-200:idx+300])

# 方法6: 查找完整的 dataenc 函数（可能跨多行）
print("\n=== 查找完整 dataenc ===")
# 找到 dataenc(e){ 的位置
idx = js.find('dataenc(e){')
if idx > 0:
    # 找到匹配的 }
    depth = 0
    start = idx
    for i in range(idx, min(idx+1000, len(js))):
        if js[i] == '{':
            depth += 1
        elif js[i] == '}':
            depth -= 1
            if depth == 0:
                print(js[start:i+1])
                break
