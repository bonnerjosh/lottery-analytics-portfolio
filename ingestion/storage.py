import os
from datetime import datetime
from pathlib import Path

from google.cloud import bigquery, storage

def powerball_gcs():
    client = storage.Client(project=os.environ["GOOGLE_CLOUD_PROJECT"])
    bucket = client.bucket(os.environ["LOTTERY_BUCKET"])

    current_month = datetime.now().strftime("%Y-%m")

    raw_source_path = Path("./data/raw/powerball.pdf")

    parsed_source_path = Path("./data/parsed/powerball_data.jsonl")

    current_raw_pdf = bucket.blob("raw/powerball/current/powerball.pdf")
    current_raw_pdf.upload_from_filename(raw_source_path)

    snapshot_raw_pdf = bucket.blob(f"raw/powerball/snapshots/{current_month}-powerball.pdf")
    snapshot_raw_pdf.upload_from_filename(raw_source_path)

    parsed_data = bucket.blob("parsed/powerball/current/powerball.jsonl")
    parsed_data.upload_from_filename(parsed_source_path)

    print("Successfully saved data to GCS.")
    return True

def powerball_bigquery():
    project = os.environ["GOOGLE_CLOUD_PROJECT"]
    dataset = os.getenv("BIGQUERY_DATASET", "lottery_data")
    bucket = os.environ["LOTTERY_BUCKET"]
    client = bigquery.Client(project=project, location=os.getenv("BIGQUERY_LOCATION", "us-east1"))
    table_id = f"{project}.{dataset}.powerball"
    gcs_uri = f"gs://{bucket}/parsed/powerball/current/powerball.jsonl"

    job_config = bigquery.LoadJobConfig(
        source_format = bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition = "WRITE_TRUNCATE"
    )

    job = client.load_table_from_uri(gcs_uri, table_id, job_config=job_config)
    job.result()

    print("Successfully added data to powerball table.")
    return True
