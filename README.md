# Lottery Analytics Data Platform

**Status:** Initial Development
**Version:** 0.1
**Purpose:** End-to-end data engineering and analytics learning project

The Powerball pipeline loads historical draw records into BigQuery. The
[Azure Functions API](azure-functions/README.md) queries the
[BigQuery reporting view](reporting/powerball_report.sql) to return data
quality metrics and look up draws by date. The API runs locally on Linux.
The sections below describe the broader project roadmap.

## Run the Powerball pipeline

Use a Google Cloud project with BigQuery and Cloud Storage enabled, the
Google Cloud CLI, and Python 3.12. Set the following in your shell, replacing
the project and bucket names with your own values.

```sh
export GOOGLE_CLOUD_PROJECT=your-project-id
export LOTTERY_BUCKET=your-globally-unique-bucket-name
export BIGQUERY_DATASET=lottery_data
export BIGQUERY_LOCATION=us-east1
gcloud auth login
gcloud auth application-default login
```

Use an existing bucket in the BigQuery dataset's location or create one
with Terraform.

```sh
export TF_VAR_project_id="$GOOGLE_CLOUD_PROJECT"
export TF_VAR_bucket_name="$LOTTERY_BUCKET"
export TF_VAR_location="$BIGQUERY_LOCATION"
terraform init
terraform plan
terraform apply
```

Create the dataset and its source table once. Skip these commands if both
already exist.

```sh
bq --location="$BIGQUERY_LOCATION" mk --dataset "$GOOGLE_CLOUD_PROJECT:$BIGQUERY_DATASET"
bq mk --table "$GOOGLE_CLOUD_PROJECT:$BIGQUERY_DATASET.powerball" \
  'draw_date:DATE,ball1:INT64,ball2:INT64,ball3:INT64,ball4:INT64,ball5:INT64,powerball:INT64,multiplier:INT64,game_type:STRING'
```

From the repository root, install the ingestion dependencies, load the
historical records, and create the reporting view. Each ingestion run
replaces the contents of the source table with the current draw history.

```sh
python3.12 -m venv .venv
source .venv/bin/activate
pip install requests beautifulsoup4 pdfplumber google-cloud-storage google-cloud-bigquery
python ingestion/get_data.py
sed -e "s/PROJECT_ID/$GOOGLE_CLOUD_PROJECT/g" -e "s/DATASET_ID/$BIGQUERY_DATASET/g" \
  reporting/powerball_report.sql |
  bq --project_id="$GOOGLE_CLOUD_PROJECT" --location="$BIGQUERY_LOCATION" query --use_legacy_sql=false
```

Follow the [API setup instructions](azure-functions/README.md) in the same
shell to run Azure Functions locally.

## 1. Objective

Build a private, production-oriented U.S. lottery analytics platform that demonstrates an end-to-end data engineering workflow:

**External Sources → Python Ingestion → Raw Data → BigQuery → dbt/SQL → Data Quality → Analytics → Apache Superset**

The platform will ingest historical and ongoing lottery data, normalize inconsistent source schemas, and enable analysis of lottery draws, winning numbers, jackpots, winners, retailers, and winning-ticket geography.

The primary learning objective is to confidently demonstrate the ability to design and build a complete data pipeline rather than simply analyze a pre-existing dataset.

---

## 2. Initial Scope

### Games

The MVP will initially support:

* Powerball
* Mega Millions

The architecture must support adding additional games and state lotteries without requiring a fundamental redesign.

### Future Expansion

Potential additions include:

* Florida Lottery games
* Other state lottery games
* Additional draw games
* Additional winner and retailer information

The MVP will **not** attempt to cover every U.S. lottery.

---

## 3. Core Data Domains

### Games

Represents the lottery game and its characteristics.

Potential attributes:

* `game_id`
* `game_name`
* `state`
* `game_type`
* `draw_frequency`

### Draws

Represents an individual lottery drawing.

Potential attributes:

