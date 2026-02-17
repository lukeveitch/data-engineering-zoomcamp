# Week 4 dbt Homework Answers

## Question 1: dbt Lineage and Execution

**Q: Running `dbt run --select int_trips_unioned` executes which models?**

**Answer: int_trips_unioned only**

**Explanation:**
The `--select` flag without a `+` prefix runs only that specific model. To include upstream dependencies, you would need `dbt run --select +int_trips_unioned`. To include downstream dependencies, you would use `dbt run --select int_trips_unioned+`.

---

## Question 2: dbt Tests

**Q: After `dbt test --select fct_trips` encounters a new value `6` in payment_type (expected: 1-5), what happens?**

**Answer: dbt fails the test, returning non-zero exit code**

**Explanation:**
The `accepted_values` test fails by default when it encounters values not in the defined list. To make it warn instead of fail, you would need to configure `severity: warn` in the test definition.

---

## Question 3: Record Count in fct_monthly_zone_revenue

**Q: What is the total record count in `fct_monthly_zone_revenue`?**

**Answer: 12,998**

**Explanation:**
This model aggregates taxi trips by service_type, year, month, and pickup_zone. The count is much smaller than the source data because of the aggregation.

---

## Question 4: Best Performing Zone for Green Taxis (2020)

**Q: Which pickup zone has the highest total revenue (`revenue_monthly_total_amount`) for Green taxis in 2020?**

**Answer: East Harlem North**

---

## Question 5: Green Taxi Trips (October 2019)

**Q: What is the total trip count (`total_monthly_trips`) for Green taxis in October 2019?**

**Answer: 384,624**

---

## Question 6: FHV Staging Model Record Count

**Q: After creating `stg_fhv_tripdata` (filtering null dispatching_base_num, renaming fields), what is the record count?**

**Answer: 22,998,722**

**Explanation:**
This count reflects FHV trip records from 2019 after filtering out rows where `dispatching_base_num` is NULL and joining with `dim_zones` to keep only records with known pickup and dropoff locations.
