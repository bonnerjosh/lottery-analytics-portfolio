import json
import logging
import os
import re
from datetime import date

import azure.functions as func
from google.api_core.exceptions import GoogleAPIError
from google.auth.exceptions import GoogleAuthError
from google.cloud import bigquery

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

def response(body, status=200):
    return func.HttpResponse(
        json.dumps(body, default=date.isoformat),
        status_code=status,
        mimetype="application/json",
    )


def query(sql, parameters=()):
    project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    dataset = os.getenv("BIGQUERY_DATASET", "lottery_data")
    if not re.fullmatch(r"[a-z][a-z0-9-]{4,28}[a-z0-9]", project):
        raise ValueError("Set GOOGLE_CLOUD_PROJECT to a valid Google Cloud project ID.")
    if not re.fullmatch(r"[A-Za-z0-9_]{1,1024}", dataset):
        raise ValueError("Set BIGQUERY_DATASET to a valid BigQuery dataset ID.")
    report_view = f"`{project}.{dataset}.powerball_report`"
    client = bigquery.Client(project=project, location=os.getenv("BIGQUERY_LOCATION", "us-east1"))
    config = bigquery.QueryJobConfig(
        query_parameters=list(parameters),
        maximum_bytes_billed=100 * 1024 * 1024,
    )
    return [dict(row) for row in client.query_and_wait(
        sql.format(report_view=report_view), job_config=config, wait_timeout=20
    )]


@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    try:
        metrics, = query("""
            WITH draw_keys AS (
                SELECT draw_date, game_type, COUNT(*) AS row_count,
                    COUNTIF(invalid_multiplier) AS invalid_count
                FROM {report_view}
                GROUP BY draw_date, game_type
            )
            SELECT
                COALESCE(SUM(row_count), 0) AS draw_count,
                MAX(draw_date) AS latest_draw_date,
                COUNTIF(row_count > 1) AS duplicate_draw_keys,
                COALESCE(SUM(invalid_count), 0) AS invalid_multiplier_rows
            FROM draw_keys
        """)
    except (GoogleAPIError, GoogleAuthError, TimeoutError, ValueError):
        logging.exception("Could not query Powerball data quality metrics")
        return response({"error": "Draw data is temporarily unavailable."}, 503)

    return response(metrics)


@app.route(route="draws", methods=["GET"])
def draws(req: func.HttpRequest) -> func.HttpResponse:
    value = req.params.get("date", "")
    try:
        draw_date = date.fromisoformat(value)
        if draw_date.isoformat() != value:
            raise ValueError("Noncanonical date")
    except ValueError:
        return response({"error": "Provide date as YYYY-MM-DD."}, 400)

    try:
        results = query(
            """
            SELECT draw_date, game_name, white_balls, powerball, multiplier
            FROM {report_view}
            WHERE draw_date = @draw_date
            ORDER BY game_type
            """,
            [bigquery.ScalarQueryParameter("draw_date", "DATE", draw_date)],
        )
    except (GoogleAPIError, GoogleAuthError, TimeoutError, ValueError):
        logging.exception("Could not look up Powerball draws")
        return response({"error": "Draw data is temporarily unavailable."}, 503)

    if not results:
        return response({"error": "No draws found for this date."}, 404)

    return response({"draws": results})
