from powerball import ingest_powerball
from storage import powerball_gcs, powerball_bigquery

data_ingestion = ingest_powerball()
if data_ingestion:
    storage = powerball_gcs()
    if storage:
        bigquery = powerball_bigquery()
        if bigquery is True:
            print("Pipeline success")
        else:
            print("BigQuery load failed")
    else:
        print("Storage failed")
else:
    print("Ingestion failed")