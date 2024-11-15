import json
from os import path
from tonsdk.contract.wallet import Wallets, WalletVersionEnum


def generate_wallet(config_path: str) -> tuple[str, dict]:
    """
    Генерирует новый TON кошелек и возвращает кортеж (адрес, полные данные)
    """
    mnemonics, public_key, private_key, wallet = Wallets.create(WalletVersionEnum.v4r2, workchain=0)
    wallet_address = wallet.address.to_string(True, True, False)
    
    wallet_data = {
        "address": wallet_address,
        "mnemonic_phrase": " ".join(mnemonics),
        "public_key": public_key.hex(),
        "private_key": private_key.hex()
    }

    return wallet_address, wallet_data
