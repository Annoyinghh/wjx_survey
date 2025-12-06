#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
from survey_filler import SurveyFiller

def test_failure_screenshots():
    """测试失败截图功能"""
    print("开始测试失败截图功能...")
    
    # 创建问卷填写器
    filler = SurveyFiller()
    
    try:
        # 测试URL（这里使用一个可能失败的URL来测试截图功能）
        test_url = "https://www.wjx.cn/vm/example.aspx"  # 示例URL，实际使用时请替换
        
        print(f"测试URL: {test_url}")
        
        # 尝试填写问卷
        result = filler.fill_survey(test_url)
        
        print(f"填写结果: {'成功' if result else '失败'}")
        
        # 检查是否有失败截图
        failure_dir = "failure_screenshots"
        if os.path.exists(failure_dir):
            screenshots = [f for f in os.listdir(failure_dir) if f.endswith('.png')]
            if screenshots:
                print(f"\n找到 {len(screenshots)} 个失败截图:")
                for screenshot in screenshots:
                    print(f"  - {screenshot}")
                    
                    # 读取对应的错误信息文件
                    error_file = screenshot.replace('.png', '.txt')
                    error_path = os.path.join(failure_dir, error_file)
                    if os.path.exists(error_path):
                        with open(error_path, 'r', encoding='utf-8') as f:
                            error_info = f.read()
                            print(f"    错误信息: {error_info.strip()}")
            else:
                print("未找到失败截图")
        else:
            print("未找到失败截图目录")
            
    except Exception as e:
        print(f"测试过程中出错: {e}")
    finally:
        filler.close()

if __name__ == "__main__":
    test_failure_screenshots() 