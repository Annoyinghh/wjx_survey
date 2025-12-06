#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
from datetime import datetime

def view_failures():
    """查看失败截图和错误信息"""
    print("🔍 查看失败原因分析")
    print("=" * 50)
    
    failure_dir = "failure_screenshots"
    
    if not os.path.exists(failure_dir):
        print("❌ 未找到失败截图目录")
        return
    
    # 获取所有截图文件
    screenshots = glob.glob(os.path.join(failure_dir, "*.png"))
    
    if not screenshots:
        print("❌ 未找到任何失败截图")
        return
    
    print(f"📸 找到 {len(screenshots)} 个失败截图:")
    print()
    
    # 按时间排序
    screenshots.sort(key=os.path.getmtime)
    
    for i, screenshot in enumerate(screenshots, 1):
        filename = os.path.basename(screenshot)
        error_file = screenshot.replace('.png', '.txt')
        
        # 获取文件修改时间
        mtime = os.path.getmtime(screenshot)
        time_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"📋 失败 {i}: {filename}")
        print(f"   时间: {time_str}")
        
        # 读取错误信息
        if os.path.exists(error_file):
            try:
                with open(error_file, 'r', encoding='utf-8') as f:
                    error_info = f.read().strip()
                    print(f"   错误: {error_info}")
            except Exception as e:
                print(f"   读取错误信息失败: {e}")
        else:
            print("   无错误信息文件")
        
        print()
    
    # 统计错误类型
    print("📊 错误类型统计:")
    error_types = {}
    for screenshot in screenshots:
        filename = os.path.basename(screenshot)
        # 从文件名提取错误类型
        parts = filename.replace('.png', '').split('_')
        if len(parts) >= 2:
            error_type = parts[1]
            error_types[error_type] = error_types.get(error_type, 0) + 1
    
    for error_type, count in sorted(error_types.items()):
        print(f"   {error_type}: {count} 次")
    
    print()
    print("💡 建议:")
    print("1. 查看截图文件了解具体失败原因")
    print("2. 根据错误类型调整填写策略")
    print("3. 检查网络连接和问卷URL有效性")
    print("4. 考虑增加重试机制")

def analyze_failure_patterns():
    """分析失败模式"""
    print("\n🔬 失败模式分析")
    print("=" * 30)
    
    failure_dir = "failure_screenshots"
    if not os.path.exists(failure_dir):
        return
    
    screenshots = glob.glob(os.path.join(failure_dir, "*.png"))
    
    # 分析常见错误类型
    error_patterns = {
        'submit': '提交按钮相关错误',
        'question': '问题处理错误',
        'single_choice': '单选题错误',
        'multi_choice': '多选题错误',
        'fill_blank': '填空题错误',
        'no_questions_found': '未找到问题',
        'general_error': '一般错误'
    }
    
    pattern_counts = {}
    for screenshot in screenshots:
        filename = os.path.basename(screenshot)
        for pattern, description in error_patterns.items():
            if pattern in filename:
                pattern_counts[description] = pattern_counts.get(description, 0) + 1
                break
    
    if pattern_counts:
        print("常见失败原因:")
        for description, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {description}: {count} 次")
    else:
        print("无常见失败模式")

if __name__ == "__main__":
    view_failures()
    analyze_failure_patterns() 