from datetime import datetime

from services.database.models.alarm import MachineAlarm
from services.database.models.machine import Machine


def create_machine(
    db_session,
):

    machine = Machine(
        code="MC-ALARM-001",
        name="报警测试设备",
        model="CK6150",
        line_code="LINE-A",
        status="running",
    )

    db_session.add(machine)

    db_session.commit()

    db_session.refresh(machine)

    return machine


def create_alarm(
    db_session,
    machine_id: int,
):

    alarm = MachineAlarm(
        machine_id=machine_id,
        alarm_code="E101",
        alarm_message="主轴温度过高",
        level="high",
        started_at=datetime(  # noqa: DTZ001
            2026,
            9,
            15,
            10,
            30,
        ),
        ended_at=None,
    )

    db_session.add(alarm)

    db_session.commit()

    db_session.refresh(alarm)

    return alarm


# ============================================================
# Alarm Query
# ============================================================

def test_alarm_query(
    client,
    db_session,
):

    machine = create_machine(
        db_session
    )

    alarm = create_alarm(  # noqa: F841
        db_session,
        machine.id,
    )

    response = client.get(
        "/api/v1/alarms",
        params={
            "machine_id": machine.id
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    assert len(data) >= 1

    alarm_data = data[0]

    assert alarm_data["machine_id"] == machine.id

    assert alarm_data["alarm_code"] == "E101"

    assert (
        alarm_data["alarm_message"]
        == "主轴温度过高"
    )

    assert alarm_data["level"] == "high"


# ============================================================
# Alarm Query Empty
# ============================================================

def test_alarm_query_empty(
    client,
):

    response = client.get(
        "/api/v1/alarms",
        params={
            "machine_id": 99999
        },
    )

    assert response.status_code == 200

    assert response.json() == []