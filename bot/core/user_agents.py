import random
from typing import Tuple

def generate_user_agent() -> Tuple[str, str]:
    android_versions = [str(i) for i in range(10, 15)]
    chrome_versions = [str(i) for i in range(91, 119)]
    devices = [
        "SM-S23U", "SM-G991B", "RMX2176", "VOG-L29", "LE2101", "ELS-NX9", 
        "IN2010", "IN2013", "M2102K1G", "CPH2185", "22041216G", "2211133C",
        "Pixel 5", "OnePlus 9", "Xiaomi Mi 11", "Oppo Find X3", "Sony Xperia 1",
        "Nokia 8.3", "Huawei P40", "Motorola Edge", "Asus Zenfone 8", "Realme GT"
    ]
    build_ids = [
        "TQ3A.230605.012", "UKQ1.230701.001", "SP1A.210812.016", 
        "MMB29K", "RD1A.201105.003.C1", "SKQ1.220519.001", "NRD90M",
        "RQ3A.210705.001", "SP1A.210812.016", "RQ3A.210705.001",
        "RQ3A.210705.002", "SP1A.210812.017", "TQ3A.230701.001"
    ]
    
    android_ver = random.choice(android_versions)
    chrome_ver = random.choice(chrome_versions)
    device = random.choice(devices)
    build_id = random.choice(build_ids)
    
    user_agent = (
        f"Mozilla/5.0 (Linux; Android {android_ver}; {device} Build/{build_id}) "
        f"AppleWebKit/537.36 (KHTML, like Gecko) "
        f"Chrome/{chrome_ver}.0.{random.randint(1000, 9999)}.{random.randint(100, 999)} "
        "Mobile"
    )
    
    return user_agent, ""

def load_or_generate_user_agent(session_name: str) -> Tuple[str, str]:
    return generate_user_agent()