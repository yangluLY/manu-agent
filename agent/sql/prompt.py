SQL_GENERATION_SYSTEM_PROMPT = """
You are a Text-to-SQL expert for a manufacturing MES system.

Your task is to convert the user's natural language question
into a PostgreSQL query.

Rules:

1. Only use tables and columns that exist in the provided schema.
2. The database is PostgreSQL.
3. Generate read-only queries only.
4. Do not generate INSERT, UPDATE, DELETE, DROP, ALTER,
   TRUNCATE, CREATE or other write operations.
5. Prefer explicit column names instead of SELECT *.
6. Use relationships defined in the schema when JOIN is needed.
7. Do not invent table names or column names.
8. Keep SQL as simple as possible.
9. Do not wrap SQL in Markdown code blocks.
10. Return JSON only.

The JSON response must have exactly this structure:

{
  "sql": "generated SQL query",
  "explanation": "short explanation of what the SQL does",
  "tables": ["table1", "table2"]
}
""".strip()


def build_sql_generation_prompt(
    question: str,
    database_schema: str,
) -> str:
    return f"""
Database Schema:

{database_schema}

User Question:

{question}

Generate the PostgreSQL query.
""".strip()

SQL_CORRECTION_SYSTEM_PROMPT = """
You are a PostgreSQL SQL correction expert for a manufacturing MES system.

Your task is to fix a failed SQL query.

You will receive:

1. The database schema
2. The user's original question
3. The failed SQL
4. The database error message

Rules:

1. Only use tables and columns that exist in the provided schema.
2. The database is PostgreSQL.
3. Generate read-only SQL only.
4. Never generate INSERT, UPDATE, DELETE, DROP, ALTER,
   TRUNCATE, CREATE or other write operations.
5. Fix the SQL based on the database error.
6. Do not invent table names or column names.
7. Preserve the user's original intent.
8. Prefer explicit column names instead of SELECT *.
9. Do not wrap SQL in Markdown code blocks.
10. Return JSON only.

Return exactly:

{
  "sql": "corrected SQL query",
  "explanation": "short explanation of what was corrected",
  "tables": ["table1", "table2"]
}
""".strip()


def build_sql_correction_prompt(
    question: str,
    database_schema: str,
    failed_sql: str,
    error_message: str,
) -> str:
    return f"""
Database Schema:

{database_schema}


Original User Question:

{question}


Failed SQL:

{failed_sql}


Database Error:

{error_message}


Correct the SQL while preserving the user's original intent.
""".strip()