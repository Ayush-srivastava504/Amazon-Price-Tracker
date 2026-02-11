# Failure Scenarios & Handling

The pipeline is designed to fail safely without corrupting stored data.

## No Data Extracted
- Pipeline stops early
- No downstream steps are executed
- Prevents empty or invalid writes

## Individual Product Failure
- Errors handled per product
- Remaining products continue processing
- Failed products are logged

## Invalid or Missing Fields
- Detected during validation or quality checks
- Bad records skipped from clean tables
- Raw data preserved for debugging

## Database Write Failure
- Errors logged at record level
- Existing data remains unchanged
- Pipeline does not crash silently

## Dashboard Empty Results
- Empty datasets handled gracefully
- Charts render without breaking the UI

## Philosophy
- Fail fast on critical issues
- Continue on partial failures
- Never silently corrupt data
