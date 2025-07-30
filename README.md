![JOVAY Banner](https://github.com/NotHennadii/JOVAY_AUTOBOT/blob/main/53683568356853.PNG?raw=true)
## Jovay FUCKER Bot

Автоматизация взаимодействия с Jovay Network (RWA L2) - бридж токенов и деплой контрактов.

## 🚀 Возможности

- **Мультиаккаунтность** - работа с несколькими кошельками
- **Бридж токенов** - автоматический перевод ETH из Sepolia в Jovay Network
- **Деплой контрактов** - создание ERC20, NFT и Staking контрактов
- **Прокси поддержка** - индивидуальные прокси для каждого кошелька
- **Параллельная работа** - многопоточное выполнение задач
- **Умные паузы** - рандомные задержки между операциями

## 📋 Требования

- Python 3.8+
- Windows (для автоустановки)
- Тестовые кошельки с ETH в Sepolia

## ⚡ Быстрый старт

### 1. Автоустановка (Windows)
```bash
git clone https://github.com/your-repo/jovay-automation.git
cd jovay-automation
install.bat
```

### 2. Ручная установка
```bash
git clone https://github.com/your-repo/jovay-automation.git
cd jovay-automation
python -m venv venv
venv\Scripts\activate
pip install -r requirements_compatible.txt
```

### 3. Настройка
Отредактируйте файлы:
- `private_keys.txt` - приватные ключи кошельков
- `api_keys.txt` - API ключи ZAN (опционально)
- `proxies.txt` - прокси серверы (опционально)

### 4. Запуск
```bash
# Windows
start.bat

# Или напрямую
python run.py
```

## 📁 Структура файлов

```
jovay-automation/
├── run.py                    # Главный запускатель
├── jovay_automation.py       # Основная логика бота
├── config.py                 # Конфигурация
├── install.bat               # Автоустановщик для Windows
├── start.bat                 # Быстрый запуск
├── private_keys.txt          # Приватные ключи (создается автоматически)
├── api_keys.txt              # API ключи ZAN
├── proxies.txt               # Прокси серверы
└── proxy_assignments.txt     # Назначение прокси кошелькам
```

## ⚙️ Настройки

### Основные параметры
- **Количество бриджей**: 0-5 на кошелек
- **Количество контрактов**: 1-10 на кошелек  
- **Сумма бриджа**: 0.001-0.005 ETH
- **Режим работы**: последовательно или параллельно

### Типы контрактов
- **Token** - ERC20 токен (1M supply)
- **NFT** - NFT контракт с минтингом
- **Staking** - Стейкинг контракт

## 🌐 Поддерживаемые сети

| Сеть | Chain ID | RPC | Explorer |
|------|----------|-----|----------|
| Sepolia Testnet | 11155111 | eth-sepolia.public.blastapi.io | sepolia.etherscan.io |
| Jovay Network | 2019775 | api.zan.top/public/jovay-testnet | scan.jovay.io |

## 🔧 Прокси настройка

Формат в `proxies.txt`:
```
ip:port
ip:port:username:password
socks5://ip:port
```

Назначение в `proxy_assignments.txt`:
```
1  # Использовать прокси для кошелька 1
0  # Без прокси для кошелька 2
```

## 💰 Получение тестовых токенов

- **Sepolia ETH**: [sepolia-faucet.pk910.de](https://sepolia-faucet.pk910.de)
- **Jovay ETH**: [zan.top/faucet/jovay](https://zan.top/faucet/jovay)

## ⚠️ Безопасность

- ✅ Используйте только тестовые кошельки
- ✅ Никогда не делитесь приватными ключами
- ✅ Начинайте с малых сумм
- ❌ Не используйте основные кошельки

## 📊 Статистика

Бот отслеживает:
- Успешные бриджи
- Задеплоенные контракты
- Ошибки выполнения
- Процент успешности

## 🔍 Проверка результатов

- **Транзакции Sepolia**: [sepolia.etherscan.io](https://sepolia.etherscan.io)
- **Контракты Jovay**: [scan.jovay.io](https://scan.jovay.io)

## 🛠️ Решение проблем

### Ошибки компиляции Windows
```bash
# Запустите для установки Build Tools
fix_compilation.bat
```

### Проблемы с web3
```bash
# Переустановка с совместимой версией
pip uninstall web3
pip install web3==6.0.0
```

## 📝 Логи и отладка

Бот выводит подробные логи:
- 💧 Фаучет операции
- 🌉 Статус бриджей  
- 📦 Деплой контрактов
- ❌ Ошибки выполнения

## 🤝 Поддержка

При возникновении проблем:
1. Проверьте баланс кошельков
2. Убедитесь в корректности RPC
3. Проверьте работу прокси
4. Обновите зависимости

## 📄 Лицензия

MIT License - используйте на свой страх и риск.

---

⚡ **Готов к автоматизации Jovay Network!** ⚡
