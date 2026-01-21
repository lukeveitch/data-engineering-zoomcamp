import pandas as pd
from sqlalchemy import create_engine

# Read the zones CSV
df = pd.read_csv('taxi_zone_lookup.csv')

# Create database connection
engine = create_engine('postgresql://root:root@localhost:5432/ny_taxi')

# Load into database
df.to_sql(
    name='zones',
    con=engine,
    if_exists='replace',  # Drop and recreate table
    index=False           # Don't include pandas index as a column
)

print(f"Loaded {len(df)} zones successfully!")