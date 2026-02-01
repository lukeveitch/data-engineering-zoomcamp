# Week 2: Workflow Orchestration — Study Notes

## Key

| Section | What it covers |
|---------|---------------|
| **Q&A** | Questions asked during study sessions with explanations |
| **Anatomy of a Kestra Flow** | Breakdown of every section in a Kestra YAML flow file |
| **Anatomy of a Docker Compose File** | Breakdown of every section in a docker-compose.yml |
| **Flow 04: Loading NYC Taxi Data** | The staging pattern, conditional branching, and tracing data flow |

## Q&A

### Q1: What are ports? How do Docker port mappings work?

**What are ports?** Computers use port numbers to keep track of different network connections. When your browser loads a website, it connects to that server on a specific port (usually port 80 for HTTP or 443 for HTTPS). Ports are how one machine can run many services at once — each service listens on a different port number, so traffic gets routed to the right place. This applies to the internet, your local network, and services running on your own machine.

**Docker port mappings:** Every service in a Docker container listens on its own port, but your computer can't see it directly. A port mapping connects a port on your computer to a port inside the container.

Format: `HOST:CONTAINER` (left is your machine, right is inside the container).

- `"8085:80"` means port 80 inside the container is exposed as port 8085 on your machine.
- You always use the **left side (host port)** to access a service.
- If a service has **no ports section**, it's only reachable by other containers on the internal Docker network (e.g. `kestra_postgres`).

| Service | Mapping | Access at |
|---------|---------|-----------|
| pgdatabase | `5432:5432` | `localhost:5432` |
| pgadmin | `8085:80` | `localhost:8085` |
| kestra | `8080:8080` | `localhost:8080` |
| kestra_postgres | none | internal only |

**Why remap?** To avoid conflicts. pgAdmin runs on port 80 inside its container, but 80 may already be in use on your machine, so it's mapped to 8085. When both sides match (`5432:5432`), no remapping is needed.

**What does "internal only" mean?** Docker Compose creates a private network that all containers in the same `docker-compose.yml` share. Containers can talk to each other using their service names (e.g. `kestra` connects to `kestra_postgres:5432`). But your computer is not on that private network. If a service has no port mapping, there's no way to reach it from your browser or terminal — only other containers can. This is intentional: Kestra's internal database doesn't need to be accessed by you, only by Kestra itself.

### Q2: How does Kestra spin up and tear down containers for tasks?

The Kestra service in `docker-compose.yml` has this volume mount:

```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
  - /tmp/kestra-wd:/tmp/kestra-wd
```

**`/var/run/docker.sock`** is the Docker socket — it's how any program talks to the Docker daemon (the background process that manages containers). By mounting it into the Kestra container, Kestra gains the ability to create, run, and destroy Docker containers on your machine.

**Why does it need this?** When a Kestra flow runs a Python script (or any code), Kestra doesn't run it inside its own container. Instead it:
1. Spins up a **fresh, isolated container** with the right image (e.g. a Python container)
2. Passes in any input files the task needs
3. Runs the script
4. Captures the output
5. Destroys the container

Each task gets a clean environment. Different tasks can use different languages or dependency versions without conflicts. If a script crashes, it only affects its own container.

**What's this pattern called?** This is **containerized task execution** (or **ephemeral container execution**). The broader pattern of one container managing other containers via the Docker socket is called **Docker-out-of-Docker (DooD)** — Kestra doesn't run its own Docker daemon, it uses the host's daemon through the mounted socket. (The related but different pattern where a container runs its own Docker daemon inside itself is called **Docker-in-Docker / DinD**.)

**`/tmp/kestra-wd`** is a shared working directory. Kestra uses this to pass files between itself and the task containers it creates — input data goes in, output data comes out. Both Kestra and the task container can see this directory because it's mounted in both.

---

## The Anatomy of a Kestra Flow

A **Flow** is a YAML file that defines a pipeline. Every Kestra flow follows the same structure:

### `id` and `namespace`

- **`id`** — the unique name of the flow.
- **`namespace`** — a logical grouping, like a folder. All zoomcamp flows go under `zoomcamp`. In a company you might have `marketing`, `finance`, etc.

### `inputs`

