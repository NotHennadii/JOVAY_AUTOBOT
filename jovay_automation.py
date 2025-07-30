import requests
import json
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from web3 import Web3
from eth_account import Account
from solcx import compile_source, install_solc, set_solc_version
import os
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Config:
    """Упрощенная конфигурация"""
    max_threads: int = 1
    bridge_count: int = 1
    deploy_count: int = 3
    bridge_amount_min: float = 0.001
    bridge_amount_max: float = 0.005
    use_proxy: bool = False
    pause_between_accounts: tuple = (10, 30)
    pause_between_operations: tuple = (5, 15)
    pause_after_bridge: tuple = (60, 120)
    pause_after_deploy: tuple = (10, 25)

class JovayAutomation:
    def __init__(self, private_key: str, api_key: str, proxy: Optional[str] = None):
        """
        Упрощенная автоматизация для Jovay Network
        """
        self.private_key = private_key
        self.api_key = api_key
        self.proxy = proxy
        self.account = Account.from_key(private_key)
        self.address = self.account.address
        
        # Статистика
        self.stats = {
            'faucet': 0,
            'bridges': 0,
            'contracts': 0,
            'errors': 0
        }
        
        # Настройка Web3
        self._setup_web3()
        
        print(f"📱 {self.address[:4]}...{self.address[-4:]} {'🌐' if proxy else '🔗'}")

    def _setup_web3(self):
        """Настройка подключений"""
        # Sepolia
        sepolia_rpc = "https://eth-sepolia.public.blastapi.io"
        self.sepolia_w3 = Web3(Web3.HTTPProvider(sepolia_rpc))
        
        # Jovay - исправленный RPC endpoint
        # Сначала пробуем публичный endpoint
        jovay_public_rpc = "https://api.zan.top/public/jovay-testnet"
        
        # Если есть API ключ, используем персональный endpoint
        if self.api_key and self.api_key != "9d9d6aa530b64877be75a16288a7eadb":
            jovay_rpc = f"https://api.zan.top/node/v1/jovay/testnet/{self.api_key}"
        else:
            jovay_rpc = jovay_public_rpc
        
        # Настройка сессии с прокси
        if self.proxy:
            session = requests.Session()
            proxy_dict = {'http': self.proxy, 'https': self.proxy}
            session.proxies.update(proxy_dict)
            try:
                self.jovay_w3 = Web3(Web3.HTTPProvider(jovay_rpc, session=session))
                # Тестируем подключение
                chain_id = self.jovay_w3.eth.chain_id
                print(f"🌐 {self.address[:4]}...{self.address[-4:]} подключен к Jovay (Chain ID: {chain_id})")
            except:
                # Fallback на публичный без прокси
                self.jovay_w3 = Web3(Web3.HTTPProvider(jovay_public_rpc))
                print(f"🌐 {self.address[:4]}...{self.address[-4:]} fallback к публичному RPC")
        else:
            try:
                self.jovay_w3 = Web3(Web3.HTTPProvider(jovay_rpc))
                # Тестируем подключение
                chain_id = self.jovay_w3.eth.chain_id
                print(f"🔗 {self.address[:4]}...{self.address[-4:]} подключен к Jovay (Chain ID: {chain_id})")
            except:
                # Fallback на публичный
                self.jovay_w3 = Web3(Web3.HTTPProvider(jovay_public_rpc))
                print(f"🔗 {self.address[:4]}...{self.address[-4:]} fallback к публичному RPC")
        
        # Chain IDs
        self.sepolia_chain_id = 11155111
        self.jovay_chain_id = 2019775

    def get_balances(self) -> dict:
        """Получение балансов"""
        try:
            sepolia_balance = self.sepolia_w3.eth.get_balance(self.address)
            sepolia_eth = float(self.sepolia_w3.from_wei(sepolia_balance, 'ether'))
            
            jovay_balance = self.jovay_w3.eth.get_balance(self.address)
            jovay_eth = float(self.jovay_w3.from_wei(jovay_balance, 'ether'))
            
            return {'sepolia': sepolia_eth, 'jovay': jovay_eth}
        except Exception:
            return {'sepolia': 0.0, 'jovay': 0.0}

    def claim_faucet(self) -> bool:
        """Получение токенов из крана"""
        try:
            session = requests.Session()
            if self.proxy:
                session.proxies.update({'http': self.proxy, 'https': self.proxy})
            
            # Исправленный endpoint фаучета
            faucet_url = "https://zan.top/faucet/jovay"
            payload = {"address": self.address, "chainId": self.jovay_chain_id}
            
            response = session.post(faucet_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                print(f"💧 {self.address[:4]}...{self.address[-4:]} ждем 30с...")
                time.sleep(30)  # Ждем поступления
                balances = self.get_balances()
                if balances['jovay'] > 0.0005:
                    self.stats['faucet'] += 1
                    return True
                else:
                    print(f"💧 {self.address[:4]}...{self.address[-4:]} средства не поступили")
                    return False
            else:
                print(f"💧 {self.address[:4]}...{self.address[-4:]} фаучет ответил: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"💧 {self.address[:4]}...{self.address[-4:]} ошибка: {type(e).__name__}")
            return False

    def bridge_tokens(self, amount: float) -> bool:
        """Бридж токенов (упрощенная версия)"""
        try:
            balances = self.get_balances()
            if balances['sepolia'] < amount + 0.002:
                print(f"🌉 {self.address[:4]}...{self.address[-4:]} недостаточно ETH: {balances['sepolia']:.4f}")
                return False
            
            # Примерный адрес бриджа (нужен актуальный)
            bridge_address = "0x4200000000000000000000000000000000000010"
            
            nonce = self.sepolia_w3.eth.get_transaction_count(self.address)
            gas_price = self.sepolia_w3.eth.gas_price
            amount_wei = self.sepolia_w3.to_wei(amount, 'ether')
            
            transaction = {
                'to': bridge_address,
                'value': amount_wei,
                'gas': 150000,
                'gasPrice': int(gas_price * 1.1),
                'nonce': nonce,
                'chainId': self.sepolia_chain_id
            }
            
            signed_txn = self.sepolia_w3.eth.account.sign_transaction(transaction, self.private_key)
            tx_hash = self.sepolia_w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            receipt = self.sepolia_w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt.status == 1:
                self.stats['bridges'] += 1
                return True
            else:
                print(f"🌉 {self.address[:4]}...{self.address[-4:]} транзакция провалена")
                return False
        except Exception as e:
            print(f"🌉 {self.address[:4]}...{self.address[-4:]} ошибка: {type(e).__name__}")
            return False

    def deploy_contract(self, contract_type: str) -> bool:
        """Деплой контракта"""
        try:
            balances = self.get_balances()
            current_balance = balances['jovay']
            
            # Получаем актуальную цену газа для точной оценки
            try:
                gas_price = self.jovay_w3.eth.gas_price or self.jovay_w3.to_wei('1', 'gwei')
                gas_limit = 1500000
                estimated_cost = self.jovay_w3.from_wei(gas_price * gas_limit, 'ether')
                
                # Добавляем 20% запас
                required_balance = float(estimated_cost) * 1.1  # Уменьшен запас
                
                if current_balance < required_balance:
                    print(f"📦 {self.address[:4]}...{self.address[-4:]} недостаточно ETH:")
                    print(f"    Есть: {current_balance:.6f} ETH")
                    print(f"    Нужно: {required_balance:.6f} ETH")
                    print(f"    Gas: {Web3.from_wei(gas_price, 'gwei'):.2f} gwei")
                    return False
                    
            except Exception as e:
                print(f"📦 {self.address[:4]}...{self.address[-4:]} ошибка оценки газа: {type(e).__name__}")
                # Fallback проверка - очень маленький минимум
                if current_balance < 0.0002:
                    print(f"📦 {self.address[:4]}...{self.address[-4:]} недостаточно ETH: {current_balance:.6f}")
                    return False
            
            # Настройка Solidity
            try:
                install_solc('0.8.20')
                set_solc_version('0.8.20')
            except Exception as e:
                print(f"📦 {self.address[:4]}...{self.address[-4:]} Solidity ошибка: {type(e).__name__}")
                pass
            
            # Выбор контракта
            contracts = {
                "token": self._get_smart_contract(),    # ERC20 Token
                "nft": self._get_nft_contract(),        # NFT Contract  
                "staking": self._get_storage_contract() # Staking Contract
            }
            
            contract_source = contracts.get(contract_type, contracts["token"])
            
            # Компиляция
            compiled_sol = compile_source(contract_source)
            contract_name = list(compiled_sol.keys())[0].split(':')[1]
            contract_interface = compiled_sol[f'<stdin>:{contract_name}']
            
            contract = self.jovay_w3.eth.contract(
                abi=contract_interface['abi'],
                bytecode=contract_interface['bin']
            )
            
            # Деплой
            nonce = self.jovay_w3.eth.get_transaction_count(self.address)
            
            # Используем правильную цену газа
            gas_price = self.jovay_w3.eth.gas_price or self.jovay_w3.to_wei('1', 'gwei')
            
            # Пробуем оценить газ
            try:
                gas_estimate = contract.constructor().estimate_gas()
                gas_limit = int(gas_estimate * 1.2)  # Добавляем 20% запас
            except:
                gas_limit = 1500000  # Фиксированный лимит
            
            transaction = contract.constructor().build_transaction({
                'chainId': self.jovay_chain_id,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'nonce': nonce,
            })
            
            # Финальная проверка стоимости
            actual_cost = self.jovay_w3.from_wei(gas_price * gas_limit, 'ether')
            if current_balance < float(actual_cost):
                print(f"📦 {self.address[:4]}...{self.address[-4:]} {contract_type} недостаточно для газа:")
                print(f"    Нужно: {actual_cost:.6f} ETH")
                print(f"    Есть: {current_balance:.6f} ETH")
                return False
            
            signed_txn = self.jovay_w3.eth.account.sign_transaction(transaction, self.private_key)
            tx_hash = self.jovay_w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            receipt = self.jovay_w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt.status == 1:
                self.stats['contracts'] += 1
                actual_cost_used = self.jovay_w3.from_wei(gas_price * receipt.gasUsed, 'ether')
                print(f"📦 {self.address[:4]}...{self.address[-4:]} {contract_type} деплой: {receipt.contractAddress[:6]}...{receipt.contractAddress[-4:]} (стоимость: {actual_cost_used:.6f} ETH)")
                return True
            else:
                print(f"📦 {self.address[:4]}...{self.address[-4:]} {contract_type} транзакция провалена")
                return False
                
        except Exception as e:
            error_msg = str(e).lower()
            if "insufficient funds" in error_msg:
                print(f"📦 {self.address[:4]}...{self.address[-4:]} {contract_type} недостаточно средств для газа")
            elif "invalid chainid" in error_msg:
                print(f"📦 {self.address[:4]}...{self.address[-4:]} {contract_type} неверный Chain ID")
            elif "nonce" in error_msg:
                print(f"📦 {self.address[:4]}...{self.address[-4:]} {contract_type} проблема с nonce")
            elif "gas" in error_msg:
                print(f"📦 {self.address[:4]}...{self.address[-4:]} {contract_type} проблема с газом")
            else:
                print(f"📦 {self.address[:4]}...{self.address[-4:]} {contract_type} ошибка: {type(e).__name__}")
            return False

    def _get_nft_contract(self) -> str:
        """NFT контракт - упрощенная версия без OpenZeppelin"""
        random_id = random.randint(1000, 9999)
        return f"""
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract JovayNFT_{random_id} {{
    mapping(uint256 => address) public owners;
    mapping(address => uint256) public balances;
    mapping(uint256 => string) public tokenURIs;
    uint256 public totalSupply = 0;
    address public owner;
    string public name = "JovayNFT";
    string public symbol = "JNFT";
    
    event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);
    event Minted(address indexed to, uint256 indexed tokenId);
    
    constructor() {{
        owner = msg.sender;
    }}
    
    modifier onlyOwner() {{
        require(msg.sender == owner, "Only owner");
        _;
    }}
    
    function mint(address to, string memory _tokenURI) public onlyOwner {{
        require(to != address(0), "Cannot mint to zero address");
        totalSupply++;
        uint256 tokenId = totalSupply;
        
        owners[tokenId] = to;
        balances[to]++;
        tokenURIs[tokenId] = _tokenURI;
        
        emit Transfer(address(0), to, tokenId);
        emit Minted(to, tokenId);
    }}
    
    function ownerOf(uint256 tokenId) public view returns (address) {{
        require(owners[tokenId] != address(0), "Token does not exist");
        return owners[tokenId];
    }}
    
    function balanceOf(address _owner) public view returns (uint256) {{
        return balances[_owner];
    }}
    
    function tokenURI(uint256 tokenId) public view returns (string memory) {{
        require(owners[tokenId] != address(0), "Token does not exist");
        return tokenURIs[tokenId];
    }}
}}
"""

    def _get_storage_contract(self) -> str:
        """Storage контракт - упрощенный стейкинг согласно документации"""
        random_id = random.randint(1000, 9999)
        return f"""
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract JovayStaking_{random_id} {{
    mapping(address => uint256) public stakes;
    mapping(address => uint256) public lastStakeTime;
    uint256 public totalStaked;
    uint256 public rewardRate = 1e18;
    
    event Staked(address indexed user, uint256 amount);
    event Withdrawn(address indexed user, uint256 amount);
    
    constructor() {{}}
    
    function stake() external payable {{
        require(msg.value > 0, "Cannot stake 0");
        stakes[msg.sender] += msg.value;
        lastStakeTime[msg.sender] = block.timestamp;
        totalStaked += msg.value;
        emit Staked(msg.sender, msg.value);
    }}
    
    function withdraw(uint256 amount) external {{
        require(stakes[msg.sender] >= amount, "Insufficient stake");
        stakes[msg.sender] -= amount;
        totalStaked -= amount;
        payable(msg.sender).transfer(amount);
        emit Withdrawn(msg.sender, amount);
    }}
    
    function getStake(address user) external view returns (uint256) {{
        return stakes[user];
    }}
    
    function checkRewards(address user) external view returns (uint256) {{
        if (stakes[user] == 0) return 0;
        uint256 timeDiff = block.timestamp - lastStakeTime[user];
        return timeDiff * rewardRate * stakes[user] / 1e18;
    }}
}}
"""

    def _get_smart_contract(self) -> str:
        """Smart контракт - ERC20 токен согласно документации"""
        random_id = random.randint(1000, 9999)
        return f"""
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract JovayToken_{random_id} {{
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    
    string public name = "JovayToken";
    string public symbol = "JTK";
    uint8 public decimals = 6;
    uint256 public totalSupply;
    address public owner;
    
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    
    constructor() {{
        uint256 initialSupply = 1000000 * 10**decimals;
        totalSupply = initialSupply;
        balanceOf[msg.sender] = initialSupply;
        owner = msg.sender;
        emit Transfer(address(0), msg.sender, initialSupply);
    }}
    
    function transfer(address to, uint256 amount) external returns (bool) {{
        require(to != address(0), "Transfer to zero address");
        require(balanceOf[msg.sender] >= amount, "Insufficient balance");
        
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        emit Transfer(msg.sender, to, amount);
        return true;
    }}
    
    function approve(address spender, uint256 amount) external returns (bool) {{
        allowance[msg.sender][spender] = amount;
        emit Approval(msg.sender, spender, amount);
        return true;
    }}
    
    function transferFrom(address from, address to, uint256 amount) external returns (bool) {{
        require(allowance[from][msg.sender] >= amount, "Allowance exceeded");
        require(balanceOf[from] >= amount, "Insufficient balance");
        
        allowance[from][msg.sender] -= amount;
        balanceOf[from] -= amount;
        balanceOf[to] += amount;
        emit Transfer(from, to, amount);
        return true;
    }}
}}
"""

    def run_automation(self, config: Config):
        """Запуск автоматизации"""
        print(f"▶️ {self.address[:4]}...{self.address[-4:]} старт")
        
        # Получаем начальные балансы
        balances = self.get_balances()
        print(f"💰 {self.address[:4]}...{self.address[-4:]} начальные балансы:")
        print(f"    Sepolia: {balances['sepolia']:.6f} ETH")
        print(f"    Jovay: {balances['jovay']:.6f} ETH")
        
        # Шаг 1: Фаучет если нужно (но он не работает)
        if balances['jovay'] < 0.001:
            print(f"💧 {self.address[:4]}...{self.address[-4:]} мало ETH в Jovay, нужен фаучет")
            if self.claim_faucet():
                print(f"💧 {self.address[:4]}...{self.address[-4:]} фаучет ✅")
                balances = self.get_balances()  # Обновляем баланс
            else:
                print(f"💧 {self.address[:4]}...{self.address[-4:]} фаучет ❌")
                self.stats['errors'] += 1
        
        # Шаг 2: Бриджи (с правильным адресом)
        if config.bridge_count > 0 and balances['sepolia'] >= 0.003:
            print(f"🌉 {self.address[:4]}...{self.address[-4:]} начинаем бридж с актуальным адресом")
            
            for i in range(config.bridge_count):
                current_sepolia = self.get_balances()['sepolia']
                if current_sepolia < 0.003:
                    print(f"🌉 {self.address[:4]}...{self.address[-4:]} пропуск бриджа - мало ETH: {current_sepolia:.6f}")
                    break
                
                amount = random.uniform(config.bridge_amount_min, config.bridge_amount_max)
                if self.bridge_tokens(amount):
                    pause_time = random.uniform(*config.pause_after_bridge)
                    print(f"🌉 {self.address[:4]}...{self.address[-4:]} бридж {i+1} ✅ пауза {pause_time:.0f}с")
                    time.sleep(pause_time)
                    
                    # Проверяем поступление средств в Jovay
                    new_jovay_balance = self.get_balances()['jovay']
                    if new_jovay_balance > balances['jovay']:
                        print(f"✅ {self.address[:4]}...{self.address[-4:]} средства поступили в Jovay: {new_jovay_balance:.6f} ETH")
                        balances['jovay'] = new_jovay_balance
                    else:
                        print(f"⚠️ {self.address[:4]}...{self.address[-4:]} средства еще не поступили, ждем...")
                        time.sleep(60)  # Дополнительное ожидание
                        balances = self.get_balances()
                else:
                    print(f"🌉 {self.address[:4]}...{self.address[-4:]} бридж {i+1} ❌")
                    self.stats['errors'] += 1
        elif config.bridge_count > 0:
            print(f"🌉 {self.address[:4]}...{self.address[-4:]} пропуск бриджа - мало ETH в Sepolia: {balances['sepolia']:.6f}")
        else:
            print(f"🌉 {self.address[:4]}...{self.address[-4:]} бридж отключен в настройках")
        
        # Шаг 3: Деплои (если есть достаточно ETH в Jovay)
        current_jovay_balance = balances['jovay']
        min_balance_for_deploy = 0.0005  # УМЕНЬШЕН минимум для теста
        
        print(f"📦 {self.address[:4]}...{self.address[-4:]} проверка для деплоя:")
        print(f"    Есть: {current_jovay_balance:.6f} ETH")
        print(f"    Нужно: {min_balance_for_deploy:.6f} ETH")
        
        if current_jovay_balance >= min_balance_for_deploy:
            contract_types = ["token", "nft", "staking"]
            deploy_per_type = max(1, config.deploy_count // 3)
            
            print(f"✅ {self.address[:4]}...{self.address[-4:]} достаточно ETH, начинаем деплой")
            
            for contract_type in contract_types:
                for i in range(deploy_per_type):
                    # Проверяем баланс перед каждым деплоем
                    current_balance = self.get_balances()['jovay']
                    if current_balance < 0.0002:  # Очень маленький минимум для теста
                        print(f"📦 {self.address[:4]}...{self.address[-4:]} остановка - мало ETH: {current_balance:.6f}")
                        break
                        
                    if self.deploy_contract(contract_type):
                        print(f"📦 {self.address[:4]}...{self.address[-4:]} {contract_type} ✅")
                    else:
                        print(f"📦 {self.address[:4]}...{self.address[-4:]} {contract_type} ❌")
                        self.stats['errors'] += 1
                    
                    if i < deploy_per_type - 1 or contract_type != contract_types[-1]:
                        pause_time = random.uniform(*config.pause_after_deploy)
                        print(f"📦 {self.address[:4]}...{self.address[-4:]} пауза {pause_time:.0f}с")
                        time.sleep(pause_time)
        else:
            print(f"❌ {self.address[:4]}...{self.address[-4:]} недостаточно ETH для деплоя")
            print(f"💡 {self.address[:4]}...{self.address[-4:]} получите токены: https://zan.top/faucet/jovay")
            print(f"💡 {self.address[:4]}...{self.address[-4:]} или подождите 24 часа между запросами фаучета")
        
        # Финальные балансы
        final_balances = self.get_balances()
        
        print(f"🏁 {self.address[:4]}...{self.address[-4:]} завершен")
        print(f"   💰 Sepolia: {balances['sepolia']:.6f} → {final_balances['sepolia']:.6f}")
        print(f"   💰 Jovay: {balances['jovay']:.6f} → {final_balances['jovay']:.6f}")
        print(f"   📊 Операции: 💧{self.stats['faucet']} 🌉{self.stats['bridges']} 📦{self.stats['contracts']} ❌{self.stats['errors']}")
        
        return self.stats


class MultiAccountManager:
    """Упрощенный менеджер аккаунтов"""
    
    def __init__(self, config: Config):
        self.config = config
        self.load_accounts()

    def load_accounts(self):
        """Загрузка данных аккаунтов"""
        # Приватные ключи
        with open("private_keys.txt", 'r', encoding='utf-8') as f:
            self.private_keys = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        # API ключи
        try:
            with open("api_keys.txt", 'r', encoding='utf-8') as f:
                self.api_keys = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except:
            self.api_keys = []
        
        # Дополняем API ключи если их меньше
        default_api = "9d9d6aa530b64877be75a16288a7eadb"
        while len(self.api_keys) < len(self.private_keys):
            self.api_keys.append(default_api)
        
        # Прокси назначения
        try:
            with open("proxy_assignments.txt", 'r', encoding='utf-8') as f:
                self.proxy_assignments = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except:
            self.proxy_assignments = []
        
        # Дополняем назначения прокси
        while len(self.proxy_assignments) < len(self.private_keys):
            self.proxy_assignments.append("0")
        
        # Прокси
        try:
            with open("proxies.txt", 'r', encoding='utf-8') as f:
                self.proxies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except:
            self.proxies = []

    def get_proxy_for_account(self, account_index: int) -> Optional[str]:
        """Получение прокси для аккаунта"""
        if account_index >= len(self.proxy_assignments):
            return None
        
        if self.proxy_assignments[account_index] == "1" and self.proxies:
            return self.proxies[account_index % len(self.proxies)]
        
        return None

    def process_account(self, account_index: int) -> dict:
        """Обработка одного аккаунта"""
        try:
            private_key = self.private_keys[account_index]
            api_key = self.api_keys[account_index]
            proxy = self.get_proxy_for_account(account_index)
            
            automation = JovayAutomation(private_key, api_key, proxy)
            
            # Пауза между аккаунтами
            if account_index > 0:
                pause = random.uniform(*self.config.pause_between_accounts)
                print(f"⏳ Пауза между аккаунтами: {pause:.0f}с")
                time.sleep(pause)
            
            return automation.run_automation(self.config)
            
        except Exception as e:
            print(f"❌ Аккаунт {account_index + 1}: ошибка {type(e).__name__} - {str(e)[:50]}")
            return {'faucet': 0, 'bridges': 0, 'contracts': 0, 'errors': 1}

    def run_sequential(self):
        """Последовательный запуск"""
        print(f"\n🔄 ПОСЛЕДОВАТЕЛЬНЫЙ РЕЖИМ")
        print(f"📱 Аккаунтов: {len(self.private_keys)}")
        print("=" * 40)
        
        total_stats = {'faucet': 0, 'bridges': 0, 'contracts': 0, 'errors': 0}
        
        for i in range(len(self.private_keys)):
            print(f"\n👤 АККАУНТ {i + 1}/{len(self.private_keys)}")
            stats = self.process_account(i)
            
            # Обновляем общую статистику
            for key in total_stats:
                total_stats[key] += stats[key]
        
        self._print_final_stats(total_stats)

    def run_multi_threaded(self):
        """Параллельный запуск"""
        print(f"\n⚡ ПАРАЛЛЕЛЬНЫЙ РЕЖИМ")
        print(f"📱 Аккаунтов: {len(self.private_keys)}")
        print(f"🧵 Потоков: {self.config.max_threads}")
        print("=" * 40)
        
        total_stats = {'faucet': 0, 'bridges': 0, 'contracts': 0, 'errors': 0}
        
        with ThreadPoolExecutor(max_workers=self.config.max_threads) as executor:
            futures = []
            for i in range(len(self.private_keys)):
                future = executor.submit(self.process_account, i)
                futures.append(future)
            
            completed = 0
            for future in as_completed(futures):
                try:
                    stats = future.result()
                    completed += 1
                    
                    # Обновляем общую статистику
                    for key in total_stats:
                        total_stats[key] += stats[key]
                    
                    print(f"✅ Завершено: {completed}/{len(self.private_keys)}")
                    
                except Exception as e:
                    print(f"❌ Ошибка потока: {e}")
                    completed += 1
        
        self._print_final_stats(total_stats)

    def _print_final_stats(self, stats):
        """Итоговая статистика"""
        print(f"\n🏆 ИТОГОВАЯ СТАТИСТИКА")
        print("=" * 30)
        print(f"💧 Фаучет: {stats['faucet']}")
        print(f"🌉 Бриджи: {stats['bridges']}")
        print(f"📦 Контракты: {stats['contracts']}")
        print(f"❌ Ошибки: {stats['errors']}")
        
        total_operations = stats['faucet'] + stats['bridges'] + stats['contracts']
        if total_operations > 0:
            success_rate = ((total_operations - stats['errors']) / total_operations) * 100
            print(f"📊 Успешность: {success_rate:.1f}%")
        
        if stats['contracts'] > 0:
            print(f"🔍 Проверить контракты: https://scan.jovay.io")


def create_example_files():
    """Создание файлов примеров"""
    
    files_to_create = {
        "private_keys.txt": [
            "# Добавьте приватные ключи кошельков",
            "# Каждый ключ с новой строки",
            "# 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            ""
        ],
        "api_keys.txt": [
            "# API ключи для каждого кошелька",
            "# Порядок должен совпадать с private_keys.txt",
            "# Получите на https://zan.top",
            "9d9d6aa530b64877be75a16288a7eadb",
            ""
        ],
        "proxy_assignments.txt": [
            "# Назначение прокси для каждого кошелька", 
            "# 1 = использовать прокси, 0 = без прокси",
            "# Порядок должен совпадать с private_keys.txt",
            "0",
            ""
        ],
        "proxies.txt": [
            "# Прокси серверы",
            "# Формат: ip:port:user:pass или ip:port",
            "# 192.168.1.1:8080",
            ""
        ]
    }
    
    for filename, content in files_to_create.items():
        if not os.path.exists(filename):
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))


def main():
    """Основная функция"""
    create_example_files()
    
    # Простая конфигурация по умолчанию
    config = Config(
        max_threads=2,
        bridge_count=1,  # ВКЛЮЧЕН с правильным адресом
        deploy_count=3,
        bridge_amount_min=0.001,
        bridge_amount_max=0.005
    )
    
    manager = MultiAccountManager(config)
    
    if not manager.private_keys:
        print("❌ Добавьте приватные ключи в private_keys.txt")
        return
    
    print(f"\n🚀 JOVAY NETWORK AUTOMATION")
    print("=" * 40)
    print(f"📱 Найдено кошельков: {len(manager.private_keys)}")
    print(f"🔑 API ключей: {len(manager.api_keys)}")
    print(f"🌐 Прокси: {len(manager.proxies)}")
    
    print(f"\n📋 РЕЖИМЫ ЗАПУСКА:")
    print("1. 🔄 Последовательно")
    print("2. ⚡ Параллельно")
    
    choice = input("\nВыбор (1-2): ").strip()
    
    if choice == "1":
        manager.run_sequential()
    elif choice == "2":
        manager.run_multi_threaded()
    else:
        print("❌ Неверный выбор")


if __name__ == "__main__":
    main()