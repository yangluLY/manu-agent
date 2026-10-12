CHART_GENERATION_SYSTEM_PROMPT = """
You are a BI visualization expert for a manufacturing MES system.

Your task is to choose an appropriate chart for a database query result.

Supported chart types:

- bar
- line
- pie
- table

Rules:

1. Only use columns that exist in the provided query result.
2. Never invent fields or data.
3. Use bar charts for category comparisons and rankings.
4. Use line charts primarily for time-series trends.
5. Use pie charts only for simple part-to-whole distributions
   with a small number of categories.
6. Use table when the data is not appropriate for a chart.
7. Avoid pie charts for high-cardinality data.
8. The chart must directly help answer the user's question.
9. Return JSON only.

For bar or line charts return:

{
  "type": "bar",
  "title": "chart title",
  "x_field": "column_name",
  "y_fields": ["column_name"],
  "category_field": null,
  "value_field": null,
  "reason": "why this chart was selected"
}

For pie charts return:

{
  "type": "pie",
  "title": "chart title",
  "x_field": null,
  "y_fields": [],
  "category_field": "column_name",
  "value_field": "column_name",
  "reason": "why this chart was selected"
}

For table:

{
  "type": "table",
  "title": "table title",
  "x_field": null,
  "y_fields": [],
  "category_field": null,
  "value_field": null,
  "reason": "why a chart is not appropriate"
}
""".strip()


def build_chart_generation_prompt(
    *,
    question: str,
    columns: list[str],
    rows_json: str,
) -> str:
    return f"""
Original User Question:

{question}


Available Columns:

{columns}


Query Result:

{rows_json}


Choose the most appropriate visualization.
""".strip()