An **Input** is a value you pass in when you trigger the flow. Inputs can have a type (STRING, INT, etc.) and a default value. When you click "Execute" in the UI, Kestra shows a form where you fill these in.

### `concurrency`

Limits how many instances of the flow can run at the same time. If the limit is reached, extra executions fail. Prevents the same flow from overwhelming your system.

### `variables`

Reusable values you define once and reference elsewhere. Uses `{{ }}` template syntax which gets replaced with actual values **at execution time** — not when you save the file. Variable namespaces include `inputs.*`, `outputs.*`, `trigger.*`, and `vars.*`.

### `tasks`

The individual steps of the flow. They run **sequentially, top to bottom** by default. Each task has:
- **`id`** — unique name within the flow
- **`type`** — the plugin that runs the task (e.g. `io.kestra.plugin.core.log.Log`)
- Task-specific config (e.g. `message`, `format`, `duration`)

**Key concepts within tasks:**
- **`render()`** — resolves nested templates. If a variable contains `{{ }}` inside it, you need `render()` to evaluate the inner template too.
- **Outputs** — a task can produce data that later tasks reference with `{{ outputs.task_id.value }}`. This is how data flows between steps.

### `pluginDefaults`

Sets default config for all tasks of a given type. Instead of repeating the same setting on every Log task, set it once here and they all inherit it.

### `triggers`

A **Trigger** starts a flow automatically. Common types:
- **Schedule** — cron expression (e.g. `"0 10 * * *"` = every day at 10:00 AM). Can pass inputs and can be `disabled: true`.
- **Event-based** — reacts to external events.

### Key Concepts Summary

| Concept | What it is |
|---------|------------|
| **Flow** | A YAML file defining a pipeline — its tasks, inputs, and triggers |
| **Task** | A single step in the flow (log a message, run a script, download a file) |
| **Input** | A value passed in when the flow is triggered — makes flows reusable |
| **Output** | Data a task produces, available to downstream tasks via `{{ outputs.task_id.* }}` |
| **Trigger** | Starts a flow automatically (cron schedule, event, etc.) |

---

## The Anatomy of a Docker Compose File

A `docker-compose.yml` defines a multi-container application. Every Docker Compose file follows the same structure:

### `volumes` (top-level)

Named storage that persists data even when containers are stopped or deleted. Without volumes, everything inside a container disappears when it's removed. You define them at the top level, then reference them inside individual services.

```yaml
volumes:
  ny_taxi_postgres_data:
    driver: local
```

`driver: local` means the data is stored on your machine's filesystem. This is the default and most common option.

### `services`

The core of the file. Each service becomes a running container. Docker Compose handles networking between them automatically — every service can reach every other service by name.

### Inside each service:

#### `image`

The Docker image to use. A pre-built package containing the software and its dependencies. Docker pulls it from Docker Hub if you don't have it locally.

```yaml
image: postgres:18
```

`postgres:18` means the Postgres image, version 18. The part after `:` is the tag (version).

#### `environment`

Environment variables passed into the container. This is how you configure the software running inside it — database names, passwords, settings. The container reads these when it starts up.

```yaml
environment:
  POSTGRES_USER: root
  POSTGRES_PASSWORD: root
  POSTGRES_DB: ny_taxi
```

#### `ports`

Maps a port on your machine to a port inside the container. Format: `HOST:CONTAINER`. You use the left side (host port) to access the service from your browser or terminal. If omitted, the service is only reachable by other containers.

```yaml
ports:
  - "5432:5432"
```

#### `volumes` (service-level)

Mounts storage into the container. Two common uses:
- **Named volumes** — persistent data storage (e.g. database files that survive restarts)
- **Bind mounts** — share a specific file or directory from your machine into the container

```yaml
volumes:
  - ny_taxi_postgres_data:/var/lib/postgresql    # named volume
  - /var/run/docker.sock:/var/run/docker.sock    # bind mount
```

#### `healthcheck`

A command Docker runs periodically to check if the service is actually working, not just running. Other services can wait for a healthy status before starting.

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -d $${POSTGRES_DB} -U $${POSTGRES_USER}"]
  interval: 30s
  timeout: 10s
  retries: 10
```

This runs `pg_isready` every 30 seconds to check if Postgres is accepting connections.

#### `depends_on`

Controls startup order. Tells Docker Compose that this service needs another service to be running first.

```yaml
depends_on:
  kestra_postgres:
    condition: service_started
