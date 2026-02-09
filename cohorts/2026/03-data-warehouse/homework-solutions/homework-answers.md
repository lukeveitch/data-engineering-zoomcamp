# Week 3 Homework Answers: Data Warehouse (BigQuery)

## Setup

Data: Yellow Taxi Trip Records for **January 2024 - June 2024** (Parquet files)

```sql
-- Create external table
CREATE OR REPLACE EXTERNAL TABLE `project.dataset.yellow_taxi_external`
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://your-bucket/yellow_tripdata_2024-*.parquet']
);

-- Create materialized table
CREATE OR REPLACE TABLE `project.dataset.yellow_taxi_materialized` AS
SELECT * FROM `project.dataset.yellow_taxi_external`;
```

---

## Question 1: Record count for 2024 Yellow Taxi Data

```sql
SELECT COUNT(*) FROM `project.dataset.yellow_taxi_materialized`;
```

**Answer: 20,332,093**

---

## Question 2: Estimated data for COUNT(DISTINCT PULocationID)

```sql
SELECT COUNT(DISTINCT PULocationID) FROM `project.dataset.yellow_taxi_external`;
SELECT COUNT(DISTINCT PULocationID) FROM `project.dataset.yellow_taxi_materialized`;
```

**Answer: 0 MB for the External Table and 155.12 MB for the Materialized Table**

External tables show 0 MB because BigQuery cannot estimate data size for external sources (no metadata available).

---

## Question 3: Why are estimated bytes different for 1 vs 2 columns?

```sql
SELECT PULocationID FROM `project.dataset.yellow_taxi_materialized`;
SELECT PULocationID, DOLocationID FROM `project.dataset.yellow_taxi_materialized`;
```

**Answer: BigQuery is a columnar database, and it only scans the specific columns requested in the query. Querying two columns (PULocationID, DOLocationID) requires reading more data than querying one column (PULocationID), leading to a higher estimated number of bytes processed.**

---

## Question 4: Records with fare_amount of 0

```sql
SELECT COUNT(*) FROM `project.dataset.yellow_taxi_materialized`
WHERE fare_amount = 0;
```

**Answer: 128,210**

---

## Question 5: Best optimization strategy (filter by tpep_dropoff_datetime, order by VendorID)

```sql
CREATE OR REPLACE TABLE `project.dataset.yellow_taxi_partitioned_clustered`
PARTITION BY DATE(tpep_dropoff_datetime)
CLUSTER BY VendorID
AS SELECT * FROM `project.dataset.yellow_taxi_materialized`;
```

**Answer: Partition by tpep_dropoff_datetime and Cluster on VendorID**

- Partition by the column you filter on (tpep_dropoff_datetime)
- Cluster by the column you sort/order by (VendorID)

---

## Question 6: Estimated bytes for distinct VendorIDs (March 1-15, 2024)

```sql
-- Non-partitioned table
SELECT DISTINCT VendorID FROM `project.dataset.yellow_taxi_materialized`
WHERE tpep_dropoff_datetime BETWEEN '2024-03-01' AND '2024-03-15';

-- Partitioned table
SELECT DISTINCT VendorID FROM `project.dataset.yellow_taxi_partitioned_clustered`
WHERE tpep_dropoff_datetime BETWEEN '2024-03-01' AND '2024-03-15';
```

**Answer: 310.24 MB for non-partitioned table and 26.84 MB for the partitioned table**

Partitioning reduces data scanned by ~90% because BigQuery only scans the relevant date partitions.

---

## Question 7: Where is External Table data stored?

**Answer: GCP Bucket**

External tables reference data stored in Google Cloud Storage (GCS). The data is not copied into BigQuery.

---

## Question 8: Is it best practice to always cluster your data?

**Answer: False**

Clustering is not always beneficial:
- Small tables (<1GB) don't benefit from clustering
- Overhead may not be worth it for infrequently queried tables
- Only cluster when queries frequently filter/sort by specific columns

---

## Question 9 (Bonus): SELECT COUNT(*) bytes estimate

```sql
SELECT COUNT(*) FROM `project.dataset.yellow_taxi_materialized`;
```

**Answer: 0 bytes**

BigQuery uses table metadata to return the row count without scanning any data. `COUNT(*)` is essentially free.
