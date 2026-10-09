import pandas as pd
from database import get_connection

STORES_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1LfF4pfY7aPECnZJHiw0YsY_AF7WRoNnB1PuFGnJ6npg/"
    "export?format=csv&gid=1763900964"
)

stores = pd.read_csv(STORES_URL)

print("STORES READY FOR LOADING:")
print(stores.to_string(index=False))
print(f"\nTotal stores: {len(stores)}")