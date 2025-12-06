#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import app

if __name__ == "__main__":
    print("=" * 50)
    print("问卷星自动填写系统")
    print("=" * 50)
    print("访问地址: http://localhost:5000")
    print("按 Ctrl+C 停止服务器")
    print("-" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000) 