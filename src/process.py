"""
Transforms and aggregates input data based on the data type.
Supports transactions, events, and metrics processing.
"""

import logging
from datetime import datetime, timezone
from collections import defaultdict

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class ProcessingError(Exception):
    """Raised when data processing encounters an unrecoverable error."""
    pass


def handler(event, context):
    """
    Process records based on their data type.
    Applies transformations and produces aggregated results.
    """
    data_type = event.get("dataType", "")
    records = event.get("records", [])
    source = event.get("source", "unknown")

    logger.info(
        "Processing %d records of type '%s' from '%s'",
        len(records), data_type, source
    )

    try:
        if data_type == "transactions":
            results = process_transactions(records)
        elif data_type == "events":
            results = process_events(records)
        elif data_type == "metrics":
            results = process_metrics(records)
        else:
            raise ProcessingError(f"Unknown data type: {data_type}")

    except ProcessingError:
        raise
    except Exception as e:
        logger.error("Processing failed: %s", str(e))
        raise ProcessingError(f"Failed to process records: {str(e)}")

    logger.info("Processing complete: %d result entries", len(results.get("summary", [])))

    return {
        "processedAt": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "dataType": data_type,
        "inputCount": len(records),
        "results": results,
    }


def process_transactions(records):
    """Aggregate transactions by category with totals and counts."""
    by_category = defaultdict(lambda: {"total": 0.0, "count": 0})

    for record in records:
        category = record.get("category", "uncategorized")
        amount = float(record.get("amount", 0))
        by_category[category]["total"] += amount
        by_category[category]["count"] += 1

    summary = []
    for category, data in sorted(by_category.items()):
        summary.append({
            "category": category,
            "totalAmount": round(data["total"], 2),
            "transactionCount": data["count"],
            "averageAmount": round(data["total"] / data["count"], 2) if data["count"] > 0 else 0,
        })

    grand_total = sum(item["totalAmount"] for item in summary)

    return {
        "summary": summary,
        "grandTotal": round(grand_total, 2),
        "categoryCount": len(summary),
    }


def process_events(records):
    """Aggregate events by type with frequency counts."""
    by_type = defaultdict(int)
    by_hour = defaultdict(int)

    for record in records:
        event_type = record.get("type", "unknown")
        by_type[event_type] += 1

        timestamp = record.get("timestamp", "")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                hour_key = dt.strftime("%Y-%m-%d %H:00")
                by_hour[hour_key] += 1
            except (ValueError, AttributeError):
                pass

    summary = [
        {"eventType": k, "count": v}
        for k, v in sorted(by_type.items(), key=lambda x: x[1], reverse=True)
    ]

    hourly = [
        {"hour": k, "count": v}
        for k, v in sorted(by_hour.items())
    ]

    return {
        "summary": summary,
        "hourlyDistribution": hourly,
        "uniqueEventTypes": len(by_type),
    }


def process_metrics(records):
    """Compute statistical aggregations for metric records."""
    by_metric = defaultdict(list)

    for record in records:
        name = record.get("name", "unknown")
        value = float(record.get("value", 0))
        by_metric[name].append(value)

    summary = []
    for name, values in sorted(by_metric.items()):
        values.sort()
        n = len(values)
        summary.append({
            "metric": name,
            "count": n,
            "min": round(values[0], 4),
            "max": round(values[-1], 4),
            "mean": round(sum(values) / n, 4),
            "median": round(values[n // 2], 4) if n % 2 == 1
                      else round((values[n // 2 - 1] + values[n // 2]) / 2, 4),
        })

    return {
        "summary": summary,
        "uniqueMetrics": len(by_metric),
    }
