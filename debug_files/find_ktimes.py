"""查找 ktimes 的定义和使用"""
import re

js = open('jqmobo2.js', 'r', encoding='utf-8').read()

print("=== 查找 ktimes 定义 ===")
ktimes_matches = re.findall(r'ktimes\s*[=:][^;]{0,100}', js)
for m in ktimes_matches[:10]:
    print(m)
    print("---")

print("\n=== 查找 var ktimes ===")
var_ktimes = re.findall(r'var\s+ktimes[^;]*', js)
for m in var_ktimes[:5]:
    print(m)

print("\n=== 查找 starttime ===")
starttime_matches = re.findall(r'starttime\s*[=:][^;]{0,100}', js)
for m in starttime_matches[:5]:
    print(m)
    print("---")
