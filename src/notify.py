"""
Publishes pipeline completion or failure notifications to SNS.
"""

import os
import json
import logging
from datetime import datetime, timezone

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sns = boto3.client("sns")


def handler(event, context):
    """
    Send a notification about pipeline completion or failure.
    Inspects the event payload to determine the outcome and build
    an appropriate message.
    """
    topic_arn = os.environ.get("SNS_TOPIC_ARN", "")
    if not topic_arn:
        logger.warning("SNS_TOPIC_ARN not configured, skipping notification")
        return {"notified": False, "reason": "No topic configured"}

    failure_info = event.get("failureInfo")
    is_failure = failure_info is not None

    if is_failure:
        subject = "Pipeline Failed"
        message = build_failure_message(event, failure_info)
    else:
        subject = "Pipeline Completed Successfully"
        message = build_success_message(event)

    sns.publish(
        TopicArn=topic_arn,
        Subject=subject,
        Message=message,
    )

    logger.info("Notification sent: %s", subject)

    return {
        "notified": True,
        "subject": subject,
        "status": "FAILED" if is_failure else "SUCCESS",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def build_success_message(event):
    """Build a human-readable success notification message."""
    processing = event.get("processing", {})
    storage = event.get("storage", {})

    lines = [
        "Data Processing Pipeline - Completed Successfully",
        "=" * 50,
        "",
        f"Source:      {processing.get('source', 'N/A')}",
        f"Data Type:   {processing.get('dataType', 'N/A')}",
        f"Records:     {processing.get('inputCount', 'N/A')}",
        f"Processed:   {processing.get('processedAt', 'N/A')}",
        "",
        "Storage:",
        f"  Bucket:    {storage.get('bucket', 'N/A')}",
        f"  Key:       {storage.get('key', 'N/A')}",
        f"  Size:      {storage.get('sizeBytes', 'N/A')} bytes",
        "",
        "Results Summary:",
    ]

    results = processing.get("results", {})
    summary = results.get("summary", [])
    for item in summary[:10]:
        lines.append(f"  - {json.dumps(item, default=str)}")

    if len(summary) > 10:
        lines.append(f"  ... and {len(summary) - 10} more entries")

    return "\n".join(lines)


def build_failure_message(event, failure_info):
    """Build a human-readable failure notification message."""
    lines = [
        "Data Processing Pipeline - FAILED",
        "=" * 50,
        "",
        f"Stage:   {failure_info.get('stage', 'unknown')}",
        f"Status:  {failure_info.get('status', 'FAILED')}",
        "",
        "Error Details:",
        json.dumps(failure_info.get("error", {}), indent=2, default=str),
        "",
        "Input Context:",
        f"  Source:    {event.get('source', 'N/A')}",
        f"  Data Type: {event.get('dataType', 'N/A')}",
    ]

    return "\n".join(lines)
