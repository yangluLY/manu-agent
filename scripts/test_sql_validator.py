from agent.sql.validator import SQLValidator


def main() -> None:
    validator = SQLValidator()

    test_cases = [
        (
            "正常 SELECT",
            """
            SELECT code, name, status
            FROM machines
            """,
        ),
        (
            "JOIN 查询",
            """
            SELECT
                m.code,
                COUNT(a.id) AS alarm_count
            FROM machines AS m
            LEFT JOIN machine_alarms AS a
                ON a.machine_id = m.id
            GROUP BY m.id, m.code
            """,
        ),
        (
            "DELETE",
            """
            DELETE FROM machines
            WHERE id = 1
            """,
        ),
        (
            "UPDATE",
            """
            UPDATE machines
            SET status = 'offline'
            WHERE id = 1
            """,
        ),
        (
            "DROP",
            """
            DROP TABLE machines
            """,
        ),
        (
            "非法表",
            """
            SELECT *
            FROM users
            """,
        ),
        (
            "多条 SQL",
            """
            SELECT * FROM machines;
            DELETE FROM machines;
            """,
        ),
    ]

    for name, sql in test_cases:
        result = validator.validate(sql)

        print("\n" + "=" * 70)
        print(name)
        print("=" * 70)

        print(f"Valid: {result.is_valid}")

        if result.errors:
            print("Errors:")

            for error in result.errors:
                print(f"- {error}")

        if result.warnings:
            print("Warnings:")

            for warning in result.warnings:
                print(f"- {warning}")


if __name__ == "__main__":
    main()