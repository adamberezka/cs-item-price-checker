import csv
from datetime import datetime
import json
import os
import time

import matplotlib.pyplot as plt
import pandas as pd

import steamApi
from currencies import currencies
from utils import log_invocation

steam_app_id = 730
steam_user_id = '76561198092099461'
currency = "PLN"
steam_currency_id = currencies[currency]
steam_item_price_type = 'lowest_price'
only_cases = True

items_prices_history_directory = './itemsPrices'
items_prices_plots_directory = './itemsPricesPlots'

itemCheckInterval = 10

plt.rcParams.update({'font.size': 22})


def getItemPrice(item_name):
    price, status = steamApi.getSteamItemPrice(steam_app_id, item_name, currency_id=steam_currency_id, price_type=steam_item_price_type)
    print(f'Item price check for {item_name} resulted in status {status}, price: {price}')
    return price


@log_invocation
def getInventory():
    inventory_response_filename = 'inventoryResponse.json'
    if os.path.exists(inventory_response_filename):
        with open(inventory_response_filename, 'r') as json_file:
            return json.load(json_file)
    else:
        inventory, status_code = steamApi.getSteamGameInventory(steam_app_id, steam_user_id)
        if status_code != 200:
            raise ValueError(f"Inventory get request returned status: {status_code}")
        with open(inventory_response_filename, "w") as json_file:
            json.dump(inventory, json_file)
        return inventory


# @log_invocation
def getItemsFromInventory(inventory, only_cases=only_cases):

    def countItems(class_id_to_count, assets):
        return sum(1 for item in assets if item.get('classid') == class_id_to_count)

    descriptions = inventory['descriptions']
    items_from_inventory = list(map(lambda item: (item['market_hash_name'], item['classid']), descriptions))
    if only_cases:
        items_from_inventory = [item for item in items_from_inventory if "Case" in item[0]]
    items_from_inventory = list(set(items_from_inventory))
    items_from_inventory = [item + (countItems(item[1], inventory['assets']),) for item in items_from_inventory]
    return sorted(items_from_inventory, key=lambda item: item[2], reverse=True)


@log_invocation
def saveSingleItemPriceChange(item_name, price):
    item_prices_history_file = items_prices_history_directory + "/" + item_name + ".csv"

    def saveHeaderAndPrice():
        print(f'Saving header and first price for: {item_name}, price: {price}')
        with open(item_prices_history_file, "w", newline="") as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(["DateTime", "Price"])
            csv_writer.writerow([datetime.now(), price])

    if not os.path.isfile(item_prices_history_file):
        print(f'Data file for item: {item_name} does not exist. Creating . . .')
        saveHeaderAndPrice()
    else:
        print(f'Checking last row for item: {item_name}')
        last_row = None
        with open(item_prices_history_file, "r", newline="") as csv_file:
            csv_reader = csv.reader(csv_file)
            for row in csv_reader:
                last_row = row

        print(f'For item {item_name}, last row: {last_row}')

        if last_row is None:
            print(f'Last row is none, saving header and first value . . .')
            saveHeaderAndPrice()
        elif last_row[1] != price:
            print(f'Last price for item {item_name} changed (last value: {last_row[1]}, new value: {price}), appending . . . ')
            with open(item_prices_history_file, "a", newline="") as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow([datetime.now(), price])


@log_invocation
def saveItemPricePlot(item_name):
    item_prices_history_file = items_prices_history_directory + "/" + item_name + ".csv"
    item_prices_plot_file = items_prices_plots_directory + "/" + item_name + ".png"

    item_prices_history = pd.read_csv(item_prices_history_file)

    plt.plot(pd.to_datetime(item_prices_history['DateTime']), item_prices_history['Price'])
    plt.savefig(item_prices_plot_file)  # TODO plots
    plt.close()


@log_invocation
def saveInventoryValue(items_with_prices_df):
    inventory_value_history_file = 'totals.csv'

    value = (items_with_prices_df['Price'] * items_with_prices_df['Count']).sum()

    def saveHeadersAndValue():
        with open(inventory_value_history_file, mode="w", newline="") as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(["DateTime", "Value"])
            csv_writer.writerow([datetime.now(), value])

    if (not os.path.isfile(inventory_value_history_file)) or (os.path.getsize(inventory_value_history_file) == 0):
        saveHeadersAndValue()
    else:
        with open(inventory_value_history_file, mode="a", newline="") as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow([datetime.now(), value])


@log_invocation
def saveInventoryValuePlot():
    inventory_value_history_file = 'totals.csv'
    inventory_value_plot_file = 'invPricePlot.png'
    inventory_value_history = pd.read_csv(inventory_value_history_file)

    plt.figure(figsize=(16, 9))
    plt.plot(pd.to_datetime(inventory_value_history['DateTime']), inventory_value_history['Value'])
    plt.savefig(inventory_value_plot_file)  # TODO plot
    plt.close()


items = pd.DataFrame(getItemsFromInventory(getInventory()), columns=['ItemName', 'ClassId', 'Count'])
items['Price'] = None

cursor = 0

print('\nStarting main loop . . .\n')

while True:

    itemToUpdate = items.iloc[cursor]
    print(f'Updating price for item {itemToUpdate["ItemName"]}')

    updatedItemPrice = getItemPrice(itemToUpdate['ItemName'])

    if updatedItemPrice is None:
        print(f'\nGet price for item: {itemToUpdate["ItemName"]} failed !!!')
        print(f'Will retry in: {itemCheckInterval} seconds\n')
    else:
        print(f'Saving item price for {itemToUpdate["ItemName"]}')
        items.at[cursor, 'Price'] = updatedItemPrice
        saveSingleItemPriceChange(itemToUpdate['ItemName'], updatedItemPrice)
        saveItemPricePlot(itemToUpdate['ItemName'])
        cursor += 1
        if cursor > len(items) - 1:
            saveInventoryValue(items)
            cursor = 0

    time.sleep(itemCheckInterval)
