"""
Validates input data format and schema before processing.
Raises ValidationError if the input does not meet requirements.
"""

import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

REQUIRED_FIELDS = ["source", "dataType", "records"]
SUPPORTED_DATA_TYPES = ["transactions", "events", "metrics"]
MAX_RECORDS = 10000


class ValidationError(Exception):
    """Raised when input data fails validation checks."""
    pass


def handler(event, context):
    """
    Validate the input payload structure and contents.

    Expected input format:
    {
        "source": "system-name",
        "dataType": "transactions|events|metrics",
        "records": [...]
    }
    """
    logger.info("Validating input data")

    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in event:
            raise ValidationError(f"Missing required field: {field}")

    source = event["source"]
    data_type = event["dataType"]
    records = event["records"]

    # Validate source
    if not isinstance(source, str) or len(source.strip()) == 0:
        raise ValidationError("Field 'source' must be a non-empty string")

    # Validate data type
    if data_type not in SUPPORTED_DATA_TYPES:
        raise ValidationError(
            f"Unsupported dataType: {data_type}. "
            f"Must be one of: {', '.join(SUPPORTED_DATA_TYPES)}"
        )

    # Validate records
    if not isinstance(records, list):
        raise ValidationError("Field 'records' must be an array")

    if len(records) == 0:
        raise ValidationError("Field 'records' must not be empty")

    if len(records) > MAX_RECORDS:
        raise ValidationError(
            f"Too many records: {len(records)}. Maximum allowed: {MAX_RECORDS}"
        )

    # Validate individual records have required structure
    for i, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValidationError(f"Record at index {i} must be an object")
        if "id" not in record:
            raise ValidationError(f"Record at index {i} is missing required field 'id'")

    logger.info(
        "Validation passed: source=%s, dataType=%s, records=%d",
        source, data_type, len(records)
    )

    return {
        "valid": True,
        "source": source,
        "dataType": data_type,
        "recordCount": len(records),
    }
