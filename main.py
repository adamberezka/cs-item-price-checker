import datetime
import json
import os
import time
import requests
import pandas as pd
from currencies import currencies


def countItems(classid, assets):
    return sum(1 for item in assets if item.get('classid') == classid)


def calculatePrice(data, onlyCases=True):
    descriptions = data['descriptions']
    items = list(map(lambda item: (item['market_hash_name'], item['classid']), descriptions))
    if onlyCases:
        items = [item for item in items if "Case" in item[0]]
    items = list(set(items))
    items = [item + (countItems(item[1], data['assets']),) for item in items]
    items = sorted(items, key=lambda item: item[2], reverse=True)

    output = []

    for marketHashName, classid, count in items:
        itemPriceResponse = requests.get(priceCheckUrl + marketHashName)

        if itemPriceResponse.status_code == 200:
            price = float(itemPriceResponse.json()['lowest_price'][:-2].replace(',', '.'))
            output.append((marketHashName, int(count), price))
        else:
            print(f'Item price check error: {itemPriceResponse.status_code} for {marketHashName}')

        time.sleep(1)

    maxNameLength = max([len(item[0]) for item in output])
    maxItemCount = max([item[1] for item in output])
    maxItemCountDigits = len(str(maxItemCount))
    maxItemPrice = max([item[2] for item in output])
    maxItemPriceDigits = len("{:.2f}".format(maxItemPrice))
    total = 0

    output = sorted(output, key=lambda item: item[1] * item[2])

    for name, count, price in output:
        formattedName = f"{name:<{maxNameLength + 5}}"
        itemsTotalPrice = count * price
        total += itemsTotalPrice
        formattedPrice = "{:.2f}".format(price)
        print(f"{formattedName} {count:<{maxItemCountDigits}} * {formattedPrice:<{maxItemPriceDigits}} = {itemsTotalPrice:.2f} zł")

    print(f'{"Total: ":>{maxNameLength + 5}}', f'{"":<{maxItemCountDigits + maxItemPriceDigits + 5}}', f"{total:.2f} zł")
    print(f'{"After tax: ":>{maxNameLength + 5}}', f'{"":<{maxItemCountDigits + maxItemPriceDigits + 5}}', f"{total * 0.85:.2f} zł")
    saveTotal(total)


def saveInventory(data, outputFileName='inventoryResponse.json'):
    with open(outputFileName, "w") as outfile:
        json.dump(data, outfile)


def saveTotal(total, totalsFileName="totals.csv"):
    file_exists = os.path.exists(totalsFileName)

    new_row_df = pd.DataFrame({'DateTime': datetime.datetime.now(), 'Value': total}, index=['DateTime'])

    if not file_exists:
        new_row_df.to_csv(totalsFileName, index=False)
    else:
        existing_data = pd.read_csv(totalsFileName)
        updated_data = pd.concat([existing_data, new_row_df], ignore_index=True)
        updated_data.to_csv(totalsFileName, index=False)


steam64Id = '76561198092099461'
appId = 730  # Counter Strinke
currencyId = currencies["PLN"]

priceCheckUrl = f'https://steamcommunity.com/market/priceoverview/?appid={appId}&currency={currencyId}&market_hash_name='
inventoryUrl = f'http://steamcommunity.com/inventory/{steam64Id}/{appId}/2?l=english&count=5000'

inventoryResponse = requests.get(inventoryUrl)

if inventoryResponse.status_code == 200:
    data = inventoryResponse.json()
    saveInventory(data)
    calculatePrice(data)

else:
    print(f'Inventory get error: {inventoryResponse.status_code}')
    inventoryResponseFileName = 'inventoryResponse.json'
    print(f'\nTrying to read inventory from saved data: {inventoryResponseFileName}\n')

    with open(inventoryResponseFileName) as json_file:
        data = json.load(json_file)
        calculatePrice(data)
