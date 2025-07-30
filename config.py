"""
Упрощенная конфигурация для Jovay Network Automation
"""

from dataclasses import dataclass
from typing import Tuple

@dataclass
class AutomationConfig:
    """Основная конфигурация автоматизации"""
    
    # === ОСНОВНЫЕ НАСТРОЙКИ ===
    max_threads: int = 3                    # Количество потоков
    bridge_count: int = 1                   # Бриджей на кошелек
    deploy_count: int = 3                   # Контрактов на кошелек
    
    # === СУММЫ БРИДЖА ===
    bridge_amount_min: float = 0.001        # Мин сумма бриджа
    bridge_amount_max: float = 0.005        # Макс сумма бриджа
    
    # === ПАУЗЫ (секунды) ===
    pause_between_accounts: Tuple[int, int] = (10, 30)     # Между кошельками
    pause_between_operations: Tuple[int, int] = (5, 15)    # Между операциями
    pause_after_bridge: Tuple[int, int] = (60, 120)        # После бриджа
    pause_after_deploy: Tuple[int, int] = (10, 25)         # После деплоя
    
    # === СЕТИ ===
    sepolia_chain_id: int = 11155111        # Sepolia
    jovay_chain_id: int = 2019775           # Jovay Network
    
    # === RPC (обновлены на июль 2025) ===
    sepolia_rpc: str = "https://eth-sepolia.public.blastapi.io"
    jovay_rpc_public: str = "https://api.zan.top/public/jovay-testnet"          # Публичный RPC
    jovay_rpc_template: str = "https://api.zan.top/node/v1/jovay/testnet/{api_key}"  # С API ключом
    
    # === МИНИМАЛЬНЫЕ БАЛАНСЫ ===
    min_eth_for_bridge: float = 0.003      # Для бриджа
    min_eth_for_deploy: float = 0.001      # Для деплоя


def get_network_info() -> dict:
    """Информация о сетях"""
    return {
        "jovay": {
            "name": "Jovay Testnet",
            "chain_id": 2019775,
            "currency": "ETH",
            "explorer": "https://scan.jovay.io",
            "faucet": "https://zan.top/faucet/jovay"
        },
        "sepolia": {
            "name": "Sepolia Testnet", 
            "chain_id": 11155111,
            "currency": "ETH",
            "explorer": "https://sepolia.etherscan.io",
            "faucet": "https://sepolia-faucet.pk910.de"
        }
    }


def get_contract_types() -> dict:
    """Типы контрактов для деплоя"""
    return {
        "nft": "NFT контракт (токены)",
        "storage": "Storage контракт (хранилище данных)", 
        "smart": "Smart контракт (логика)"
    }


def get_quick_config() -> AutomationConfig:
    """Быстрая конфигурация для тестирования"""
    return AutomationConfig(
        max_threads=1,
        bridge_count=0,  # Без бриджа
        deploy_count=1,  # Один контракт
        pause_between_accounts=(5, 10),
        pause_between_operations=(3, 8),
        pause_after_deploy=(5, 15)
    )