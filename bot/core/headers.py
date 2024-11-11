def get_headers(user_agent: str, token: str = None) -> dict:
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ru',
        'Connection': 'keep-alive',
        'Host': 'api.beeharvest.life',
        'Origin': 'https://beeharvest.life',
        'Referer': 'https://beeharvest.life/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'User-Agent': user_agent
    }
    
    if token:
        headers['Authorization'] = f'Bearer {token}'
        
    return headers