# Week 3: Data Warehouse (BigQuery)

## Core Concepts

### OLTP vs OLAP
- **OLTP**: Transactional databases (inserts, updates, deletes)
- **OLAP**: Analytical databases (aggregations, reporting, read-heavy)
- **BigQuery**: Serverless OLAP data warehouse - no infrastructure, auto-scaling, pay-per-query

### Columnar Storage
BigQuery only scans columns you SELECT:
- `SELECT PULocationID` → 155 MB
- `SELECT PULocationID, DOLocationID` → 310 MB (2x)

**Rule**: Only SELECT columns you need.

---

## External vs Materialized Tables

| Aspect | External Table | Materialized Table |
|--------|---------------|-------------------|
| Data location | Stays in GCS | Copied to BigQuery |
| Query speed | Slower | Faster |
| Cost estimate | Shows 0 MB (unreliable) | Accurate |
| Storage cost | Lower | Higher |
| Use case | Exploration, staging | Production workloads |

```sql
-- External table from GCS
CREATE OR REPLACE EXTERNAL TABLE dataset.external_table
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://bucket-name/path/*.parquet']
);

-- Materialize it
CREATE OR REPLACE TABLE dataset.materialized_table AS
SELECT * FROM dataset.external_table;
```

---

## Partitioning

**When to use**: Large tables (>1GB), filtering by date/time columns

**Benefits**: 90%+ reduction in data scanned (e.g., 310 MB → 27 MB)

**Types**:
- Time-unit: HOURLY, DAILY, MONTHLY, YEARLY (most common)
- Integer range
- Ingestion time

**Limit**: 4,000 partitions max

```sql
CREATE OR REPLACE TABLE dataset.partitioned_table
PARTITION BY DATE(datetime_column)
AS SELECT * FROM dataset.source_table;
```

---

## Clustering

**When to use**: High-cardinality columns, columns in WHERE/GROUP BY/ORDER BY

**Rules**:
- Up to 4 columns
- Tables should be >1GB (overhead not worth it for small tables)
- Combine with partitioning for best results

```sql
CREATE OR REPLACE TABLE dataset.optimized_table
PARTITION BY DATE(dropoff_datetime)
CLUSTER BY VendorID, payment_type
AS SELECT * FROM dataset.source_table;
```

---

## Performance Comparison

| Type | Data Scanned | Query Speed | Best For |
|------|-------------|-------------|----------|
| External | Full | Slow | Exploration |
| Materialized | Full | Fast | Production |
| Partitioned | ~10% | Faster | Date filtering |
| Partitioned + Clustered | ~5% | Fastest | Complex queries |

---

## Cost Optimization

### Pricing
- **Storage**: $0.02/GB/month (active), $0.01/GB/month (long-term)
- **Queries**: $5/TB scanned (on-demand)

### Strategies
1. Partition large tables by date
2. Cluster frequently filtered columns
3. Avoid `SELECT *`
4. Use `COUNT(*)` instead of `COUNT(column)` - uses metadata, free
5. Set partition expiration for auto-deletion
6. `LIMIT` doesn't reduce data scanned - BigQuery scans first, then limits

### Testing Tips
- Disable query cache when testing optimization (Settings → Query settings)
- Always check estimated bytes before running

---

## Flat-Rate vs On-Demand Pricing

**Common misconception**: "Flat-rate means optimization doesn't matter"

**Reality**: Optimization is still critical with flat-rate:

| Concern | On-Demand | Flat-Rate |
|---------|-----------|-----------|
| Cost driver | $ per TB scanned | Slot contention |
| Bad query impact | Higher bill | Blocks other queries |
| Optimization goal | Reduce scanned data | Free up slots faster |

### Flat-Rate Specifics
- Fixed number of **slots** (compute units)
- Poor queries hog slots → other queries queue
- Storage costs still apply separately
- Slot exhaustion = timeouts & failures

**Example**:
- Bad query: 2TB scan, 8 min, uses all 500 slots
- Optimized: 20GB scan, 12 sec, uses 50 slots → 40x more concurrent capacity

---

## Parquet Format

- Columnar storage (matches BigQuery architecture)
- Highly compressed
- Fast reads
- Preserves schema/types
- Much more efficient than CSV for analytics

---

## Quick Reference SQL

```sql
-- Count records (free - uses metadata)
SELECT COUNT(*) FROM table;

-- Count distinct
SELECT COUNT(DISTINCT column) FROM table;

-- Date filtering (triggers partition pruning)
SELECT * FROM table
WHERE date_column BETWEEN '2024-03-01' AND '2024-03-15';

-- Check for zero values
SELECT COUNT(*) FROM table WHERE fare_amount = 0;
```
