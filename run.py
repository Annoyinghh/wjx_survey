#!/usr/bin/env python
"""
快速启动脚本
- 本地开发：python run.py
- 云端部署：python run.py --production
"""

import os
import sys
import argparse
from app import app

def main():
    parser = argparse.ArgumentParser(description='启动 WJX Survey 应用')
    parser.add_argument('--production', action='store_true', help='生产环境模式')
    parser.add_argument('--host', default='127.0.0.1', help='绑定主机地址')
    parser.add_argument('--port', type=int, default=5000, help='绑定端口')
    
    args = parser.parse_args()
    
    if args.production:
        print("⚠️  生产环境模式启动")
        print("建议使用 Gunicorn 运行：gunicorn -w 4 -b 0.0.0.0:5000 app:app")
        os.environ['FLASK_ENV'] = 'production'
        app.run(host=args.host, port=args.port, debug=False)
    else:
        print("✅ 本地开发模式启动")
        print(f"访问地址：http://{args.host}:{args.port}")
        app.run(host=args.host, port=args.port, debug=True)

if __name__ == '__main__':
    main()
