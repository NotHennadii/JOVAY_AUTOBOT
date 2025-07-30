#!/usr/bin/env python3
"""
Простой launcher для Jovay Network Automation
Упрощенное меню настроек
"""

import os
import sys
import random
import time # Добавляем импорт time для print_banner

# Добавляем текущую директорию в путь Python
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def check_files():
    """Проверка файлов"""
    required_files = ['jovay_automation.py', 'config.py']

    for filename in required_files:
        if not os.path.exists(filename):
            print(f"❌ Отсутствует файл: {filename}")
            return False

    # Создаем файлы если их нет
    create_config_files()
    return True

def create_config_files():
    """Создание файлов конфигурации"""

    # private_keys.txt
    if not os.path.exists("private_keys.txt"):
        with open("private_keys.txt", 'w', encoding='utf-8') as f:
            f.write("# Добавьте приватные ключи кошельков\n")
            f.write("# Каждый ключ с новой строки\n")
            f.write("# 0x1234567890abcdef...\n")

    # api_keys.txt
    if not os.path.exists("api_keys.txt"):
        with open("api_keys.txt", 'w', encoding='utf-8') as f:
            f.write("# API ключи для каждого кошелька\n")
            f.write("# Порядок должен совпадать с private_keys.txt\n")
            f.write("# 9d9d6aa530b64877be75a16288a7eadb\n")
            f.write("# 8c8c5bb420a53766ae64b17288a6dbea\n")

    # proxies.txt
    if not os.path.exists("proxies.txt"):
        with open("proxies.txt", 'w', encoding='utf-8') as f:
            f.write("# Прокси для кошельков\n")
            f.write("# ip:port:user:pass\n")
            f.write("# 192.168.1.1:8080\n")

    # proxy_assignments.txt
    if not os.path.exists("proxy_assignments.txt"):
        with open("proxy_assignments.txt", 'w', encoding='utf-8') as f:
            f.write("# Назначение прокси для каждого кошелька\n")
            f.write("# 1 = использовать прокси, 0 = без прокси\n")
            f.write("# Порядок должен совпадать с private_keys.txt\n")
            f.write("# 1\n")
            f.write("# 0\n")

def load_wallets_info():
    """Загружает информацию о кошельках"""
    try:
        # Приватные ключи
        with open("private_keys.txt", 'r', encoding='utf-8') as f:
            keys = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        # API ключи
        api_keys = []
        if os.path.exists("api_keys.txt"):
            with open("api_keys.txt", 'r', encoding='utf-8') as f:
                api_keys = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        # Прокси назначения
        proxy_assignments = []
        if os.path.exists("proxy_assignments.txt"):
            with open("proxy_assignments.txt", 'r', encoding='utf-8') as f:
                proxy_assignments = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        # Прокси
        proxies = []
        if os.path.exists("proxies.txt"):
            with open("proxies.txt", 'r', encoding='utf-8') as f:
                proxies = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        # Дополняем недостающие данные
        while len(api_keys) < len(keys):
            api_keys.append("9d9d6aa530b64877be75a16288a7eadb")  # Дефолтный API ключ

        while len(proxy_assignments) < len(keys):
            proxy_assignments.append("0")  # По умолчанию без прокси

        return keys, api_keys, proxy_assignments, proxies

    except Exception as e:
        print(f"❌ Ошибка загрузки файлов: {e}")
        return [], [], [], []

