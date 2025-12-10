#!/usr/bin/env python3
"""
ChromeDriver 自动安装脚本
使用 webdriver-manager 自动下载和管理 ChromeDriver
"""

import sys
import subprocess

def install_webdriver_manager():
    """安装 webdriver-manager"""
    print("=" * 60)
    print("🚀 ChromeDriver 自动安装工具")
    print("=" * 60)
    
    print("\n📦 正在安装 webdriver-manager...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "webdriver-manager"])
        print("✅ webdriver-manager 安装成功！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 安装失败: {e}")
        return False

def test_chromedriver():
    """测试 ChromeDriver 是否可用"""
    print("\n🧪 测试 ChromeDriver...")
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        
        print("  正在下载 ChromeDriver...")
        driver_path = ChromeDriverManager().install()
        print(f"  ✓ ChromeDriver 路径: {driver_path}")
        
        print("  正在启动浏览器...")
        service = Service(driver_path)
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        
        driver = webdriver.Chrome(service=service, options=options)
        print("  ✓ 浏览器启动成功")
        
        driver.quit()
        print("✅ ChromeDriver 测试通过！")
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("安装步骤:")
    print("=" * 60)
    
    # 安装 webdriver-manager
    if not install_webdriver_manager():
        print("\n❌ 安装失败，请手动执行:")
        print("   pip install webdriver-manager")
        sys.exit(1)
    
    # 测试
    if not test_chromedriver():
        print("\n⚠️  测试失败，但 webdriver-manager 已安装")
        print("   首次运行时会自动下载 ChromeDriver")
        print("   请确保网络连接正常")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ 安装完成！")
    print("=" * 60)
    print("\n现在可以运行问卷填写程序了:")
    print("   python app.py")

if __name__ == '__main__':
    main()
