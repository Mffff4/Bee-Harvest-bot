from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    API_ID: int
    API_HASH: str
    REF_ID: str = "6344320439"
    USE_PROXY_FROM_FILE: bool = False
    VALIDATE_PROXIES: bool = True
    PROXY_TYPES: list[str] = ["socks5", "socks4", "http", "https"]
    PROXY_TIMEOUT: int = 30
    PROXY_CHECK_URL: str = "http://api.ipify.org?format=json"

    DELAY_BEFORE_START: list[int] = [1, 5]
    DELAY_BETWEEN_ACTIONS: list[int] = [1, 3]
    DELAY_BETWEEN_SPINS: list[int] = [6, 8]
    DELAY_BETWEEN_CYCLES: list[int] = [300, 54000]

    MAX_RETRIES: int = 10
    RETRY_DELAY: list[int] = [3, 10]
    REQUEST_TIMEOUT: list[int] = [60, 54000]

    LOGGING_LEVEL: str = "INFO"
    ENABLE_RICH_LOGGING: bool = True
    LOG_USER_AGENT: bool = True
    LOG_PROXY: bool = True

    SPIN_AMOUNTS: list[int] = [1000, 500, 150, 50, 10, 5, 3, 1]

    INITIAL_BEE_TARGET: int = 84
    BEE_STEP: int = 4
    BEE_QUALITY_STEP: int = 1
    BEEHIVE_STEP: int = 1
    MIN_HONEY_BALANCE: float = 1.0

    COMBO_FILE: str = "combo.json"
    COMBO_ITEMS_COUNT: int = 4

    MIN_POOL_AMOUNT: float = 1.0
    POOL_RESERVE: float = 500.0
    POOL_SEND_PERCENT: float = 50
    MIN_SQUAD_POOL_AMOUNT: float = 0.1
    
    SQUAD_POOL_RESERVE: float = 100.0
    SQUAD_POOL_SEND_PERCENT: float = 10
    SQUAD_ID: int = 2581
    
    MULTITHREADING: bool = False

    ENABLE_MAIN_POOL: bool = True
    ENABLE_SQUAD_POOL: bool = True

    def __init__(self, **data):
        super().__init__(**data)
        self.MAX_RETRIES = max(1, self.MAX_RETRIES)
        self.PROXY_TIMEOUT = max(1, self.PROXY_TIMEOUT)
        self.RETRY_DELAY[0] = max(1, self.RETRY_DELAY[0])
        self.RETRY_DELAY[1] = max(self.RETRY_DELAY[0], self.RETRY_DELAY[1])
        self.REQUEST_TIMEOUT[0] = max(1, self.REQUEST_TIMEOUT[0])
        self.REQUEST_TIMEOUT[1] = max(self.REQUEST_TIMEOUT[0], self.REQUEST_TIMEOUT[1])
        self.DELAY_BEFORE_START[0] = max(1, self.DELAY_BEFORE_START[0])
        self.DELAY_BEFORE_START[1] = max(self.DELAY_BEFORE_START[0], self.DELAY_BEFORE_START[1])
        self.DELAY_BETWEEN_ACTIONS[0] = max(1, self.DELAY_BETWEEN_ACTIONS[0])
        self.DELAY_BETWEEN_ACTIONS[1] = max(self.DELAY_BETWEEN_ACTIONS[0], self.DELAY_BETWEEN_ACTIONS[1])
        self.DELAY_BETWEEN_SPINS[0] = max(1, self.DELAY_BETWEEN_SPINS[0])
        self.DELAY_BETWEEN_SPINS[1] = max(self.DELAY_BETWEEN_SPINS[0], self.DELAY_BETWEEN_SPINS[1])
        self.DELAY_BETWEEN_CYCLES[0] = max(1, self.DELAY_BETWEEN_CYCLES[0])
        self.DELAY_BETWEEN_CYCLES[1] = max(self.DELAY_BETWEEN_CYCLES[0], self.DELAY_BETWEEN_CYCLES[1])
        self.MIN_POOL_AMOUNT = max(0.1, self.MIN_POOL_AMOUNT)
        self.MIN_SQUAD_POOL_AMOUNT = max(0.1, self.MIN_SQUAD_POOL_AMOUNT)
        self.POOL_RESERVE = max(1, self.POOL_RESERVE)
        self.SQUAD_POOL_RESERVE = max(1, self.SQUAD_POOL_RESERVE)
        self.POOL_SEND_PERCENT = max(1, min(100, self.POOL_SEND_PERCENT))
        self.SQUAD_POOL_SEND_PERCENT = max(1, min(100, self.SQUAD_POOL_SEND_PERCENT))


settings = Settings()