```

This means: don't start Kestra until `kestra_postgres` has started. You can also use `condition: service_healthy` to wait for the healthcheck to pass.

#### `user`

Which user to run as inside the container. Most containers run as a non-root user by default for security. Sometimes you need root for specific permissions (like accessing the Docker socket).

```yaml
user: "root"
```

#### `command`

Overrides the default command the container runs on startup. The image has a built-in default, but you can replace it.

```yaml
command: server standalone
```

#### `pull_policy`

When to pull a new version of the image. `always` means check for updates every time you run `docker compose up`, even if you already have the image locally.

```yaml
pull_policy: always
```

### Key Concepts Summary

| Concept | What it is |
|---------|------------|
| **Service** | A single container defined in the file — one running application |
| **Image** | The pre-built package a container is created from |
| **Volume** | Persistent storage that survives container restarts and removals |
| **Port mapping** | Connects a port on your machine to a port inside a container (`HOST:CONTAINER`) |
| **Environment** | Configuration values passed into the container at startup |
| **Healthcheck** | A periodic test to verify the service is actually working |
| **depends_on** | Controls startup order between services |

---

### Q3: How does Kestra capture Python script output?

The `kestra` pip package is a small SDK. Your script calls `Kestra.outputs({"downloads": 1459257})` — that one line writes the data to a file inside the container. Kestra is already watching for that file. When the container finishes, Kestra reads it and shows the data in the Outputs tab.

The noisy debug logs (Python version detection etc.) aren't from your code. That's Kestra's **task runner** setting up the container before your script starts. If the status says SUCCESS and Outputs has your number, everything worked — ignore the noise.

**In short:** Kestra creates a throwaway Python environment from scratch every run — pulls the image, installs pip packages, runs the script, grabs the output, deletes the container. Next execution starts from zero again. That's why the first run is slower (image pull + pip install) and why there's setup noise in the logs.

**Analogy:** Kestra is like a manager who hires a temp worker for one job. It sets up a desk (container), gives them tools (pip packages), hands them instructions (your script), collects their report (outputs), then clears the desk. Next job, new temp, new desk.

**How to know what Kestra is doing — read the YAML:**
- `containerImage` tells you what environment it's building (e.g. `python:slim`)
- `dependencies` tells you what packages it installs
- `script` is the actual code it runs
- `Kestra.outputs()` in the script is what gets sent back to you in the Outputs tab
- `taskRunner.type: ...Docker` confirms it's running in a throwaway container

### Q4: Does the API in flow 03 require authentication?

No. `https://dummyjson.com/products` is a free public test API — no auth, no API key. That's why the `extract` task is just a `Download` with a URL and nothing else. A real-world pipeline with auth would look like:

```yaml
- id: extract
  type: io.kestra.plugin.core.http.Download
  uri: https://api.company.com/v1/sales
  headers:
    Authorization: "Bearer {{ secret('API_TOKEN') }}"
    Content-Type: application/json
```

Same plugin, but with `headers` for authentication. `secret()` pulls the token from Kestra's secret storage so you don't hardcode credentials in YAML.

### Q5: How does downloaded data get passed into the Python container?

Nothing to do with the Docker image (`python:3.11-alpine`). The image is just a blank Python environment — it knows nothing about Kestra or your data.

The connection happens through **Kestra's YAML properties**:

1. The `extract` task downloads a file. Kestra stores it internally and creates a reference: `outputs.extract.uri`.
2. The `transform` task says:
   ```yaml
   inputFiles:
     data.json: "{{outputs.extract.uri}}"
   ```
   This tells **Kestra** (not Python): "Before starting the container, take the file from `outputs.extract.uri` and place it inside the container as `data.json`."
3. Kestra creates the container and copies the file in. By the time the Python script runs, `data.json` is just a regular file on disk. The script does `open("data.json", "r")` — it has no idea the file came from a URL.

`inputFiles` and `outputFiles` are Kestra YAML properties that move files between tasks. The Docker image doesn't know about them. The Python script doesn't know about them. Kestra reads the YAML, moves the files, and the script just sees normal files.

### Q6: Flow 03 — the `query` (Load) task

