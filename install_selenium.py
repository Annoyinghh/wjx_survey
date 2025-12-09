#!/usr/bin/env python
"""
安装 Selenium + undetected-chromedriver
"""
import subprocess
import sys

print("正在安装 Selenium...")
subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium"])

print("正在安装 undetected-chromedriver...")
subprocess.check_call([sys.executable, "-m", "pip", "install", "undetected-chromedriver"])

print("""
✓ 安装完成！

注意：undetected-chromedriver 会自动下载匹配的 ChromeDriver。
请确保已安装 Google Chrome 浏览器。

如果遇到问题，请检查：
1. Chrome 浏览器是否已安装
2. Chrome 版本是否过旧（建议 100+）
""")
