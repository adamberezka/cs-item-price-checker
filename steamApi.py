import requests

from currencies import currencies


def getSteamItemPrice(app_id, item_hash, currency_id=currencies["PLN"], price_type='lowest_price'):
    price_check_url = f'https://steamcommunity.com/market/priceoverview/?appid={app_id}&currency={currency_id}&market_hash_name={item_hash}'
    item_price_check_response = requests.get(price_check_url)

    if item_price_check_response.status_code == 200:
        price = float(item_price_check_response.json()[price_type][:-2].replace(',', '.'))
        return price, 200
    else:
        return None, item_price_check_response.status_code


def getSteamGameInventory(app_id, steam_id):
    inventory_url = f'http://steamcommunity.com/inventory/{steam_id}/{app_id}/2?l=english&count=5000'
    inventory_get_response = requests.get(inventory_url)

    if inventory_get_response.status_code == 200:
        return inventory_get_response.json(), 200
    else:
        return None, inventory_get_response.status_code
