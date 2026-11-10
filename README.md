# Lottery Analytics

An end-to-end data pipeline that loads historical Powerball and Double Play
draws into Google BigQuery and exposes the results through a Python API running
on Azure Functions.

## What it does

- Extracts and validates historical lottery draw data
- Stores raw files in Google Cloud Storage
- Loads normalized records into BigQuery
- Builds a reporting view for analytics and data-quality checks
- Provides API endpoints for pipeline health and draw lookup by date

## Architecture

```text
Lottery source → Python ingestion → Cloud Storage → BigQuery → Azure Functions API
```

## Tech stack

Python, Google Cloud Storage, BigQuery, SQL, Terraform, Azure Functions, and
unit tests.

## API endpoints

```text
GET /api/health
GET /api/draws?date=2026-03-23
```

`health` returns record counts and data-quality results. `draws` returns the
Powerball and Double Play results for a requested date.

## Run locally

Requirements: Python 3.12, Google Cloud CLI, BigQuery, Cloud Storage, and Azure
Functions Core Tools v4.

Set your Google Cloud configuration and authenticate:

```sh
export GOOGLE_CLOUD_PROJECT=your-project-id
export LOTTERY_BUCKET=your-unique-bucket-name
export BIGQUERY_DATASET=lottery_data
export BIGQUERY_LOCATION=us-east1
gcloud auth application-default login
```

Create the storage bucket with Terraform:

```sh
export TF_VAR_project_id="$GOOGLE_CLOUD_PROJECT"
export TF_VAR_bucket_name="$LOTTERY_BUCKET"
export TF_VAR_location="$BIGQUERY_LOCATION"
terraform init
terraform apply
```

Create the BigQuery dataset and table:

```sh
bq --location="$BIGQUERY_LOCATION" mk --dataset "$GOOGLE_CLOUD_PROJECT:$BIGQUERY_DATASET"
bq mk --table "$GOOGLE_CLOUD_PROJECT:$BIGQUERY_DATASET.powerball" \
  'draw_date:DATE,ball1:INT64,ball2:INT64,ball3:INT64,ball4:INT64,ball5:INT64,powerball:INT64,multiplier:INT64,game_type:STRING'
```

Install the ingestion dependencies and load the data:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
pip install requests beautifulsoup4 pdfplumber google-cloud-storage google-cloud-bigquery
python ingestion/get_data.py
```

Create the reporting view:

```sh
sed -e "s/PROJECT_ID/$GOOGLE_CLOUD_PROJECT/g" \
    -e "s/DATASET_ID/$BIGQUERY_DATASET/g" \
    reporting/powerball_report.sql | \
  bq --project_id="$GOOGLE_CLOUD_PROJECT" \
     --location="$BIGQUERY_LOCATION" query --use_legacy_sql=false
```

See [azure-functions/README.md](azure-functions/README.md) to start and test the
API locally.

## Tests

```sh
python -m unittest discover -s tests -v
```
