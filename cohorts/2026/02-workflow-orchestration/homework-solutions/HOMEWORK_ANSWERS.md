# Week 2: Workflow Orchestration — Homework Answers

## Q1: Uncompressed file size of `yellow_tripdata_2020-12.csv`

**Answer: 128.3 MiB**

Found by running flow 04 (not 05) with yellow, 2020, 12. Click `extract` task → Outputs tab → file size shown next to the CSV. Flow 05 has `purge_files` which deletes output files after each execution, so the size isn't visible there.

## Q2: Rendered value of `file` variable (green, 2020, April)

**Answer: `green_tripdata_2020-04.csv`**

From the YAML: `file: "{{inputs.taxi}}_tripdata_{{trigger.date | date('yyyy-MM')}}.csv"` — with taxi=green and date=2020-04, it renders to `green_tripdata_2020-04.csv`.

## Q3: Total rows for Yellow Taxi 2020

**Answer: 24,648,499**

```sql
SELECT COUNT(*) FROM public.yellow_tripdata WHERE filename LIKE '%2020%';
```

## Q4: Total rows for Green Taxi 2020

**Answer: 1,734,051**

```sql
SELECT COUNT(*) FROM public.green_tripdata WHERE filename LIKE '%2020%';
```

## Q5: Rows for Yellow Taxi March 2021

**Answer: 1,925,152**

```sql
SELECT COUNT(*) FROM public.yellow_tripdata WHERE filename = 'yellow_tripdata_2021-03.csv';
```

## Q6: How to configure timezone to New York in a Schedule trigger?

**Answer: Add a `timezone` property set to `America/New_York` in the Schedule trigger configuration**

Kestra uses IANA timezone database names (the standard used across Java, Linux, Python, etc.):
- `EST` is wrong — it's an abbreviation and doesn't handle daylight saving (New York uses EDT in summer)
- `UTC-5` is wrong — it's a fixed offset, but New York switches between UTC-5 (winter) and UTC-4 (summer)
- `location` is wrong — the property name is `timezone`, not `location`

```yaml
triggers:
  - id: schedule
    type: io.kestra.plugin.core.trigger.Schedule
    cron: "0 9 1 * *"
    timezone: America/New_York
```