* `draw_id`
* `game_id`
* `draw_date`
* `draw_time`
* `jackpot`
* `multiplier`
* `estimated_cash_value`
* `drawing_number`

### Winning Numbers

Represents numbers drawn for each drawing.

Potential attributes:

* `draw_id`
* `number`
* `number_type`
* `ball_position`

The canonical model should support different lottery formats rather than hard-coding a fixed number of columns.

### Winners

Represents winning tickets or winning outcomes where source data is available.

Potential attributes:

* `winner_id`
* `draw_id`
* `prize_tier`
* `prize_amount`
* `number_of_winning_tickets`

### Retailers / Ticket Locations

Represents the retailer or location associated with a winning ticket where available.

Potential attributes:

* `retailer_id`
* `retailer_name`
* `retailer_address`
* `ticket_city`
* `ticket_state`
* `ticket_zip`

---

## 4. Winner Geography Definition

**Winning-ticket geography is not necessarily winner residence geography.**

Unless a source explicitly provides residence information, geographic analysis will represent the location associated with the winning ticket, such as the retailer or city/state where the ticket was sold.

The platform must not infer a winner's residence from ticket-sale location.

If residence information is unavailable, residence fields remain `NULL`.

---

## 5. Data Source Strategy

Sources should be prioritized as follows:

1. Official lottery authority sources
2. Government/open-data sources
3. Structured third-party APIs
4. Other reliable sources when necessary

Sources will be evaluated for:

* Historical coverage
* Data completeness
* Reliability
* Accessibility
* Update frequency
* Schema consistency
* Licensing/usage considerations
* Winner and retailer availability

The first implementation will establish and validate the Powerball source before expanding to Mega Millions.

---

## 6. Data Architecture

Source-specific schemas must not dictate the analytical model.

```text
External Lottery Sources
          ↓
   Python Ingestion
          ↓
      Raw Data
          ↓
       BigQuery
          ↓
   dbt Staging Models
          ↓
 Intermediate Models
          ↓
   Analytics Marts
          ↓
   Data Quality Tests
          ↓
      Superset
```

The platform should separate source-specific ingestion/staging from canonical analytical models so additional games can be incorporated consistently.

---

## 7. Technology Stack

| Layer              | Technology      |
| ------------------ | --------------- |
| Programming        | Python          |
| Data Warehouse     | Google BigQuery |
| Transformation     | dbt + SQL       |
| Infrastructure     | Terraform       |
| Containerization   | Docker          |
| BI / Visualization | Apache Superset |
| Version Control    | Git / GitHub    |

Future tooling for orchestration, scheduling, monitoring, object storage, and CI/CD remains TBD.

---

## 8. Initial Repository Structure

```text
lottery-analytics/
├── README.md
├── .gitignore
├── .env.example
│
├── docker/
│
├── infrastructure/
│   └── terraform/
│
├── ingestion/
│   ├── powerball/
│   ├── mega_millions/
│   └── common/
│
├── data/
│   └── README.md
│
├── dbt/
│   ├── models/
│   │   ├── staging/
│   │   ├── intermediate/
│   │   └── marts/
│   ├── tests/
│   ├── macros/
│   └── dbt_project.yml
│
├── sql/
├── dashboards/
├── tests/
│
└── docs/
    ├── architecture.md
    ├── data_sources.md
    └── data_dictionary.md
```

The structure is a target architecture; components will be implemented incrementally.

---

## 9. Initial Data Model Direction

The eventual analytical model is expected to include concepts such as:

```text
dim_game
dim_retailer
dim_location

fact_draw
fact_draw_numbers
fact_winner
fact_winning_ticket
```

The exact physical schema will be determined after inspecting real source data. The project should avoid prematurely designing a complex model that is not supported by the available data.

---

## 10. Data Quality

The pipeline should eventually validate:

### Draws

* Unique draw identifiers
* Non-null draw dates
* Valid game relationships
* No duplicate draws
* Valid dates and expected draw frequency

