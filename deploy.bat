@echo off
REM 一键部署脚本 - Windows
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ==========================================
echo   问卷星智能填写系统 - 一键部署
echo ==========================================
echo.

REM 检查 Docker
echo 检查 Docker 环境...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Docker 未安装
    echo 请先安装 Docker Desktop: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo [成功] Docker 已安装

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Docker Compose 未安装
    pause
    exit /b 1
)
echo [成功] Docker Compose 已安装

REM 检查端口
echo.
echo 检查端口占用...
netstat -ano | findstr ":5000" >nul 2>&1
if not errorlevel 1 (
    echo [警告] 端口 5000 已被占用
    set /p choice="是否停止占用进程并继续? (Y/N): "
    if /i "!choice!"=="Y" (
        for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000"') do (
            taskkill /F /PID %%a >nul 2>&1
        )
        echo [成功] 已释放端口 5000
    ) else (
        echo 部署已取消
        pause
        exit /b 1
    )
) else (
    echo [成功] 端口 5000 可用
)

REM 配置环境变量
echo.
echo 配置环境变量...
if not exist .env (
    if exist .env.docker (
        copy .env.docker .env >nul
        echo [成功] 已创建 .env 文件
    ) else (
        echo [警告] 未找到 .env.docker 模板
    )
) else (
    echo [成功] .env 文件已存在
)

REM 生成随机 SECRET_KEY
if exist .env (
    set "chars=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    set "secret_key="
    for /l %%i in (1,1,64) do (
        set /a "rand=!random! %% 62"
        for %%j in (!rand!) do set "secret_key=!secret_key!!chars:~%%j,1!"
    )
    powershell -Command "(Get-Content .env) -replace 'your-random-secret-key-change-this-in-production', '!secret_key!' | Set-Content .env"
    echo [成功] 已生成随机 SECRET_KEY
)

REM 构建镜像
echo.
echo 构建 Docker 镜像...
docker-compose build
if errorlevel 1 (
    echo [错误] 镜像构建失败
    pause
    exit /b 1
)
echo [成功] 镜像构建完成

REM 启动服务
echo.
echo 启动服务...
docker-compose up -d
if errorlevel 1 (
    echo [错误] 服务启动失败
    pause
    exit /b 1
)
echo [成功] 服务启动成功

REM 等待服务就绪
echo.
echo 等待服务就绪...
timeout /t 10 /nobreak >nul

REM 显示信息
echo.
echo ==========================================
echo 部署完成！
echo ==========================================
echo.
echo 访问地址: http://localhost:5000
echo.
echo 默认管理员账号:
echo   用户名: Bear
echo   密码: xzx123456
echo.
echo [警告] 请立即修改默认密码！
echo.
echo 常用命令:
echo   查看日志: docker-compose logs -f
echo   停止服务: docker-compose stop
echo   启动服务: docker-compose start
echo   重启服务: docker-compose restart
echo   删除服务: docker-compose down
echo.
echo ==========================================
echo.
pause