**Why `data["products"]` in the script?** The API at `dummyjson.com/products` returns JSON structured like `{ "products": [...], "total": 100, "skip": 0 }`. The actual data is nested under the `"products"` key — the rest is pagination metadata. So the script does `data["products"]` to grab the list. This isn't a Kestra thing, it's just how this API structures its response. Every API is different.

**`{{workingDir}}`** is a built-in Kestra variable. It points to the temporary directory where the task's `inputFiles` are placed. When Kestra copies `products.json` into the DuckDB task, it puts it in the working directory. So `{{workingDir}}/products.json` resolves to the actual file path. You don't set this yourself — Kestra provides it automatically for every task.

**`fetchType: STORE`** controls what Kestra does with SQL query results:
- **`FETCH`** — loads all rows into memory, returns them as a Kestra output. Fine for small results.
- **`STORE`** — writes results to a file instead of holding them in memory. Better for large result sets.
- **`NONE`** — don't return results (useful for INSERT/UPDATE where you don't need output).

`STORE` is used here as good practice — it scales better even if the result set is small.

### Q7: What is the task environment, why DuckDB, and where is data stored?

**Task environment:** The temporary workspace Kestra creates for each task. For Python tasks, that's the throwaway Docker container. For SQL tasks like DuckDB, it's a working directory on the Kestra server. Each task gets its own isolated environment — cleaned up when the task finishes.

**Why DuckDB?** It's an in-process analytics database — no server needed. It runs inside the task itself, processes the query, and shuts down. No setup, no credentials, no separate container. It can read JSON, CSV, and Parquet files directly with SQL, making it perfect for lightweight query steps. It's free and open source.

**How much can FETCH hold?** `FETCH` loads results into Kestra's JVM memory (the Java process running the server). A few thousand rows is fine. Millions of rows would crash it — that's why `STORE` exists (writes to disk instead).

**Where does the data live?** `localhost:8080` is just the web UI — a window into Kestra, not a storage location.
- `FETCH` results — held in server memory while the execution is active. Visible in Outputs tab but not permanently stored as data.
- `STORE` results — written to Kestra's internal storage (the `kestra_data` Docker volume on disk).

Both show up in the Outputs tab through the UI, but the UI is just displaying them — not where they live.

---

## Flow 04: Loading NYC Taxi Data into Postgres

### How many tasks run?

5 top-level tasks: `set_label` → `extract` → `if_yellow_taxi` → `if_green_taxi` → `purge_files`. But only **one** `if` branch runs per execution (the other is skipped). Each branch has 5 sub-tasks inside it. So a single execution runs 4 top-level tasks + 5 sub-tasks = 9 actual steps.

### The Staging Pattern

Data doesn't go directly into the final table. Instead:
1. **Create final table** — `CREATE TABLE IF NOT EXISTS` (only creates once)
2. **Create staging table** — same schema, temporary landing zone
3. **Truncate staging** — wipe it clean so no leftover data from previous runs
4. **CopyIn** — bulk load the CSV into staging (fast Postgres bulk import)
5. **Add unique ID + filename** — enrich rows with an MD5 hash (fingerprint) and source filename
6. **MERGE** — move data from staging to final table. If the row already exists, skip it. No duplicates.

This means you can safely re-run the flow for the same month without creating duplicate rows.

### Q8: How do I know where data comes from and where it goes?

You can trace the full data journey by reading the YAML:

**Where data comes FROM — look at the `extract` task:**
```yaml
commands:
  - wget -qO- https://github.com/DataTalksClub/nyc-tlc-data/releases/download/{{inputs.taxi}}/...
```
The URL tells you the source. Here it's a GitHub releases page hosting CSV files.

**Where data goes TO — look at two places:**

1. **The task type** tells you the destination technology:
   - `io.kestra.plugin.jdbc.postgresql.Queries` → it's talking to PostgreSQL
   - `io.kestra.plugin.jdbc.duckdb.Queries` → it's talking to DuckDB
   - `io.kestra.plugin.gcp.bigquery` → it's talking to BigQuery