def simple_config_menu():
    """Упрощенное меню настроек"""
    keys, api_keys, proxy_assignments, proxies = load_wallets_info()

    if not keys:
        print("❌ Нет кошельков в private_keys.txt")
        return None

    print(f"\n📋 НАСТРОЙКА АВТОМАТИЗАЦИИ")
    print("=" * 40)

    # 1. Количество кошельков
    print(f"💼 Найдено кошельков: {len(keys)}")
    while True:
        try:
            wallet_count = input(f"Сколько использовать? (1-{len(keys)}): ").strip()
            wallet_count = int(wallet_count) if wallet_count else len(keys)
            if 1 <= wallet_count <= len(keys):
                break
            print("❌ Неверное количество")
        except ValueError:
            print("❌ Введите число")

    # 2. Бриджи
    while True:
        try:
            bridge_count = input("🌉 Бриджей на кошелек (0-5): ").strip()
            bridge_count = int(bridge_count) if bridge_count else 1
            if 0 <= bridge_count <= 5:
                break
            print("❌ От 0 до 5")
        except ValueError:
            print("❌ Введите число")

    # 3. Деплои
    while True:
        try:
            deploy_count = input("📦 Контрактов на кошелек (1-10): ").strip()
            deploy_count = int(deploy_count) if deploy_count else 3
            if 1 <= deploy_count <= 10:
                break
            print("❌ От 1 до 10")
        except ValueError:
            print("❌ Введите число")

    # 4. Режим работы
    print("\n🔧 Режим работы:")
    print("1. Последовательно (один за другим)")
    print("2. Параллельно (несколько одновременно)")

    while True:
        mode = input("Выберите (1-2): ").strip()
        if mode in ['1', '2']:
            parallel = mode == '2'
            break
        print("❌ Выберите 1 или 2")

    # 5. Настройка прокси
    if proxies:
        print(f"\n🌐 Найдено прокси: {len(proxies)}")
        setup_proxies = input("Настроить прокси для кошельков? (y/n): ").lower().strip()

        if setup_proxies in ['y', 'yes', 'да']:
            configure_proxy_assignments(wallet_count)

    # Возвращаем конфигурацию
    config = {
        'wallet_count': wallet_count,
        'bridge_count': bridge_count,
        'deploy_count': deploy_count,
        'parallel': parallel,
        'bridge_amount_min': 0.001,
        'bridge_amount_max': 0.005
    }

    return config

def configure_proxy_assignments(wallet_count):
    """Настройка прокси для кошельков"""
    print(f"\n🔧 Настройка прокси для {wallet_count} кошельков:")
    print("Для каждого кошелька выберите:")
    print("1 = использовать прокси")
    print("0 = без прокси")

    assignments = []
    for i in range(wallet_count):
        while True:
            choice = input(f"Кошелек {i+1}: ").strip()
            if choice in ['0', '1']:
                assignments.append(choice)
                break
            print("❌ Введите 0 или 1")

    # Сохраняем в файл
    try:
        with open("proxy_assignments.txt", 'w', encoding='utf-8') as f:
            f.write("# Назначение прокси (1=да, 0=нет)\n")
            for assignment in assignments:
                f.write(f"{assignment}\n")
        print("✅ Настройки прокси сохранены")
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")

def show_summary(config):
    """Показать сводку настроек"""
    keys, _, _, proxies = load_wallets_info()

    print(f"\n📊 СВОДКА НАСТРОЕК")
    print("=" * 30)
    print(f"💼 Кошельков: {config['wallet_count']}")
    print(f"🌉 Бриджей: {config['bridge_count']} на кошелек")
    print(f"📦 Контрактов: {config['deploy_count']} на кошелек")
    print(f"⚡ Режим: {'Параллельно' if config['parallel'] else 'Последовательно'}")
    print(f"💰 Сумма бриджа: {config['bridge_amount_min']}-{config['bridge_amount_max']} ETH")
    print(f"🌐 Прокси: {'Настроены' if proxies else 'Отключены'}")

def run_automation(config):
    """Запуск автоматизации с упрощенной конфигурацией"""
    try:
        from jovay_automation import MultiAccountManager, Config

        # Создаем упрощенную конфигурацию
        automation_config = Config(
            max_threads=config['wallet_count'] if config['parallel'] else 1,
            bridge_count=config['bridge_count'],
            deploy_count=config['deploy_count'],
            bridge_amount_min=config['bridge_amount_min'],
            bridge_amount_max=config['bridge_amount_max'],
            use_proxy=True,  # Будет определяться индивидуально
            pause_between_accounts=(10, 30),
            pause_between_operations=(5, 15),
            pause_after_bridge=(60, 120),
            pause_after_deploy=(10, 25)
        )

        manager = MultiAccountManager(automation_config)

        # Ограничиваем количество кошельков
        if config['wallet_count'] < len(manager.private_keys):
            manager.private_keys = manager.private_keys[:config['wallet_count']]

        print(f"\n🚀 ЗАПУСК АВТОМАТИЗАЦИИ")
        print("=" * 30)

        if config['parallel']:
            manager.run_multi_threaded()
        else:
            manager.run_sequential()

    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")

