
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Query

app = FastAPI(
    title="ecommerce Data API",
    description="Explore customers, orders, products and payments",
    version="1.0.0"
)

DATA_DIR = Path(__file__).parent / "data"

FILES = {
    "customers": "customers.csv",
    "geolocation": "geolocation.csv",
    "order_items": "order_items.csv",
    "orders": "orders.csv",
    "payments": "payments.csv",
    "products": "products.csv",
    "sellers": "sellers.csv"
}


def load_data(dataset: str) -> pd.DataFrame:
    """Load a supported CSV dataset."""
    if dataset not in FILES:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found"
        )

    file_path = DATA_DIR / FILES[dataset]

    if not file_path.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Missing CSV file: {FILES[dataset]}"
        )

    try:
        return pd.read_csv(file_path)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not read dataset: {dataset}"
        ) from exc


@app.get("/")
def home():
    return {
        "message": "E-commerce API is running",
        "documentation": "/docs",
        "datasets": list(FILES.keys())
    }


@app.get("/datasets")
def list_datasets():
    return {"datasets": list(FILES.keys())}


@app.get("/data/{dataset}")
def get_data(
    dataset: str,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    df = load_data(dataset)

    # Avoid returning missing values as invalid JSON
    records = (
        df.iloc[offset:offset + limit]
        .astype(object)
        .where(pd.notna(df.iloc[offset:offset + limit]), None)
        .to_dict(orient="records")
    )

    return{
        "dataset": dataset,
        "total_rows": len(df),
        "offset": offset,
        "limit": limit,
        "data": records
    }


@app.get("/customers/search")
def search_customers(
    city: str = Query(min_length=1),
    limit: int = Query(default=10, ge=1, le=100)
):
    df = load_data("customers")

    result = df[
        df["customer_city"].str.contains(
            city, case=False, na=False, regex=False
        )
    ].head(limit)

    return {
        "count": len(result),
        "data": result.to_dict(orient="records")
    }


@app.get("/orders/status/{status}")
def orders_by_status(status: str):
    df = load_data("orders")

    result = df[
        df["order_status"].str.lower() == status.lower()
    ]

    return {
        "status": status,
        "count": len(result),
        "data": result.head(100).to_dict(orient="records")
    }


@app.get("/products/categories")
def product_categories():
    df = load_data("products")
    column = "product category"

    categories = (
        df[column]
        .dropna()
        .value_counts()
        .rename_axis("category")
        .reset_index(name="product_count")
    )

    return {
        "total_categories": len(categories),
        "data": categories.to_dict(orient="records")
    }


@app.get("/analytics/summary")
def analytics_summary():
    orders = load_data("orders")
    customers = load_data("customers")
    items = load_data("order_items")
    payments = load_data("payments")

    return {
        "total_orders": int(len(orders)),
        "total_customers": int(len(customers)),
        "total_order_items": int(len(items)),
        "total_payment_records": int(len(payments)),
        "total_payment_value": round(
            float(payments["payment_value"].sum()), 2
        ),
        "order_status_counts": {
            str(k): int(v)
            for k, v in orders["order_status"]
            .value_counts(dropna=False).items()
        }
    }
print("Data folder:", DATA_DIR.resolve())
print("Folder exists:", DATA_DIR.exists())
print("Customers file exists:", (DATA_DIR / "customers.csv").exists()) 