# Step Functions Pipeline

AWS Step Functions data processing workflow with validation, transformation, storage, and notifications.

## Overview

A serverless data processing pipeline orchestrated by AWS Step Functions. The workflow validates incoming data, transforms and aggregates it, stores results in S3, and sends completion notifications via SNS.

## Architecture

```
Input -> ValidateInput -> ProcessData -> StoreResults -> NotifyComplete
              |                |              |
              v                v              v
        ValidationError   ProcessingError  StorageError
              |                |              |
              +--------> NotifyFailure <------+
```

### Pipeline Steps

1. **ValidateInput**: Checks required fields, data types, and record limits
2. **ProcessData**: Transforms and aggregates records based on data type (transactions, events, metrics)
3. **StoreResults**: Writes processed output to S3, organized by date and source
4. **NotifyComplete**: Publishes success notification to SNS

Error handling catches failures at each stage and routes to a failure notification path.

## Supported Data Types

| Type | Processing |
|------|-----------|
| `transactions` | Aggregates by category with totals, counts, averages |
| `events` | Frequency counts by type, hourly distribution |
| `metrics` | Statistical summaries (min, max, mean, median) |

## Tech Stack

- Python 3.12
- AWS Step Functions (ASL)
- AWS Lambda
- Amazon S3
- Amazon SNS
- AWS SAM

## Getting Started

### Prerequisites

- Python 3.12+
- AWS SAM CLI
- AWS credentials configured

### Deploy

```bash
sam build
sam deploy --guided \
  --parameter-overrides NotificationEmail=your-email@example.com
```

### Test Execution

Start a pipeline execution via the AWS CLI:

```bash
aws stepfunctions start-execution \
  --state-machine-arn <your-state-machine-arn> \
  --input '{
    "source": "test-system",
    "dataType": "transactions",
    "records": [
      {"id": "1", "category": "electronics", "amount": 299.99},
      {"id": "2", "category": "books", "amount": 19.95},
      {"id": "3", "category": "electronics", "amount": 149.50}
    ]
  }'
```

## Input Format

```json
{
  "source": "system-name",
  "dataType": "transactions|events|metrics",
  "records": [
    {"id": "1", ...}
  ]
}
```

All records must include an `id` field. Additional fields depend on the data type.

## License

MIT
