import pandas as pd
from sqlalchemy import create_engine
from time import time

# Connection details from docker-compose.yaml
# Using localhost:5433 since we're running from outside the container
engine = create_engine('postgresql://postgres:postgres@localhost:5433/ny_taxi')

def load_parquet_in_batches(file_path, table_name, batch_size=100000):
    """Load a parquet file into PostgreSQL in batches."""
    print(f"\nLoading {file_path} into table '{table_name}'...")

    df = pd.read_parquet(file_path)
    total_rows = len(df)
    print(f"Total rows to load: {total_rows}")

    for i in range(0, total_rows, batch_size):
        t_start = time()
        batch = df.iloc[i:i+batch_size]

        if_exists = 'replace' if i == 0 else 'append'
        batch.to_sql(table_name, engine, if_exists=if_exists, index=False)

        t_end = time()
        print(f"  Loaded rows {i} to {min(i+batch_size, total_rows)} in {t_end - t_start:.2f} seconds")

    print(f"Finished loading {table_name}!")

def load_csv_in_batches(file_path, table_name, batch_size=100000):
    """Load a CSV file into PostgreSQL in batches."""
    print(f"\nLoading {file_path} into table '{table_name}'...")

    df = pd.read_csv(file_path)
    total_rows = len(df)
    print(f"Total rows to load: {total_rows}")

    for i in range(0, total_rows, batch_size):
        t_start = time()
        batch = df.iloc[i:i+batch_size]

        if_exists = 'replace' if i == 0 else 'append'
        batch.to_sql(table_name, engine, if_exists=if_exists, index=False)

        t_end = time()
        print(f"  Loaded rows {i} to {min(i+batch_size, total_rows)} in {t_end - t_start:.2f} seconds")

    print(f"Finished loading {table_name}!")

if __name__ == "__main__":
    load_parquet_in_batches(
        'data/green_tripdata_2025-11.parquet',
        'green_taxi_trips'
    )

    load_csv_in_batches(
        'data/taxi_zone_lookup.csv',
        'taxi_zones'
    )

    print("\nAll data loaded successfully!")
