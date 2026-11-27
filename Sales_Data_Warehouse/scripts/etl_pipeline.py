
import mysql.connector
import pandas as pd

# Connect to MySQL
connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="regan007",
    database="sales_analytics"
)

print("MySQL connection successful!")

# Extract sales data
query = """
SELECT
    f.order_id,
    c.customer_name,
    p.product_name,
    p.category,
    s.store_name,
    s.region,
    d.full_date,
    d.month_name,
    d.quarter,
    d.year,
    f.quantity,
    f.unit_price,
    f.discount_amount,
    f.total_amount,
    f.cost_amount,
    f.profit_amount
FROM fact_sales f
JOIN dim_customer c ON f.customer_key = c.customer_key
JOIN dim_product p ON f.product_key = p.product_key
JOIN dim_store s ON f.store_key = s.store_key
JOIN dim_date d ON f.date_key = d.date_key
"""

df = pd.read_sql(query, connection)


print("\nEXTRACT STAGE COMPLETED")
print("Total records:", len(df))
print(df.head())

# =====================================
# TRANSFORM STAGE
# =====================================

# Remove duplicate orders
df = df.drop_duplicates(subset=["order_id"])

# Remove records with missing values
df = df.dropna()

# Convert date column to datetime
df["full_date"] = pd.to_datetime(df["full_date"])

# Calculate revenue
df["calculated_revenue"] = (
    df["quantity"] * df["unit_price"]
    - df["discount_amount"]
)

# Calculate profit
df["calculated_profit"] = (
    df["calculated_revenue"] - df["cost_amount"]
)

print("\nTRANSFORM STAGE COMPLETED")
print("Records after cleaning:", len(df))
print("\nCalculated Revenue and Profit:")
print(df[[
    "order_id",
    "calculated_revenue",
    "calculated_profit"
]].head())


# =====================================
# LOAD STAGE
# =====================================

cursor = connection.cursor()

# Create destination table
cursor.execute("""
CREATE TABLE IF NOT EXISTS etl_sales_processed (
    order_id VARCHAR(30) PRIMARY KEY,
    customer_name VARCHAR(100),
    product_name VARCHAR(100),
    category VARCHAR(50),
    store_name VARCHAR(100),
    region VARCHAR(50),
    full_date DATE,
    quantity INT,
    unit_price DECIMAL(12,2),
    discount_amount DECIMAL(12,2),
    calculated_revenue DECIMAL(14,2),
    cost_amount DECIMAL(14,2),
    calculated_profit DECIMAL(14,2)
)
""")

# Clear previous ETL output before reloading
cursor.execute("DELETE FROM etl_sales_processed")

# Prepare transformed records
load_df = df[[
    "order_id",
    "customer_name",
    "product_name",
    "category",
    "store_name",
    "region",
    "full_date",
    "quantity",
    "unit_price",
    "discount_amount",
    "calculated_revenue",
    "cost_amount",
    "calculated_profit"
]]

insert_query = """
INSERT INTO etl_sales_processed (
    order_id, customer_name, product_name, category,
    store_name, region, full_date, quantity,
    unit_price, discount_amount, calculated_revenue,
    cost_amount, calculated_profit
) VALUES (
    %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s
)
"""

records = []
for row in load_df.itertuples(index=False, name=None):
    records.append(tuple(
        value.to_pydatetime() if isinstance(value, pd.Timestamp)
        else value.item() if hasattr(value, "item")
        else value
        for value in row
    ))

cursor.executemany(insert_query, records)
connection.commit()

print("\nLOAD STAGE COMPLETED")
print("Records loaded into MySQL:", cursor.rowcount)

cursor.close()
connection.close()

print("\nETL PIPELINE COMPLETED SUCCESSFULLY!")
