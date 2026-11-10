# Powerball data quality API

Two read-only HTTP endpoints run in the Azure Functions Python runtime and
query the existing BigQuery `lottery_data.powerball_report` view. No Azure
subscription is needed to run the host locally.

Set up the [BigQuery reporting view](../README.md#run-the-powerball-pipeline)
first. From this directory, with Python 3.12 and Azure Functions Core Tools v4
installed, set the project, dataset, and location to match your view.

```sh
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export GOOGLE_CLOUD_PROJECT=your-project-id
export BIGQUERY_DATASET=lottery_data
export BIGQUERY_LOCATION=us-east1
export FUNCTIONS_WORKER_RUNTIME=python
export PYTHON_ISOLATE_WORKER_DEPENDENCIES=1
func start
```

The dependency isolation setting lets the BigQuery client use its own Protobuf
version alongside the Functions worker.

If Application Default Credentials are missing, run
`gcloud auth application-default login` before starting the host. The Google
identity needs read access to the view and its underlying table and permission
to run query jobs in the configured project.

```sh
curl -sS http://localhost:7071/api/health
curl -sS 'http://localhost:7071/api/draws?date=2026-03-23'
```

The health endpoint counts distinct duplicated date-and-game keys and counts
rows with invalid multipliers. On November 9, 2026, the view had 2,950 draw
records and zero exceptions for both checks. Counts can change with source data.
For March 23, 2026, expect a Powerball record with a multiplier of 10 and a
Double Play record with a null multiplier. The lookup returns 400 for missing
or invalid dates and 404 for dates with no draws.
