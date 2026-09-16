from platform import machine

from services.database.models.machine import Machine


def create_machine(
    db_session,
):

    machine = Machine(
        code="MC-WO-001",
        name="工单测试设备",
        model="VMC-850",
        line_code="LINE-A",
        status="running",
    )

    db_session.add(machine)

    db_session.commit()

    db_session.refresh(machine)

    return machine


# ============================================================
# Create Work Order
# ============================================================

def test_create_work_order(
    client,
    db_session,
):

    machine = create_machine(
        db_session
    )

    payload = {
        "machine_id": machine.id,
        "type": "repair",
        "priority": "high",
        "description": "检查主轴温度异常问题",
        "status": "pending",
        "assigned_to": "张工",
    }

    response = client.post(
        "/api/v1/work-orders",
        json=payload,
    )

    assert response.status_code in (
        200,
        201,
    )

    data = response.json()

    assert "order_no" in data
    assert data["order_no"] is not None
    assert data["order_no"].startswith("WO-")

    assert data["machine_id"] == (
        machine.id
    )

    assert data["type"] == "repair"

    assert data["priority"] == "high"

    assert data["status"] == "pending"

    assert data["assigned_to"] == "张工"

    assert "id" in data