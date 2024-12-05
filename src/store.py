"""
Stores processed pipeline results in S3 as JSON.
Organizes output by date and source for easy retrieval.
"""

import os
import json
import logging
from datetime import datetime, timezone

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")


def handler(event, context):
    """
    Store processing results in S3.

    The output is organized by date and source:
      s3://<bucket>/results/<date>/<source>/<timestamp>.json
    """
    processing = event.get("processing", {})
    source = processing.get("source", "unknown")
    data_type = processing.get("dataType", "unknown")
    results = processing.get("results", {})

    bucket = os.environ.get("RESULTS_BUCKET", event.get("resultsBucket", ""))
    if not bucket:
        raise ValueError("No results bucket configured")

    now = datetime.now(timezone.utc)
    date_prefix = now.strftime("%Y/%m/%d")
    timestamp = now.strftime("%Y%m%dT%H%M%SZ")

    key = f"results/{date_prefix}/{source}/{data_type}_{timestamp}.json"

    output = {
        "source": source,
        "dataType": data_type,
        "processedAt": processing.get("processedAt", now.isoformat()),
        "inputCount": processing.get("inputCount", 0),
        "results": results,
    }

    body = json.dumps(output, indent=2, default=str)

    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        ContentType="application/json",
    )

    logger.info("Stored results to s3://%s/%s (%d bytes)", bucket, key, len(body))

    return {
        "bucket": bucket,
        "key": key,
        "sizeBytes": len(body),
        "storedAt": now.isoformat(),
    }
