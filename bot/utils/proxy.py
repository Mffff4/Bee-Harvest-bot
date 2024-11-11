import aiohttp
import asyncio
from typing import Optional, Dict
from better_proxy import Proxy
from bot.config import settings
from bot.utils.logger import logger
from aiohttp import TCPConnector, ClientSession, ClientTimeout

class ProxyManager:
    def __init__(self):
        self.proxies: Dict[str, Optional[str]] = {}
        self.proxy_file = "bot/config/proxies.txt"
        
    def load_proxies(self) -> list[str]:
        """Загружает прокси из файла"""
        try:
            with open(self.proxy_file, 'r') as f:
                proxies = [line.strip() for line in f if line.strip()]
                
            # Проверяем формат каждого прокси
            valid_proxies = []
            for proxy in proxies:
                if '://' not in proxy:
                    logger.warning(f"Invalid proxy format (missing protocol): {proxy}")
                    continue
                protocol = proxy.split('://', 1)[0].lower()
                if protocol not in settings.PROXY_TYPES:
                    logger.warning(f"Unsupported proxy protocol: {protocol}")
                    continue
                valid_proxies.append(proxy)
                
            logger.info(f"Loaded {len(valid_proxies)} proxies from file")
            return valid_proxies
        except FileNotFoundError:
            logger.warning(f"Proxy file {self.proxy_file} not found")
            return []
        except Exception as e:
            logger.error(f"Error loading proxies: {e}")
            return []

    async def check_proxy(self, proxy_str: str) -> bool:
        """Проверяет работоспособность прокси"""
        if not settings.VALIDATE_PROXIES:
            return True
            
        try:
            proxy = Proxy.from_str(proxy_str)
            proxy_url = f"{proxy.protocol}://"
            if proxy.login and proxy.password:
                proxy_url += f"{proxy.login}:{proxy.password}@"
            proxy_url += f"{proxy.host}:{proxy.port}"

            # Сначала пробуем через Telegram API
            try:
                from pyrogram import Client
                client = Client(
                    "proxy_check",
                    api_id=settings.API_ID,
                    api_hash=settings.API_HASH,
                    proxy=dict(
                        scheme=proxy.protocol,
                        hostname=proxy.host,
                        port=proxy.port,
                        username=proxy.login,
                        password=proxy.password
                    ),
                    in_memory=True
                )
                await client.connect()
                await client.disconnect()
                logger.success(f"Proxy {proxy_str} is working (Telegram check)")
                return True
            except Exception as e:
                logger.debug(f"Telegram proxy check failed: {e}")

            # Если Telegram проверка не прошла, пробуем через HTTP
            connector = TCPConnector(verify_ssl=False)
            timeout = ClientTimeout(total=settings.PROXY_TIMEOUT)
            
            async with ClientSession(connector=connector) as session:
                try:
                    # Пробуем через google.com
                    async with session.get(
                        "http://www.google.com",
                        proxy=proxy_url,
                        timeout=timeout,
                        ssl=False
                    ) as response:
                        if response.status == 200:
                            logger.success(f"Proxy {proxy_str} is working (HTTP check)")
                            return True
                except Exception as e:
                    logger.debug(f"HTTP proxy check failed: {e}")
                    
                try:
                    # Пробуем через api.ipify.org
                    async with session.get(
                        settings.PROXY_CHECK_URL,
                        proxy=proxy_url,
                        timeout=timeout,
                        ssl=False
                    ) as response:
                        if response.status == 200:
                            logger.success(f"Proxy {proxy_str} is working (ipify check)")
                            return True
                except Exception as e:
                    logger.debug(f"ipify proxy check failed: {e}")
                    
            # Если все проверки не прошли, но прокси в правильном формате - всё равно пробуем использовать
            if await self.validate_proxy(proxy_str):
                logger.warning(f"Proxy {proxy_str} failed checks but will be used anyway")
                return True
                    
            return False
                    
        except Exception as e:
            logger.warning(f"Proxy {proxy_str} validation failed: {e}")
            return False

    async def validate_proxy(self, proxy_str: str) -> bool:
        """Валидирует формат и тип прокси"""
        try:
            proxy = Proxy.from_str(proxy_str)
            if proxy.protocol not in settings.PROXY_TYPES:
                logger.warning(f"Unsupported proxy type: {proxy.protocol}")
                return False
            return True
        except Exception as e:
            logger.warning(f"Invalid proxy format: {proxy_str} - {e}")
            return False

    async def init_proxies(self):
        """Инициализирует и проверяет прокси"""
        if not settings.USE_PROXY_FROM_FILE:
            return

        raw_proxies = self.load_proxies()
        valid_proxies = []

        for proxy in raw_proxies:
            if await self.validate_proxy(proxy):
                if await self.check_proxy(proxy):
                    valid_proxies.append(proxy)
                else:
                    logger.warning(f"Proxy {proxy} is not working")

        if not valid_proxies:
            logger.warning("No valid proxies found")
            return

        logger.info(f"Loaded {len(valid_proxies)} valid proxies")
        return valid_proxies

    def assign_proxy(self, session_name: str, proxy: Optional[str]):
        """Привязывает прокси к сессии"""
        self.proxies[session_name] = proxy

    def get_proxy(self, session_name: str) -> Optional[str]:
        """Получает прокси для сессии"""
        return self.proxies.get(session_name)

proxy_manager = ProxyManager() 