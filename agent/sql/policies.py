READ_ONLY_ALLOWED_TABLES = {
    "machines",
    "machine_alarms",
    "work_orders",
    "materials",
    "production_records",
    "knowledge_documents",
    "knowledge_chunks",    
}


BLOCKED_SQL_KEYWORDS = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "REPLACE",
    "MERGE",
    "GRANT",
    "REVOKE",
}


DEFAULT_MAX_ROWS = 100

ABSOLUTE_MAX_ROWS = 1000

DEFAULT_QUERY_TIMEOUT_MS = 5000