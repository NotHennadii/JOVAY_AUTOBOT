import requests
import json
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from web3 import Web3
from eth_account import Account
try:
    from solcx import compile_source, install_solc, set_solc_version
    SOLC_AVAILABLE = True
except ImportError:
    SOLC_AVAILABLE = False
    print("⚠️ solcx не установлен, деплой контрактов недоступен")
import os
from dataclasses import dataclass
from typing import List, Optional, Dict

@dataclass
class Config:
    """Конфигурация с низкими требованиями"""
    max_threads: int = 1
    bridge_count: int = 2  # ВКЛЮЧЕН
    deploy_count: int = 3
    bridge_amount_min: float = 0.001
    bridge_amount_max: float = 0.005
    use_proxy: bool = False
    pause_between_accounts: tuple = (15, 30)
    pause_between_operations: tuple = (5, 10)
    pause_after_bridge: tuple = (60, 120)
    pause_after_deploy: tuple = (8, 15)
    pause_after_faucet: tuple = (30, 60)
    rpc_delay: float = 1.0

class JovayAutomation:
    def __init__(self, private_key: str, api_key: str, proxy: Optional[str] = None):
        """
        Автоматизация для деплоя с минимальными требованиями
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
        
        # Инициализация Web3 подключений
        self.jovay_w3 = None
        self.sepolia_w3 = None
        self.jovay_chain_id = 2019775
        self.sepolia_chain_id = 11155111
        
        # Настройка Web3
        self._setup_web3()
        self._setup_sepolia_web3()
        
        print(f"📱 {self.address[:4]}...{self.address[-4:]} {'🌐' if proxy else '🔗'}")

    def _retry_request(self, func, max_retries=3, delay=1):
        """Повторные попытки с задержкой"""
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                error_msg = str(e).lower()
                if "429" in error_msg or "too many requests" in error_msg or "rate limit" in error_msg:
                    if attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt)
                        print(f"⏳ {self.address[:4]}...{self.address[-4:]} лимит запросов, ждем {wait_time}с...")
                        time.sleep(wait_time)
                        continue
                raise e
        return None

    def _safe_web3_call(self, w3_instance, method_name, *args, **kwargs):
        """Безопасный вызов Web3 методов с retry"""
        def make_call():
            method = getattr(w3_instance.eth, method_name)
            return method(*args, **kwargs)
        
        return self._retry_request(make_call, max_retries=3, delay=1)

    def _validate_proxy_format(self, proxy: str) -> bool:
        """Проверка формата прокси"""
        try:
            if proxy.startswith(('http://', 'https://', 'socks5://', 'socks4://')):
                return True
                
            parts = proxy.split(':')
            if len(parts) in [2, 4]:
                ip, port = parts[0], parts[1]
                int(port)
                return True
            return False
        except:
            return False

    def _setup_web3(self):
        """Настройка подключения к Jovay"""
        if self.proxy and not self._validate_proxy_format(self.proxy):
            print(f"⚠️ {self.address[:4]}...{self.address[-4:]} неверный формат прокси: {self.proxy}")
            self.proxy = None
        
        # Jovay RPC
        jovay_public_rpc = "https://api.zan.top/public/jovay-testnet"
        
        if self.api_key and self.api_key != "9d9d6aa530b64877be75a16288a7eadb":
            jovay_rpc = f"https://api.zan.top/node/v1/jovay/testnet/{self.api_key}"
            print(f"🔑 {self.address[:4]}...{self.address[-4:]} используем API ключ: {self.api_key[:8]}...")
        else:
            jovay_rpc = jovay_public_rpc
            print(f"🔓 {self.address[:4]}...{self.address[-4:]} используем публичный RPC")
        
        # Настройка с прокси
        if self.proxy:
            session = requests.Session()
            if self.proxy.startswith(('http://', 'https://', 'socks5://', 'socks4://')):
                proxy_dict = {'http': self.proxy, 'https': self.proxy}
            else:
                parts = self.proxy.split(':')
                if len(parts) == 4:
                    proxy_url = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
                elif len(parts) == 2:
                    proxy_url = f"http://{parts[0]}:{parts[1]}"
                else:
                    proxy_url = None
                
                if proxy_url:
                    proxy_dict = {'http': proxy_url, 'https': proxy_url}
                else:
                    proxy_dict = {}
            
            if proxy_dict:
                session.proxies.update(proxy_dict)
                
            try:
                self.jovay_w3 = Web3(Web3.HTTPProvider(jovay_rpc, session=session))
                if self.jovay_w3.is_connected():
                    chain_id = self.jovay_w3.eth.chain_id
                    print(f"🌐 {self.address[:4]}...{self.address[-4:]} подключен к Jovay (Chain ID: {chain_id})")
                else:
                    raise Exception("Не удалось подключиться")
            except Exception as e:
                print(f"⚠️ {self.address[:4]}...{self.address[-4:]} прокси ошибка, fallback к публичному")
                self.jovay_w3 = Web3(Web3.HTTPProvider(jovay_public_rpc))
        else:
            try:
                self.jovay_w3 = Web3(Web3.HTTPProvider(jovay_rpc))
                if self.jovay_w3.is_connected():
                    chain_id = self.jovay_w3.eth.chain_id
                    print(f"🔗 {self.address[:4]}...{self.address[-4:]} подключен к Jovay (Chain ID: {chain_id})")
                else:
                    raise Exception("Не удалось подключиться")
            except Exception as e:
                print(f"⚠️ {self.address[:4]}...{self.address[-4:]} RPC ошибка, fallback к публичному")
                self.jovay_w3 = Web3(Web3.HTTPProvider(jovay_public_rpc))

    def _setup_sepolia_web3(self):
        """Настройка подключения к Sepolia с несколькими RPC"""
        # Список альтернативных RPC для Sepolia
        sepolia_rpcs = [
            "https://sepolia.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161",
            "https://rpc.sepolia.org",
            "https://sepolia.gateway.tenderly.co",
            "https://ethereum-sepolia-rpc.publicnode.com",
            "https://1rpc.io/sepolia",
            "https://sepolia.drpc.org"
        ]
        
        self.sepolia_w3 = None
        
        for rpc_url in sepolia_rpcs:
            try:
                print(f"🔍 {self.address[:4]}...{self.address[-4:]} тестируем Sepolia RPC: {rpc_url.split('/')[2]}")
                
                if self.proxy:
                    session = requests.Session()
                    if self.proxy.startswith(('http://', 'https://', 'socks5://', 'socks4://')):
                        proxy_dict = {'http': self.proxy, 'https': self.proxy}
                    else:
                        parts = self.proxy.split(':')
                        if len(parts) == 4:
                            proxy_url = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
                        elif len(parts) == 2:
                            proxy_url = f"http://{parts[0]}:{parts[1]}"
                        else:
                            proxy_url = None
                        
                        if proxy_url:
                            proxy_dict = {'http': proxy_url, 'https': proxy_url}
                        else:
                            proxy_dict = {}
                    
                    if proxy_dict:
                        session.proxies.update(proxy_dict)
                        
                    temp_w3 = Web3(Web3.HTTPProvider(rpc_url, session=session))
                else:
                    temp_w3 = Web3(Web3.HTTPProvider(rpc_url))
                
                # Тестируем подключение
                if temp_w3.is_connected():
                    # Дополнительная проверка - получаем номер блока
                    block_number = temp_w3.eth.block_number
                    if block_number > 0:
                        self.sepolia_w3 = temp_w3
                        print(f"🔗 {self.address[:4]}...{self.address[-4:]} подключен к Sepolia ({rpc_url.split('/')[2]}, блок: {block_number})")
                        break
                    else:
                        print(f"⚠️ {self.address[:4]}...{self.address[-4:]} RPC отвечает, но блоки недоступны")
                else:
                    print(f"⚠️ {self.address[:4]}...{self.address[-4:]} RPC недоступен")
                    
            except Exception as e:
                print(f"⚠️ {self.address[:4]}...{self.address[-4:]} ошибка RPC {rpc_url.split('/')[2]}: {type(e).__name__}")
                continue
        
        if self.sepolia_w3 is None:
            print(f"❌ {self.address[:4]}...{self.address[-4:]} не удалось подключиться ни к одному Sepolia RPC")
        
        # Небольшая задержка после подключения
        time.sleep(1)

    def get_balances(self) -> Dict[str, float]:
        """Получение балансов с задержками - ИСПРАВЛЕНО"""
        balances = {'sepolia': 0.0, 'jovay': 0.0}
        
        # Sepolia баланс с дополнительными проверками
        try:
            if self.sepolia_w3 and self.sepolia_w3.is_connected():
                print(f"💰 {self.address[:4]}...{self.address[-4:]} запрашиваем баланс Sepolia...")
                sepolia_balance_wei = self._safe_web3_call(self.sepolia_w3, 'get_balance', self.address)
                if sepolia_balance_wei is not None:
                    balances['sepolia'] = float(Web3.from_wei(sepolia_balance_wei, 'ether'))
                    print(f"💰 {self.address[:4]}...{self.address[-4:]} Sepolia баланс получен: {balances['sepolia']:.6f} ETH")
                else:
                    print(f"⚠️ {self.address[:4]}...{self.address[-4:]} Sepolia баланс = None")
            else:
                print(f"⚠️ {self.address[:4]}...{self.address[-4:]} Sepolia не подключен для получения баланса")
        except Exception as e:
            print(f"⚠️ {self.address[:4]}...{self.address[-4:]} ошибка баланса Sepolia: {type(e).__name__} - {str(e)[:50]}")
        
        # Jovay баланс
        try:
            if self.jovay_w3 and self.jovay_w3.is_connected():
                jovay_balance_wei = self._safe_web3_call(self.jovay_w3, 'get_balance', self.address)
                if jovay_balance_wei is not None:
                    balances['jovay'] = float(Web3.from_wei(jovay_balance_wei, 'ether'))
                else:
                    balances['jovay'] = 0.0
        except Exception as e:
            print(f"⚠️ {self.address[:4]}...{self.address[-4:]} ошибка баланса Jovay: {e}")
            balances['jovay'] = 0.0
        
        return balances

    def claim_faucet(self) -> bool:
        """Получение токенов через фаучет Sepolia"""
        try:
            print(f"💧 {self.address[:4]}...{self.address[-4:]} получение из фаучета...")
            
            # Список различных фаучетов Sepolia
            faucets = [
                {
                    "name": "Sepolia PoW Faucet",
                    "url": "https://sepolia-faucet.pk910.de/api/startSession",
                    "method": "POST",
                    "data": {"addr": self.address}
                },
                {
                    "name": "Alchemy Faucet", 
                    "url": f"https://sepoliafaucet.com/api/claimTokens",
                    "method": "POST",
                    "data": {"walletAddress": self.address, "captcha": "skip"}
                },
                {
                    "name": "QuickNode Faucet",
                    "url": "https://faucet.quicknode.com/ethereum/sepolia",
                    "method": "POST", 
                    "data": {"wallet": self.address}
                }
            ]
            
            # Настройка сессии с прокси
            if self.proxy:
                session = requests.Session()
                if self.proxy.startswith(('http://', 'https://', 'socks5://', 'socks4://')):
                    proxy_dict = {'http': self.proxy, 'https': self.proxy}
                else:
                    parts = self.proxy.split(':')
                    if len(parts) == 4:
                        proxy_url = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
                    elif len(parts) == 2:
                        proxy_url = f"http://{parts[0]}:{parts[1]}"
                    else:
                        proxy_url = None
                    
                    if proxy_url:
                        proxy_dict = {'http': proxy_url, 'https': proxy_url}
                    else:
                        proxy_dict = {}
                
                if proxy_dict:
                    session.proxies.update(proxy_dict)
            else:
                session = requests.Session()
            
            # Заголовки
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin'
            }
            
            # Пробуем каждый фаучет
            for faucet in faucets:
                try:
                    print(f"💧 {self.address[:4]}...{self.address[-4:]} пробуем {faucet['name']}...")
                    
                    def make_faucet_request():
                        if faucet['method'] == 'POST':
                            response = session.post(
                                faucet['url'], 
                                json=faucet['data'], 
                                headers=headers, 
                                timeout=30
                            )
                        else:
                            response = session.get(
                                faucet['url'], 
                                params=faucet['data'], 
                                headers=headers, 
                                timeout=30
                            )
                        return response
                    
                    response = self._retry_request(make_faucet_request, max_retries=2, delay=3)
                    
                    if response is None:
                        print(f"💧 {self.address[:4]}...{self.address[-4:]} {faucet['name']} недоступен")
                        continue
                    
                    print(f"💧 {self.address[:4]}...{self.address[-4:]} {faucet['name']} ответ: {response.status_code}")
                    
                    if response.status_code == 200:
                        try:
                            result = response.json()
                            print(f"💧 {self.address[:4]}...{self.address[-4:]} {faucet['name']} JSON: {str(result)[:100]}")
                            
                            # Проверяем различные форматы успешного ответа
                            success_indicators = ['success', 'ok', 'status', 'result']
                            is_success = False
                            
                            for indicator in success_indicators:
                                if indicator in result:
                                    if result[indicator] in [True, 'success', 'ok', 200, '200']:
                                        is_success = True
                                        break
                            
                            # Если нет явных индикаторов, считаем успехом если нет ошибок
                            if not is_success and 'error' not in result and 'Error' not in result:
                                is_success = True
                            
                            if is_success:
                                self.stats['faucet'] += 1
                                print(f"💧 {self.address[:4]}...{self.address[-4:]} {faucet['name']} ✅")
                                return True
                            else:
                                error_msg = result.get('message', result.get('error', 'неизвестная ошибка'))
                                print(f"💧 {self.address[:4]}...{self.address[-4:]} {faucet['name']} отклонен: {error_msg}")
                                
                        except json.JSONDecodeError:
                            # Если не JSON, проверяем текст ответа
                            response_text = response.text.lower()
                            if any(word in response_text for word in ['success', 'sent', 'queued', 'processing']):
                                self.stats['faucet'] += 1
                                print(f"💧 {self.address[:4]}...{self.address[-4:]} {faucet['name']} ✅ (text response)")
                                return True
                            else:
                                print(f"💧 {self.address[:4]}...{self.address[-4:]} {faucet['name']} неожиданный ответ: {response.text[:100]}")
                    else:
                        print(f"💧 {self.address[:4]}...{self.address[-4:]} {faucet['name']} HTTP ошибка: {response.status_code}")
                        
                except Exception as e:
                    print(f"💧 {self.address[:4]}...{self.address[-4:]} {faucet['name']} ошибка: {type(e).__name__}")
                    continue
            
            print(f"💧 {self.address[:4]}...{self.address[-4:]} все фаучеты неудачны")
            return False
                
        except Exception as e:
            print(f"💧 {self.address[:4]}...{self.address[-4:]} общая ошибка фаучета: {type(e).__name__}")
            return False

    def bridge_tokens(self, amount: float) -> bool:
        """Бридж токенов через официальный мост Jovay"""
        try:
            print(f"🌉 {self.address[:4]}...{self.address[-4:]} бридж {amount:.4f} ETH...")
            
            if not self.sepolia_w3 or not self.sepolia_w3.is_connected():
                print(f"🌉 {self.address[:4]}...{self.address[-4:]} нет подключения к Sepolia")
                return False
            
            # Проверяем баланс в Sepolia
            balances = self.get_balances()
            sepolia_balance = balances.get('sepolia', 0.0)
            
            if sepolia_balance < amount:
                print(f"🌉 {self.address[:4]}...{self.address[-4:]} недостаточно ETH в Sepolia: {sepolia_balance:.6f}")
                return False
            
            # Адрес официального моста Jovay в Sepolia
            bridge_contract_address = "0x940eFB877281884699176892B02A3db49f29CDE8"  # Реальный адрес моста
            
            # Расширенный ABI для моста Jovay
            bridge_abi = [
                {
                    "inputs": [],
                    "name": "depositETH",
                    "outputs": [],
                    "stateMutability": "payable",
                    "type": "function"
                },
                {
                    "inputs": [],
                    "name": "bridge",
                    "outputs": [],
                    "stateMutability": "payable",
                    "type": "function"
                },
                {
                    "inputs": [
                        {"internalType": "address", "name": "to", "type": "address"},
                        {"internalType": "uint256", "name": "amount", "type": "uint256"}
                    ],
                    "name": "bridgeETH",
                    "outputs": [],
                    "stateMutability": "payable",
                    "type": "function"
                }
            ]
            
            # Создаем контракт
            bridge_contract = self.sepolia_w3.eth.contract(
                address=Web3.to_checksum_address(bridge_contract_address),
                abi=bridge_abi
            )
            
            # Получаем nonce
            nonce = self._safe_web3_call(self.sepolia_w3, 'get_transaction_count', self.address)
            if nonce is None:
                print(f"🌉 {self.address[:4]}...{self.address[-4:]} не удалось получить nonce")
                return False
            
            # Получаем gas price
            try:
                gas_price = self.sepolia_w3.eth.gas_price
                if gas_price is None or gas_price == 0:
                    gas_price = Web3.to_wei('20', 'gwei')  # Fallback для Sepolia
            except:
                gas_price = Web3.to_wei('20', 'gwei')
            
            # Вычисляем amount в wei
            amount_wei = Web3.to_wei(amount, 'ether')
            gas_limit = 150000  # Увеличен лимит для моста
            
            # Проверяем достаточность средств (amount + gas)
            total_needed = amount_wei + (gas_price * gas_limit)
            sepolia_balance_wei = Web3.to_wei(sepolia_balance, 'ether')
            
            if sepolia_balance_wei < total_needed:
                print(f"🌉 {self.address[:4]}...{self.address[-4:]} недостаточно для газа + amount")
                return False
            
            # Пробуем разные методы моста
            bridge_methods = [
                ("depositETH", lambda: bridge_contract.functions.depositETH()),
                ("bridge", lambda: bridge_contract.functions.bridge()),
                ("bridgeETH", lambda: bridge_contract.functions.bridgeETH(self.address, amount_wei))
            ]
            
            for method_name, method_func in bridge_methods:
                try:
                    print(f"🌉 {self.address[:4]}...{self.address[-4:]} пробуем метод {method_name}...")
                    
                    # Строим транзакцию
                    if method_name == "bridgeETH":
                        # Для bridgeETH не передаем value, сумма в параметрах
                        transaction = method_func().build_transaction({
                            'chainId': self.sepolia_chain_id,
                            'gas': gas_limit,
                            'gasPrice': gas_price,
                            'nonce': nonce,
                        })
                    else:
                        # Для depositETH и bridge передаем value
                        transaction = method_func().build_transaction({
                            'chainId': self.sepolia_chain_id,
                            'gas': gas_limit,
                            'gasPrice': gas_price,
                            'nonce': nonce,
                            'value': amount_wei,
                        })
                    
                    # Отправляем транзакцию
                    def send_bridge_transaction():
                        signed_txn = self.sepolia_w3.eth.account.sign_transaction(transaction, self.private_key)
                        return self.sepolia_w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                    
                    tx_hash = self._retry_request(send_bridge_transaction, max_retries=3, delay=2)
                    if tx_hash is None:
                        print(f"🌉 {self.address[:4]}...{self.address[-4:]} не удалось отправить транзакцию {method_name}")
                        continue
                    
                    print(f"🌉 {self.address[:4]}...{self.address[-4:]} бридж {method_name} отправлен: {tx_hash.hex()[:10]}...")
                    
                    # Ждем подтверждение
                    def wait_bridge_receipt():
                        return self.sepolia_w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
                    
                    receipt = self._retry_request(wait_bridge_receipt, max_retries=2, delay=10)
                    if receipt is None:
                        print(f"🌉 {self.address[:4]}...{self.address[-4:]} таймаут ожидания бриджа {method_name}")
                        continue
                    
                    if receipt.status == 1:
                        self.stats['bridges'] += 1
                        gas_used = Web3.from_wei(gas_price * receipt.gasUsed, 'ether')
                        print(f"🌉 {self.address[:4]}...{self.address[-4:]} бридж {method_name} ✅ (газ: {gas_used:.6f} ETH)")
                        return True
                    else:
                        print(f"🌉 {self.address[:4]}...{self.address[-4:]} бридж {method_name} провален")
                        continue
                        
                except Exception as e:
                    print(f"🌉 {self.address[:4]}...{self.address[-4:]} ошибка метода {method_name}: {type(e).__name__}")
                    continue
            
            print(f"🌉 {self.address[:4]}...{self.address[-4:]} все методы бриджа неудачны")
            return False
                
        except Exception as e:
            print(f"🌉 {self.address[:4]}...{self.address[-4:]} общая ошибка бриджа: {type(e).__name__}: {str(e)[:50]}")
            return False

    def deploy_contract(self, contract_type: str) -> bool:
        """Деплой контракта с МИНИМАЛЬНЫМИ требованиями - ИСПРАВЛЕНО"""
        if not SOLC_AVAILABLE:
            print(f"📦 {self.address[:4]}...{self.address[-4:]} solcx не установлен")
            return False
            
        try:
            if not self.jovay_w3 or not self.jovay_w3.is_connected():
                print(f"📦 {self.address[:4]}...{self.address[-4:]} нет подключения к Jovay")
                return False
                
            # ИСПРАВЛЕНО: получаем балансы корректно
            balances = self.get_balances()
            current_balance = balances.get('jovay', 0.0)
            
            # ОЧЕНЬ НИЗКИЕ требования
            min_balance = 0.0002  # Минимум для старта
            if current_balance < min_balance:
                print(f"📦 {self.address[:4]}...{self.address[-4:]} недостаточно ETH: {current_balance:.6f}")
                return False
            
            # Настройка Solidity
            try:
                install_solc('0.8.20')
                set_solc_version('0.8.20')
            except Exception as e:
                print(f"📦 {self.address[:4]}...{self.address[-4:]} Solidity предупреждение: {type(e).__name__}")
                pass
            
            # Выбор контракта
            contracts = {
                "token": self._get_smart_contract(),
                "nft": self._get_nft_contract(),
                "staking": self._get_storage_contract()
            }
            
            contract_source = contracts.get(contract_type, contracts["token"])
            
            # Компиляция
            try:
                compiled_sol = compile_source(contract_source)
                contract_name = list(compiled_sol.keys())[0].split(':')[1]
                contract_interface = compiled_sol[f'<stdin>:{contract_name}']
            except Exception as e:
                print(f"📦 {self.address[:4]}...{self.address[-4:]} ошибка компиляции: {type(e).__name__}")
                return False
            
            contract = self.jovay_w3.eth.contract(
                abi=contract_interface['abi'],
                bytecode=contract_interface['bin']
            )
            
            # Получаем nonce
            nonce = self._safe_web3_call(self.jovay_w3, 'get_transaction_count', self.address)
            if nonce is None:
                print(f"📦 {self.address[:4]}...{self.address[-4:]} не удалось получить nonce")
                return False
            
            time.sleep(1.0)
            
            # ИСПРАВЛЕНО: правильное получение gas price
            try:
                gas_price = self.jovay_w3.eth.gas_price  # Убрали лишние скобки ()
                if gas_price is None or gas_price == 0:
                    gas_price = Web3.to_wei('0.5', 'gwei')  # ОЧЕНЬ НИЗКИЙ fallback
                    print(f"📦 {self.address[:4]}...{self.address[-4:]} используем fallback gas: 0.5 gwei")
                else:
                    print(f"📦 {self.address[:4]}...{self.address[-4:]} gas price: {Web3.from_wei(gas_price, 'gwei'):.2f} gwei")
            except Exception as e:
                print(f"📦 {self.address[:4]}...{self.address[-4:]} ошибка gas price, используем 0.5 gwei")
                gas_price = Web3.to_wei('0.5', 'gwei')
            
            # НИЗКИЙ лимит газа
            gas_limit = 800000  # ЗНАЧИТЕЛЬНО УМЕНЬШЕН
            
            # Проверка стоимости БЕЗ запаса
            actual_cost = Web3.from_wei(gas_price * gas_limit, 'ether')
            
            if current_balance < float(actual_cost):
                print(f"📦 {self.address[:4]}...{self.address[-4:]} {contract_type} недостаточно для газа:")
                print(f"    Нужно: {actual_cost:.6f} ETH")
                print(f"    Есть: {current_balance:.6f} ETH")
                print(f"    Gas: {Web3.from_wei(gas_price, 'gwei'):.2f} gwei, лимит: {gas_limit}")
                return False
            
            # Строим транзакцию
            try:
                transaction = contract.constructor().build_transaction({
                    'chainId': self.jovay_chain_id,
                    'gas': gas_limit,
                    'gasPrice': gas_price,
                    'nonce': nonce,
                })
            except Exception as e:
                print(f"📦 {self.address[:4]}...{self.address[-4:]} ошибка build_transaction: {type(e).__name__}")
                return False
            
            # Отправка транзакции
            def send_transaction():
                signed_txn = self.jovay_w3.eth.account.sign_transaction(transaction, self.private_key)
                return self.jovay_w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            tx_hash = self._retry_request(send_transaction, max_retries=3, delay=2)
            if tx_hash is None:
                print(f"📦 {self.address[:4]}...{self.address[-4:]} не удалось отправить транзакцию")
                return False
            
            print(f"📦 {self.address[:4]}...{self.address[-4:]} {contract_type} отправлен: {tx_hash.hex()[:10]}...")
            
            # Ждем подтверждение
            def wait_receipt():
                return self.jovay_w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
            
            receipt = self._retry_request(wait_receipt, max_retries=2, delay=5)
            if receipt is None:
                print(f"📦 {self.address[:4]}...{self.address[-4:]} таймаут ожидания")
                return False
            
            if receipt.status == 1:
                self.stats['contracts'] += 1
                actual_cost_used = Web3.from_wei(gas_price * receipt.gasUsed, 'ether')
                print(f"📦 {self.address[:4]}...{self.address[-4:]} {contract_type} ✅ деплой: {receipt.contractAddress[:6]}...{receipt.contractAddress[-4:]} (газ: {actual_cost_used:.6f} ETH)")
                return True
            else:
                print(f"📦 {self.address[:4]}...{self.address[-4:]} {contract_type} транзакция провалена")
                return False
                
        except Exception as e:
            self.stats['errors'] += 1
            print(f"📦 {self.address[:4]}...{self.address[-4:]} {contract_type} ошибка: {type(e).__name__}: {str(e)[:50]}")
            return False

    def _get_nft_contract(self) -> str:
        """Максимально упрощенный NFT контракт"""
        random_id = random.randint(1000, 9999)
        return f"""
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract MiniNFT_{random_id} {{
    mapping(uint256 => address) public owners;
    uint256 public count = 0;
    
    constructor() {{}}
    
    function mint() public {{
        count++;
        owners[count] = msg.sender;
    }}
}}
"""

    def _get_storage_contract(self) -> str:
        """Максимально упрощенный storage контракт"""
        random_id = random.randint(1000, 9999)
        return f"""
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract MiniStorage_{random_id} {{
    uint256 public data;
    
    constructor() {{}}
    
    function set(uint256 _data) public {{
        data = _data;
    }}
}}
"""

    def _get_smart_contract(self) -> str:
        """Максимально упрощенный токен контракт"""
        random_id = random.randint(1000, 9999)
        return f"""
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract MiniToken_{random_id} {{
    mapping(address => uint256) public balance;
    
    constructor() {{
        balance[msg.sender] = 1000;
    }}
    
    function transfer(address to, uint256 amount) public {{
        balance[msg.sender] -= amount;
        balance[to] += amount;
    }}
}}
"""

    def run_automation(self, config: Config) -> Dict[str, int]:
        """Запуск полного цикла: фаучет → бридж → деплой - ИСПРАВЛЕНО"""
        print(f"▶️ {self.address[:4]}...{self.address[-4:]} старт")
        
        # Получаем начальные балансы
        balances = self.get_balances()
        print(f"💰 {self.address[:4]}...{self.address[-4:]} начальные балансы:")
        print(f"    Sepolia: {balances['sepolia']:.6f} ETH")
        print(f"    Jovay: {balances['jovay']:.6f} ETH")
        
        # Шаг 1: Фаучет ВКЛЮЧЕН
        print(f"💧 {self.address[:4]}...{self.address[-4:]} попытка получить из фаучета...")
        if self.claim_faucet():
            print(f"💧 {self.address[:4]}...{self.address[-4:]} фаучет успешен")
            pause_time = random.uniform(*config.pause_after_faucet)
            print(f"💧 {self.address[:4]}...{self.address[-4:]} пауза после фаучета {pause_time:.0f}с")
            time.sleep(pause_time)
            
            # Обновляем балансы после фаучета
            balances = self.get_balances()
        else:
            print(f"💧 {self.address[:4]}...{self.address[-4:]} фаучет неудачен")
        
        # Шаг 2: Бридж ВКЛЮЧЕН
        if config.bridge_count > 0:
            sepolia_balance = balances.get('sepolia', 0.0)
            if sepolia_balance > 0.01:  # Минимум для бриджа
                print(f"🌉 {self.address[:4]}...{self.address[-4:]} начинаем бридж...")
                
                for i in range(config.bridge_count):
                    # Случайная сумма для бриджа
                    bridge_amount = random.uniform(config.bridge_amount_min, config.bridge_amount_max)
                    
                    # Проверяем текущий баланс
                    current_sepolia = self.get_balances().get('sepolia', 0.0)
                    if current_sepolia < bridge_amount + 0.005:  # +0.005 для газа
                        print(f"🌉 {self.address[:4]}...{self.address[-4:]} недостаточно для бриджа {i+1}")
                        break
                    
                    if self.bridge_tokens(bridge_amount):
                        print(f"🌉 {self.address[:4]}...{self.address[-4:]} бридж {i+1} ✅")
                    else:
                        print(f"🌉 {self.address[:4]}...{self.address[-4:]} бридж {i+1} ❌")
                        self.stats['errors'] += 1
                    
                    if i < config.bridge_count - 1:
                        pause_time = random.uniform(*config.pause_after_bridge)
                        print(f"🌉 {self.address[:4]}...{self.address[-4:]} пауза {pause_time:.0f}с")
                        time.sleep(pause_time)
            else:
                print(f"🌉 {self.address[:4]}...{self.address[-4:]} недостаточно ETH в Sepolia для бриджа")
        else:
            print(f"🌉 {self.address[:4]}...{self.address[-4:]} бридж отключен в конфиге")
        
        # Шаг 3: Деплой контрактов
        current_jovay_balance = self.get_balances().get('jovay', 0.0)  # Обновляем баланс после бриджа
        min_balance_for_deploy = 0.0002  # ОЧЕНЬ НИЗКИЙ минимум
        
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
                    current_balance_check = self.get_balances().get('jovay', 0.0)  # ИСПРАВЛЕНО
                    if current_balance_check < 0.0001:  # ОЧЕНЬ НИЗКИЙ минимум
                        print(f"📦 {self.address[:4]}...{self.address[-4:]} остановка - мало ETH: {current_balance_check:.6f}")
                        break
                        
                    if self.deploy_contract(contract_type):
                        print(f"📦 {self.address[:4]}...{self.address[-4:]} {contract_type} ✅")
                    else:
                        print(f"📦 {self.address[:4]}...{self.address[-4:]} {contract_type} ❌")
                    
                    if i < deploy_per_type - 1 or contract_type != contract_types[-1]:
                        pause_time = random.uniform(*config.pause_after_deploy)
                        print(f"📦 {self.address[:4]}...{self.address[-4:]} пауза {pause_time:.0f}с")
                        time.sleep(pause_time)
        else:
            print(f"❌ {self.address[:4]}...{self.address[-4:]} недостаточно ETH для деплоя")
            print(f"💡 {self.address[:4]}...{self.address[-4:]} получите токены: https://zan.top/faucet/jovay")
        
        # Финальные балансы
        final_balances = self.get_balances()
        
        print(f"🏁 {self.address[:4]}...{self.address[-4:]} завершен")
        print(f"   💰 Sepolia: {balances['sepolia']:.6f} → {final_balances['sepolia']:.6f}")
        print(f"   💰 Jovay: {balances['jovay']:.6f} → {final_balances['jovay']:.6f}")
        print(f"   📊 Операции: 💧{self.stats['faucet']} 🌉{self.stats['bridges']} 📦{self.stats['contracts']} ❌{self.stats['errors']}")
        
        return self.stats


class MultiAccountManager:
    """Менеджер аккаунтов - ИСПРАВЛЕНО"""
    
    def __init__(self, config: Config):
        self.config = config
        self.private_keys = []
        self.api_keys = []
        self.proxy_assignments = []
        self.proxies = []
        self.load_accounts()

    def load_accounts(self):
        """Загрузка данных аккаунтов с API ключами из файла"""
        # Приватные ключи
        try:
            with open("private_keys.txt", 'r', encoding='utf-8') as f:
                self.private_keys = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except FileNotFoundError:
            print("❌ Файл private_keys.txt не найден")
            self.private_keys = []
        
        # API ключи из файла
        try:
            with open("api_keys.txt", 'r', encoding='utf-8') as f:
                api_lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                self.api_keys = []
                
                for line in api_lines:
                    if not line.startswith('#') and line != "9d9d6aa530b64877be75a16288a7eadb":
                        self.api_keys.append(line)
                    elif line == "9d9d6aa530b64877be75a16288a7eadb":
                        self.api_keys.append(line)
                        
                print(f"📋 Загружено API ключей из файла: {len(self.api_keys)}")
                
        except FileNotFoundError:
            print("⚠️ Файл api_keys.txt не найден, создаем с примером...")
            self.api_keys = []
        except Exception as e:
            print(f"⚠️ Ошибка чтения api_keys.txt: {e}")
            self.api_keys = []
        
        # Дополняем API ключи до количества кошельков
        default_api = "9d9d6aa530b64877be75a16288a7eadb"
        while len(self.api_keys) < len(self.private_keys):
            self.api_keys.append(default_api)
            
        print(f"🔑 Итого API ключей: {len(self.api_keys)} (для {len(self.private_keys)} кошельков)")
        
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

    def process_account(self, account_index: int) -> Dict[str, int]:
        """Обработка одного аккаунта"""
        try:
            private_key = self.private_keys[account_index]
            api_key = self.api_keys[account_index] if account_index < len(self.api_keys) else self.api_keys[0]
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

    def _print_final_stats(self, stats: Dict[str, int]):
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
            "# API ключи ZAN для каждого кошелька",
            "# Порядок должен совпадать с private_keys.txt",
            "# Получите персональные ключи на https://zan.top",
            "# Формат: один ключ на строку",
            "",
            "# Примеры (замените на свои):",
            "# abc123def456ghi789jkl012mno345pqr678stu901",
            "# def456ghi789jkl012mno345pqr678stu901vwx234",
            "",
            "# Дефолтный ключ (публичный RPC, медленнее):",
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
            "# 192.168.1.1:8080:username:password",
            ""
        ]
    }
    
    for filename, content in files_to_create.items():
        if not os.path.exists(filename):
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))
            print(f"📄 Создан файл: {filename}")


def main():
    """Основная функция"""
    print("🚀 JOVAY NETWORK AUTOMATION - ПОЛНАЯ ВЕРСИЯ")
    print("=" * 50)
    
    create_example_files()
    
    # Конфигурация с ВКЛЮЧЕННЫМИ фаучетом и бриджем
    config = Config(
        max_threads=10,
        bridge_count=2,  # ВКЛЮЧЕН
        deploy_count=3,
        bridge_amount_min=0.001,
        bridge_amount_max=0.005,
        pause_between_accounts=(15, 30),    
        pause_between_operations=(5, 10),   
        pause_after_bridge=(60, 120),       
        pause_after_deploy=(8, 15),         
        pause_after_faucet=(30, 60),        
        rpc_delay=1.0                       
    )
    
    manager = MultiAccountManager(config)
    
    if not manager.private_keys:
        print("❌ Добавьте приватные ключи в private_keys.txt")
        print("💡 Создайте файл private_keys.txt и добавьте приватные ключи")
        return
    
    print(f"\n🔧 ПАРАМЕТРЫ ЗАПУСКА:")
    print(f"📱 Найдено кошельков: {len(manager.private_keys)}")
    print(f"🔑 API ключей: {len(manager.api_keys)}")
    print(f"🌐 Прокси: {len(manager.proxies)}")
    print(f"💧 Фаучет: ВКЛЮЧЕН")
    print(f"🌉 Бридж: ВКЛЮЧЕН ({config.bridge_count} операций)")
    print(f"💰 Сумма бриджа: {config.bridge_amount_min}-{config.bridge_amount_max} ETH")
    print(f"📦 Деплой: {config.deploy_count} контрактов")
    print(f"💰 Минимум для деплоя: 0.0002 ETH")
    print(f"⛽ Gas price: автоматически")
    print(f"🔥 Gas limit: 800,000 (оптимизированный)")
    print(f"📦 Контракты: максимально упрощенные")
    
    print(f"\n📋 РЕЖИМЫ ЗАПУСКА:")
    print("1. 🔄 Последовательно (рекомендуется)")
    print("2. ⚡ Параллельно")
    
    choice = input("\nВыбор (1-2): ").strip()
    
    if choice == "1":
        manager.run_sequential()
    elif choice == "2":
        manager.run_multi_threaded()
    else:
        print("❌ Неверный выбор, используем последовательный режим")
        manager.run_sequential()


if __name__ == "__main__":
    main()