2. **`pluginDefaults`** tells you the exact destination:
   ```yaml
   pluginDefaults:
     - type: io.kestra.plugin.jdbc.postgresql
       values:
         url: jdbc:postgresql://pgdatabase:5432/ny_taxi
         username: root
         password: root
   ```
   This says: all Postgres tasks connect to `pgdatabase` (the container name from Docker Compose), port `5432`, database `ny_taxi`, with user `root`. That's the same Postgres you can browse in pgAdmin at `localhost:8085`.

3. **The SQL itself** tells you the exact table:
   ```yaml
   table: "public.{{inputs.taxi}}_tripdata"
   ```
   So yellow taxi data goes into `public.yellow_tripdata`, green goes into `public.green_tripdata`.

**In short:** the plugin type tells you *what* technology, `pluginDefaults` tells you *which* server, and the SQL/variables tell you *which table*. You piece it all together from the YAML.

**Quick checklist — tracing data in any Kestra flow:**
1. **Source** — look at the `extract` task's URL or command to see where data comes from
2. **Destination technology** — the plugin type tells you what it's talking to (Postgres, DuckDB, BigQuery, etc.)
3. **Exact destination** — `pluginDefaults` gives you the server/connection, SQL/variables give you the table name

### Q9: Do I always use pgAdmin to check Postgres data?

No. pgAdmin is just one tool — it's included in this `docker-compose.yml` as a convenience, not a requirement. If it wasn't in the compose file, Postgres would still work fine.

Other ways to check Postgres data:
- **pgAdmin** — browser UI (`localhost:8085`, because this compose file set it up)
- **psql** — command line tool (`psql -h localhost -p 5432 -U root -d ny_taxi`)
- **DBeaver, DataGrip, VS Code extensions** — other database GUIs
- **Any code** — Python with `psycopg2`, etc.

**How to remember:** Ask two questions:
1. **What database?** → read `pluginDefaults` in the YAML (e.g. `postgresql://pgdatabase:5432/ny_taxi`)
2. **How do I access it?** → read `docker-compose.yml` for available tools (pgAdmin on 8085, Postgres exposed on 5432)

### What we actually did with Flow 04 — end to end

1. **Docker Compose** spun up 4 containers (Postgres for data, Postgres for Kestra internals, Kestra, pgAdmin)
2. We gave Kestra a **YAML flow** through its UI at `localhost:8080`
3. Kestra executed it: **download CSV from GitHub → load into staging table → enrich rows with unique ID → merge into final Postgres table**
4. **Postgres** (running in a container) stores the data
5. **pgAdmin** (running in another container) lets us browse the data through the browser on localhost
6. Everything runs in containers on our machine, talking to each other over Docker's internal network. We access them through ports mapped to localhost.

This is workflow orchestration — you define *what* should happen in YAML, and Kestra handles the *how* and *when*.

### Q10: Why does Docker Desktop need to be running before using docker commands?

Docker commands (`docker`, `docker compose`) are just a **client** — they don't do anything on their own. They send instructions to the **Docker daemon**, a background process that actually creates and manages containers.

On Windows with WSL, Docker Desktop *is* the daemon. If it's not running, the daemon isn't running, and the client has nobody to talk to — so commands fail.

On a Linux server, the daemon runs as a system service (`dockerd`) with no Desktop app needed. On Windows/Mac, Docker Desktop bundles the daemon, client, and UI together.

---

## Flow 05: Scheduled Taxi Pipeline

Same tasks and SQL as flow 04. Three key differences:

### Difference 1: `trigger.date` replaces manual year/month inputs

```yaml
file: "{{inputs.taxi}}_tripdata_{{trigger.date | date('yyyy-MM')}}.csv"
```

Instead of picking year and month from dropdowns, the flow uses `trigger.date` — provided automatically by the schedule trigger. The flow figures out which month's data to download based on *when it was triggered*.

### Difference 2: Two schedule triggers

```yaml
triggers:
  - id: green_schedule
    cron: "0 9 1 * *"       # 9:00 AM on the 1st of every month
    inputs:
      taxi: green

  - id: yellow_schedule
    cron: "0 10 1 * *"      # 10:00 AM on the 1st of every month
    inputs:
      taxi: yellow
```

Staggered so they don't overlap.

### Difference 3: `concurrency: limit: 1`

Only one execution at a time. Prevents the staging table from being used by two runs simultaneously.

### Backfill

To load historical data, use **backfill** — tells Kestra to pretend the trigger fired for every month in a date range.