### Winning Numbers

* Valid number ranges
* Expected number counts
* Valid number types
* Duplicate-number rules appropriate to each game

### Relationships

* Draw → Game
* Draw → Winning Numbers
* Draw → Winners
* Winning Ticket → Retailer

Where applicable, dbt tests should enforce these expectations.

---

## 11. Historical and Incremental Loading

The platform must support both:

* Initial historical backfill
* Incremental ingestion of new drawings

The initial implementation may load historical data in a simple manner. Incremental loading strategy, partitioning, and optimization will be established after the first source is understood.

---

## 12. Analytics Requirements

The platform should eventually support questions including:

### Draw Analysis

* Number frequency
* Number-pair and combination frequency
* Jackpot trends
* Jackpot rollover behavior
* Draw frequency
* Historical jackpot distributions

### Winner Analysis

* Winning tickets by state
* Winning tickets by city
* Winning tickets by retailer
* Prize distributions
* Geographic concentration of winning tickets

### Game Comparison

* Powerball vs. Mega Millions jackpot behavior
* Jackpot frequency and size
* Winning-ticket geographic distribution
* Other comparable metrics supported by available data

Analytics should describe historical patterns and distributions; the project is **not intended to create a lottery-number prediction system**.

---

## 13. Data Lineage and Reproducibility

The pipeline should make it possible to determine:

* Where data originated
* When it was retrieved
* Which source was used
* How it was transformed
* Which pipeline/code version produced the output
* Whether data-quality tests passed

Where practical, ingestion metadata should include fields such as:

* `source`
* `source_url`
* `ingested_at`
* `pipeline_run_id`
* `source_record_id`

Exact metadata requirements remain TBD.

---

## 14. Open Decisions

The following decisions remain intentionally unresolved and should be made as implementation progresses:

* Exact Powerball source
* Exact Mega Millions source
* Final raw-storage strategy
* BigQuery dataset structure
* Final canonical/star schema
* Exact dbt model naming
* Incremental loading strategy
* Partitioning/clustering strategy
* Orchestration technology
* Scheduling approach
* CI/CD implementation
* Monitoring and alerting
* Superset deployment strategy
* Extent and availability of winner/retailer data across games

These decisions should be documented as they are made rather than assumed in advance.

---

## 15. MVP Non-Goals

The initial MVP will not require:

* Every U.S. lottery
* Every state
* Complete winner information for every game
* Winner residence data
* Real-time ingestion
* Machine learning
* Number prediction
* A custom application frontend
* Sophisticated cloud orchestration
* Full production deployment
* Numerous dashboards

The priority is demonstrating sound data engineering practices.

---

## 16. Development Approach

The project will be developed incrementally through vertical slices.

### First vertical slice

```text
Powerball Source
      ↓
Python Ingestion
      ↓
Raw Data
      ↓
BigQuery
      ↓
dbt Staging
      ↓
dbt Tests
      ↓
Analytics Model
```

Once the first pipeline works end-to-end, the project will expand to Mega Millions, winner/ticket geography, additional analytics, automation, and production-oriented infrastructure.

The project is intended as a learning exercise. Architecture, schema, SQL, dbt, testing, infrastructure, and implementation decisions should be reasoned through and documented rather than blindly copied from generated code.

---

## 17. Definition of Done

The platform will be considered successful when it can reliably demonstrate:

1. Data retrieved from an external lottery source.
2. Programmatic ingestion using Python.
3. Raw data stored in BigQuery.
4. Data transformed using dbt and SQL.
5. Automated data-quality testing.
6. Canonical analytical models supporting multiple lottery games.
7. Winner/ticket geography incorporated where source data permits.
8. Analytics exposed through Apache Superset.
9. A second lottery game added without redesigning the core architecture.
10. Clear documentation of sources, architecture, data definitions, and lineage.

**Target outcome:**

> Build and explain a complete, reproducible data pipeline from external source to analytical dashboard using modern data-engineering tooling.