def print_banner():
    """Печатает ASCII баннер с анимацией"""
    # Очищаем экран для лучшего эффекта
    os.system('cls' if os.name == 'nt' else 'clear')

    banner = """

    ┌───────────────────────────────────────────────────────────────────────────┐
    │   ██╗ ██████╗ ██╗    ██╗  █████╗ ██╗    ██╗     ██████╗  ██████╗ ████████╗│
    │   ██║██╔═══██╗██║    ██║ ██╔══██╗╚██╗ ██╔╝      ██╔══██╗██╔═══██╗╚══██╔══╝│
    │   ██║██║   ██║██║    ██║ ███████║ ╚████╔╝       ██████╔╝██║   ██║   ██║   │
    │██╗██║██║   ██║╚██╗  ██╔╝ ██╔══██║  ╚██╔╝        ██╔══██╗██║   ██║   ██║   │
    │╚████║╚██████╔╝ ╚█████╔╝  ██║  ██║   ██║         ██████╔╝╚██████╔╝   ██║   │
    │ ╚═══╝ ╚═════╝   ╚════╝   ╚═╝  ╚═╝   ╚═╝         ╚═════╝  ╚═════╝    ╚═╝   │
    │                                                                           │
    │                                 FUCKER BOT                                │
    │                                                                           │
    │               [+] INITIALIZING AUTOMATION PROTOCOL [+]                    │
    │               [+] LOADING MULTI-ACCOUNT MANAGER... [+]                    │
    │               [+] CONNECTING TO RWA L2 NETWORK... [+]                     │
    │               [+] STATUS: READY FOR DEPLOYMENT [+]                        │
    └───────────────────────────────────────────────────────────────────────────┘
    """

    # Пытаемся добавить цвета
    try:
        from colorama import init, Fore, Style
        init()

        # Цветной баннер
        colored_lines = []
        for line in banner.split('\n'):
            # Применяем светло-голубой цвет ко всей строке
            colored_lines.append(Fore.CYAN + line + Style.RESET_ALL)

        # Печатаем с небольшой анимацией
        for line in colored_lines:
            print(line)
            time.sleep(0.05)  # Небольшая задержка для эффекта

    except ImportError:
        # Если colorama не установлена, печатаем обычный баннер
        for line in banner.split('\n'):
            print(line)
            time.sleep(0.05)


def main():
    """Главная функция"""
    # Показываем красивый баннер
    print_banner()

    # Проверяем наличие colorama для цветного вывода
    try:
        from colorama import Fore, Style
        print(Fore.CYAN + "JOVAY FUCKER BOT" + Style.RESET_ALL)
    except ImportError:
        print("JOVAY FUCKER BOT")

    print("=" * 70)

    # Проверяем файлы
    if not check_files():
        print("❌ Проблемы с файлами проекта")
        input("Нажмите Enter для выхода...")
        return

    # Проверяем кошельки
    keys, api_keys, proxy_assignments, proxies = load_wallets_info()
    if not keys:
        print("❌ Добавьте приватные ключи в private_keys.txt")
        input("Нажмите Enter для выхода...")
        return

    print(f"✅ Загружено {len(keys)} кошельков")
    print(f"✅ API ключей: {len(api_keys)}")
    print(f"✅ Прокси: {len(proxies)}")

    # Меню
    print("\n📋 ВЫБЕРИТЕ ДЕЙСТВИЕ:")
    print("1. 🚀 Запустить автоматизацию")
    print("2. 🔧 Настроить прокси")
    print("3. ❌ Выход")

    choice = input("\nВыбор (1-3): ").strip()

    if choice == "1":
        config = simple_config_menu()
        if config:
            show_summary(config)
            confirm = input("\n✅ Запустить? (y/n): ").lower().strip()
            if confirm in ['y', 'yes', 'да']:
                run_automation(config)

    elif choice == "2":
        print("🔧 Настройка прокси...")
        wallet_count = len(keys)
        configure_proxy_assignments(wallet_count)

    elif choice == "3":
        print("👋 Выход")
        return

    else:
        print("❌ Неверный выбор")

    input("\nНажмите Enter для выхода...")

if __name__ == "__main__":
    main()
