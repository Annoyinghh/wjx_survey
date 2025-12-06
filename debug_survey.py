#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
问卷填写调试脚本
用于诊断问卷填写问题
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def debug_survey(url):
    """调试问卷"""
    print(f"开始调试问卷: {url}")
    
    chrome_options = Options()
    # 不使用无头模式，便于观察
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        driver.get(url)
        time.sleep(3)
        
        print("\n========== 页面信息 ==========")
        print(f"当前URL: {driver.current_url}")
        print(f"页面标题: {driver.title}")
        
        # 查找所有问题
        print("\n========== 问题信息 ==========")
        questions = driver.find_elements(By.CLASS_NAME, 'field')
        print(f"找到 {len(questions)} 个问题")
        
        for idx, question in enumerate(questions, 1):
            try:
                question_text = question.find_element(By.CLASS_NAME, 'field-label').text
                print(f"第{idx}题: {question_text}")
            except:
                print(f"第{idx}题: 无法获取标题")
        
        # 查找下一页按钮
        print("\n========== 下一页按钮信息 ==========")
        selectors = [
            (By.ID, 'ctlNext'),
            (By.XPATH, '//a[text()="下一页"]'),
            (By.XPATH, '//button[text()="下一页"]'),
            (By.XPATH, '//input[@value="下一页"]'),
            (By.XPATH, '//a[contains(text(), "下一页")]'),
            (By.XPATH, '//button[contains(text(), "下一页")]'),
        ]
        
        for selector in selectors:
            try:
                buttons = driver.find_elements(*selector)
                if buttons:
                    print(f"\n选择器 {selector}:")
                    for i, button in enumerate(buttons):
                        print(f"  按钮{i+1}:")
                        print(f"    文本: {button.text}")
                        print(f"    值: {button.get_attribute('value')}")
                        print(f"    ID: {button.get_attribute('id')}")
                        print(f"    类名: {button.get_attribute('class')}")
                        print(f"    可见: {button.is_displayed()}")
                        print(f"    可用: {button.is_enabled()}")
            except:
                pass
        
        # 查找提交按钮
        print("\n========== 提交按钮信息 ==========")
        submit_selectors = [
            (By.ID, 'ctlNext'),
            (By.XPATH, '//a[text()="提交"]'),
            (By.XPATH, '//button[text()="提交"]'),
            (By.XPATH, '//input[@value="提交"]'),
            (By.XPATH, '//a[contains(text(), "提交")]'),
            (By.XPATH, '//button[contains(text(), "提交")]'),
        ]
        
        for selector in submit_selectors:
            try:
                buttons = driver.find_elements(*selector)
                if buttons:
                    print(f"\n选择器 {selector}:")
                    for i, button in enumerate(buttons):
                        print(f"  按钮{i+1}:")
                        print(f"    文本: {button.text}")
                        print(f"    值: {button.get_attribute('value')}")
                        print(f"    ID: {button.get_attribute('id')}")
                        print(f"    类名: {button.get_attribute('class')}")
                        print(f"    可见: {button.is_displayed()}")
                        print(f"    可用: {button.is_enabled()}")
            except:
                pass
        
        # 保存页面源代码用于分析
        print("\n========== 保存页面源代码 ==========")
        with open('debug_page_source.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("页面源代码已保存到 debug_page_source.html")
        
        print("\n========== 调试完成 ==========")
        print("请查看浏览器窗口和debug_page_source.html文件")
        print("按Enter键关闭浏览器...")
        input()
        
    finally:
        driver.quit()

if __name__ == '__main__':
    # 替换为实际的问卷URL
    url = input("请输入问卷URL: ").strip()
    if url:
        debug_survey(url)
    else:
        print("URL不能为空")
