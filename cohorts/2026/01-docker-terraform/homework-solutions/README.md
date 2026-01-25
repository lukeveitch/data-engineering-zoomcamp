
# Week 1 Homework Solutions

## question 1 - understanding docker images. 

here we need to run a container, from the python:3.13 image and override the entrypoint. 
once running the container, we can use python to check the pip version.

docker run --it --entrypoint bash python:3.13

What's the version of pip in the image?

**25.3**

## question2 - understanding docker networking and docker compose

given the .yaml file, the hostname needs to be the service name that we want to connect to. 

there are three services, or containers, in this .yaml file. we can the service called 'db' because it's running postgres on it. 

the port that you connect to/share is always the second one, so in this case 5432

the answer is: **db:5432**
you could also use postgres:5432, but if there are multiple databases running postgres then this will be a problem, as you should always use the service name. 

## question3 - counting short trips

We need to count trips in November 2025 with trip_distance <= 1 mile.

```
SELECT COUNT(1)
FROM green_taxi_trips
WHERE DATE(lpep_pickup_datetime) >= '2025-11-01'
  AND DATE(lpep_pickup_datetime) < '2025-12-01'
  AND trip_distance <= 1;
```

**Answer: 8,007**

## question 4 - longest trip

```sql
select date(lpep_pickup_datetime) date,
max(trip_distance) max_trip_distance
from green_taxi_trips
where trip_distance <= 100
group by 1
order by 2 desc
limit 1;
```

**Answer: 2025-11-14**

