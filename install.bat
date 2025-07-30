@echo off
chcp 65001 >nul
echo.
echo ===============================================
echo     🚀 JOVAY FUCKER BOT INSTALLER
echo ===============================================
echo.

:: Проверяем наличие Python
echo 🔍 Проверка Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python не найден!
    echo 📥 Скачайте Python с https://www.python.org/downloads/
    echo ⚠️  Убедитесь, что отметили "Add Python to PATH" при установке
    pause
    exit /b 1
)

python --version
echo ✅ Python найден!
echo.

:: Проверяем наличие pip
echo 🔍 Проверка pip...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip не найден!
    echo 📥 Устанавливаем pip...
    python -m ensurepip --upgrade
)

echo ✅ pip готов!
echo.

:: Создаем виртуальную среду
echo 🏗️ Создание виртуальной среды...
if exist "venv" (
    echo ⚠️  Виртуальная среда уже существует
    set /p choice="Пересоздать? (y/n): "
    if /i "!choice!"=="y" (
        echo 🗑️ Удаляем старую среду...
        rmdir /s /q venv
        echo 🏗️ Создаем новую виртуальную среду...
        python -m venv venv
    )
) else (
    python -m venv venv
)

if not exist "venv" (
    echo ❌ Ошибка создания виртуальной среды!
    pause
    exit /b 1
)

echo ✅ Виртуальная среда создана!
echo.

:: Активируем виртуальную среду
echo 🔌 Активация виртуальной среды...
call venv\Scripts\activate.bat

:: Обновляем pip и устанавливаем основные инструменты
echo 📦 Обновление pip и установка инструментов...
python -m pip install --upgrade pip
python -m pip install --upgrade setuptools wheel

:: Устанавливаем зависимости с предкомпилированными wheel'ами
echo 📦 Установка зависимостей (используем предкомпилированные пакеты)...
echo.

:: Устанавливаем основные зависимости с --only-binary для избежания компиляции
echo 📦 Установка requests...
pip install --only-binary=all requests==2.31.0
if %errorlevel% neq 0 (
    echo ⚠️ Пробуем без ограничения версии...
    pip install requests
)

echo 📦 Установка eth-account...
pip install --only-binary=all eth-account==0.10.0
if %errorlevel% neq 0 (
    echo ⚠️ Пробуем установить eth-account без ограничения версии...
    pip install eth-account
)

echo 📦 Установка web3 (может занять время)...
:: Сначала пробуем установить с предкомпилированными пакетами
pip install --only-binary=all web3==6.15.1
if %errorlevel% neq 0 (
    echo ⚠️ Ошибка с предкомпилированными пакетами
    echo 🔧 Пробуем альтернативный способ...
    
    :: Устанавливаем более старую версию web3 которая не требует компиляции
    pip install web3==6.0.0
    if %errorlevel% neq 0 (
        echo 🔧 Пробуем установить минимальную версию web3...
        pip install web3==5.31.4
        if %errorlevel% neq 0 (
            echo ❌ Критическая ошибка установки web3!
            echo.
            echo 🛠️ РЕШЕНИЕ ПРОБЛЕМЫ:
            echo.
            echo 1. Установите Microsoft C++ Build Tools:
            echo    https://visualstudio.microsoft.com/visual-cpp-build-tools/
            echo.
            echo 2. Или установите Visual Studio Community с C++ поддержкой:
            echo    https://visualstudio.microsoft.com/vs/community/
            echo.
            echo 3. После установки перезапустите install.bat
            echo.
            pause
            exit /b 1
        )
    )
)

echo 📦 Установка py-solc-x...
pip install --only-binary=all py-solc-x==2.0.2
if %errorlevel% neq 0 (
    echo ⚠️ Пробуем более старую версию py-solc-x...
    pip install py-solc-x==1.12.2
    if %errorlevel% neq 0 (
        echo ⚠️ Устанавливаем py-solc-x без ограничения версии...
        pip install py-solc-x
    )
)

:: Дополнительные полезные зависимости (опционально)
echo 📦 Установка дополнительных пакетов...
pip install --only-binary=all colorama tqdm
if %errorlevel% neq 0 (
    pip install colorama tqdm
)

echo.
echo ✅ Зависимости установлены!
echo.

:: Создаем упрощенную версию requirements.txt без проблемных пакетов
echo 📝 Создание совместимого requirements.txt...
(
    echo # Совместимые зависимости для Jovay Network Automation
    echo requests^>=2.28.0
    echo eth-account^>=0.8.0
    echo py-solc-x^>=1.12.0
    echo colorama^>=0.4.0
    echo tqdm^>=4.60.0
    echo.
    echo # Web3 - используем совместимую версию
    echo web3^>=5.31.0,^<7.0.0
) > requirements_compatible.txt

echo ✅ Создан совместимый requirements.txt
echo.

