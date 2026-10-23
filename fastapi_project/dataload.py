
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

uri = os.getenv("MONGO_URI")
if not uri:
    raise ValueError("MONGO_URI is missing from your .env file")

client = MongoClient(uri, serverSelectionTimeoutMS=10000)

# Verify the Atlas connection
client.admin.command("ping")
print("MongoDB Atlas connected successfully!")

db = client["data_api"]

data_dir = Path(__file__).parent / "data"

files = [
    "customers.csv",
    "geolocation.csv",
    "order_items.csv",
    "orders.csv",
    "payments.csv",
    "products.csv",
    "sellers.csv",
]

for filename in files:
    path = data_dir / filename

    if not path.exists():
        print(f"File not found: {path}")
        continue

    df = pd.read_csv(path)
    df = df.astype(object).where(pd.notna(df), None)
    records = df.to_dict(orient="records")

    collection_name = path.stem
    collection = db[collection_name]

    if records:
        # Replace existing collection contents on re-import.
        # Only use this on collections you intend to refresh.
        collection.delete_many({})
        result = collection.insert_many(records)
        print(f"{collection_name}: inserted {len(result.inserted_ids)} documents")
    else:
        print(f"{collection_name}: CSV is empty")

client.close()
