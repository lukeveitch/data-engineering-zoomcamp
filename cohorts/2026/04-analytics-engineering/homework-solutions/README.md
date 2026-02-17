# Week 4 dbt Homework Answers

## Question 1: Understanding dbt model resolution

Given the `sources.yaml`:

```yaml
sources:
  - name: raw_nyc_tripdata
    database: "{{ env_var('DBT_BIGQUERY_PROJECT', 'dtc_zoomcamp_2025') }}"
    schema: "{{ env_var('DBT_BIGQUERY_SOURCE_DATASET', 'raw_nyc_tripdata') }}"
```

With environment variables:

```shell
export DBT_BIGQUERY_PROJECT=myproject
export DBT_BIGQUERY_DATASET=my_nyc_tripdata
```

**Answer:** `select * from myproject.raw_nyc_tripdata.ext_green_taxi`

**Explanation:**
- `DBT_BIGQUERY_PROJECT` is set to `myproject`, so the database resolves to `myproject`
- `DBT_BIGQUERY_DATASET` is set, but the schema uses `DBT_BIGQUERY_SOURCE_DATASET` which is **NOT** set, so it falls back to the default `raw_nyc_tripdata`
- The table name is `ext_green_taxi` as defined in the source

---

## Question 2: dbt Variables & Dynamic Models

To make `days_back` controllable where command line args > ENV_VARs > DEFAULT:

**Answer:** Update the WHERE clause to:
```sql
pickup_datetime >= CURRENT_DATE - INTERVAL '{{ var("days_back", env_var("DAYS_BACK", "30")) }}' DAY
```

**Explanation:**
- `var("days_back", ...)` checks for CLI variable first (via `--vars '{"days_back": 7}'`)
- If no CLI var, it falls back to `env_var("DAYS_BACK", "30")`
- If no env var set, it uses the default `"30"`
- This gives the correct precedence: CLI > ENV_VAR > DEFAULT

---

## Question 3: dbt Data Lineage and Execution

Which command does **NOT** work for materializing `fct_taxi_monthly_zone_revenue`?

**Answer:** `dbt run --select models/staging/+`

**Explanation:**
- `dbt run` - runs ALL models, including `fct_taxi_monthly_zone_revenue` ✓
- `dbt run --select +models/core/dim_taxi_trips.sql+` - runs `dim_taxi_trips` and all its upstream AND downstream dependencies ✓
- `dbt run --select +models/core/fct_taxi_monthly_zone_revenue.sql` - runs the fact model plus all upstream dependencies ✓
- `dbt run --select +models/core/` - runs everything in core plus upstream dependencies ✓
- `dbt run --select models/staging/+` - runs staging models and their **downstream** only, but this depends on the DAG. If `fct_taxi_monthly_zone_revenue` depends on staging models, it would be included. However, looking at the lineage diagram, if `taxi_zone_lookup` is a seed and the fact table depends on it, this selector might not reach everything needed.

---

## Question 4: dbt Macros and Jinja

Given the macro:

```sql
{% macro resolve_schema_for(model_type) -%}
    {%- set target_env_var = 'DBT_BIGQUERY_TARGET_DATASET' -%}
    {%- set stging_env_var = 'DBT_BIGQUERY_STAGING_DATASET' -%}

    {%- if model_type == 'core' -%} {{- env_var(target_env_var) -}}
    {%- else -%}                    {{- env_var(stging_env_var, env_var(target_env_var)) -}}
    {%- endif -%}
{%- endmacro %}
```

**True statements:**

1. ✅ **Setting a value for `DBT_BIGQUERY_TARGET_DATASET` env var is mandatory, or it'll fail to compile**
   - When `model_type == 'core'`, it calls `env_var(target_env_var)` without a default - this will fail if not set
   - When `model_type != 'core'`, the fallback also uses `env_var(target_env_var)` without a default

2. ❌ Setting a value for `DBT_BIGQUERY_STAGING_DATASET` env var is mandatory - **FALSE**
   - It has a fallback: `env_var(stging_env_var, env_var(target_env_var))`

3. ✅ **When using `core`, it materializes in the dataset defined in `DBT_BIGQUERY_TARGET_DATASET`**
   - The `if model_type == 'core'` branch returns `env_var(target_env_var)`

4. ✅ **When using `stg`, it materializes in the dataset defined in `DBT_BIGQUERY_STAGING_DATASET`, or defaults to `DBT_BIGQUERY_TARGET_DATASET`**
   - Any value other than `'core'` goes to the else branch

5. ✅ **When using `staging`, it materializes in the dataset defined in `DBT_BIGQUERY_STAGING_DATASET`, or defaults to `DBT_BIGQUERY_TARGET_DATASET`**
   - Same as above - `'staging'` is not `'core'`, so it goes to else branch
