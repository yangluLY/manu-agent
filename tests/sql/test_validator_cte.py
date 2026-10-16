
import pytest

from agent.sql.validator import SQLValidator


@pytest.fixture
def validator():
    return SQLValidator(
        allowed_tables={
            "machines",
            "machine_alarms",
        }
    )


def test_normal_select(validator):
    sql = """
    SELECT id
    FROM machine_alarms
    """

    result = validator.validate(sql)

    assert result.is_valid is True


def test_cte_select(validator):
    sql = """
    WITH recent_alarms AS (
        SELECT
            machine_id,
            COUNT(*) AS alarm_count
        FROM machine_alarms
        GROUP BY machine_id
    )
    SELECT
        machine_id,
        alarm_count
    FROM recent_alarms
    """

    result = validator.validate(sql)

    assert result.is_valid is True
    assert result.errors == []


def test_unauthorized_table(validator):
    sql = """
    SELECT *
    FROM alarms
    """

    result = validator.validate(sql)

    assert result.is_valid is False
    assert any(
        "alarms" in error
        for error in result.errors
    )


def test_unauthorized_table_in_cte(validator):
    sql = """
    WITH recent_alarms AS (
        SELECT id
        FROM secret_records
    )
    SELECT *
    FROM recent_alarms
    """

    result = validator.validate(sql)

    assert result.is_valid is False
    assert any(
        "secret_records" in error
        for error in result.errors
    )


def test_write_operation_rejected(validator):
    sql = """
    DELETE FROM machine_alarms
    """

    result = validator.validate(sql)

    assert result.is_valid is False
