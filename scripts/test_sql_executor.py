from agent.sql.executor import SQLExecutor
from agent.sql.validator import SQLValidator
from services.database.session import engine


def main() -> None:
    validator = SQLValidator()

    executor = SQLExecutor(
        engine=engine,
        validator=validator,
    )

    sql = """
    SELECT id, code, name, status
    FROM machines
    """

    result = executor.execute(sql)

    print("=" * 70)
    print("SQL Executor Test")
    print("=" * 70)

    print("\nColumns:")
    print(result.columns)

    print("\nRows:")

    for row in result.rows:
        print(row)

    print("\nRow Count:")
    print(result.row_count)

    print("\nExecution Time:")
    print(
        f"{result.execution_time_ms} ms"
    )

    print("\nTruncated:")
    print(result.truncated)


if __name__ == "__main__":
    main()