:: Создаем файлы конфигурации
echo 📝 Создание файлов конфигурации...

:: Создаем private_keys.txt если его нет
if not exist "private_keys.txt" (
    (
        echo # Добавьте ваши приватные ключи, каждый с новой строки
        echo # Пример:
        echo # 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
        echo # 0xfedcba0987654321fedcba0987654321fedcba0987654321fedcba0987654321
        echo.
        echo # ⚠️ ВАЖНО: Никогда не делитесь своими приватными ключами!
        echo # 🔒 Используйте только тестовые кошельки
    ) > private_keys.txt
    echo ✅ Создан файл private_keys.txt
) else (
    echo ⚠️  Файл private_keys.txt уже существует
)

:: Создаем proxies.txt если его нет
if not exist "proxies.txt" (
    (
        echo # Добавьте прокси в формате host:port или host:port:username:password
        echo # Примеры:
        echo # 192.168.1.1:8080
        echo # proxy.example.com:3128:user:pass
        echo # socks5://127.0.0.1:1080
        echo.
        echo # Для работы без прокси просто оставьте файл пустым
        echo # или отключите использование прокси в настройках
    ) > proxies.txt
    echo ✅ Создан файл proxies.txt
) else (
    echo ⚠️  Файл proxies.txt уже существует
)

:: Создаем start.bat
(
    echo @echo off
    echo chcp 65001 ^>nul
    echo echo.
    echo echo 🚀 Запуск Jovay Network Automation...
    echo echo.
    echo call venv\Scripts\activate.bat
    echo python run.py
    echo pause
) > start.bat

echo ✅ Создан файл start.bat для запуска
echo.

:: Создаем fix_compilation.bat для решения проблем с компиляцией
(
    echo @echo off
    echo echo 🔧 Установка Microsoft C++ Build Tools...
    echo echo.
    echo echo Этот скрипт поможет установить необходимые инструменты
    echo echo для компиляции Python пакетов на Windows
    echo echo.
    echo echo 1. Скачивается установщик Build Tools
    echo echo 2. Запускается автоматическая установка
    echo echo.
    echo pause
    echo.
    echo :: Скачиваем и устанавливаем Build Tools
    echo powershell -Command "Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vs_buildtools.exe' -OutFile 'vs_buildtools.exe'"
    echo echo Запуск установщика...
    echo vs_buildtools.exe --quiet --wait --add Microsoft.VisualStudio.Workload.VCTools --add Microsoft.VisualStudio.Component.VC.Tools.x86.x64 --add Microsoft.VisualStudio.Component.Windows10SDK.19041
    echo echo Установка завершена!
    echo del vs_buildtools.exe
    echo pause
) > fix_compilation.bat

echo ✅ Создан файл fix_compilation.bat для решения проблем компиляции
echo.

:: Проверяем установку
echo 🔍 Проверка установки...
python -c "
try:
    import requests
    print('✅ requests установлен')
    import eth_account
    print('✅ eth_account установлен')
    try:
        import web3
        print(f'✅ web3 установлен (версия: {web3.__version__})')
    except Exception as e:
        print(f'⚠️ web3: {e}')
    try:
        import solcx
        print('✅ py-solc-x установлен')
    except Exception as e:
        print(f'⚠️ py-solc-x: {e}')
    print('🎉 Основные модули готовы к работе!')
except Exception as e:
    print(f'❌ Ошибка: {e}')
"

echo.
echo ===============================================
echo     ✅ УСТАНОВКА ЗАВЕРШЕНА!
echo ===============================================
echo.
echo 📋 ЧТО ДАЛЬШЕ:
echo.
echo 1. 📝 Отредактируйте файл private_keys.txt
echo    - Добавьте ваши приватные ключи
echo.
echo 2. 🌐 (Опционально) Отредактируйте proxies.txt
echo    - Добавьте ваши прокси-серверы
echo.
echo 3. 🚀 Запустите бота:
echo    - Дважды кликните на start.bat
echo    - Или выполните: python run.py
echo.
echo 🔧 ЕСЛИ БЫЛИ ОШИБКИ КОМПИЛЯЦИИ:
echo    - Запустите fix_compilation.bat
echo    - Или установите Visual Studio Build Tools вручную
echo    - Затем перезапустите install.bat
echo.
echo ⚠️  ВАЖНО:
echo    - Используйте только тестовые кошельки
echo    - Не делитесь приватными ключами
echo    - Начните с малых сумм
echo.
echo ===============================================

echo.
echo 🎯 Хотите запустить бота сейчас? (y/n)
set /p launch_choice=

if /i "%launch_choice%"=="y" (
    echo.
    echo 🚀 Запуск...
    python run.py
) else (
    echo.
    echo 📝 Не забудьте настроить private_keys.txt перед запуском!
)

echo.
pause