import pandas as pd

FILE_PATH = "data/incoming/inventory/BRU-0001_inventory_2026-10-05.xlsx"

inventory = pd.read_excel(FILE_PATH)

print(inventory)
