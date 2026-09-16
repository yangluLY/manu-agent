from services.database.models.machine import Machine

# ============================================================
# Test Data
# ============================================================

def create_test_machine(
    db_session,
    code="MC-TEST-001",
):

    machine = Machine(
        code=code,
        name="测试CNC设备",
        model="VMC-850",
        line_code="LINE-A",
        status="running",
    )

    db_session.add(machine)

    db_session.commit()

    db_session.refresh(machine)

    return machine


# ============================================================
# Machine List
# ============================================================

def test_machine_list(
    client,
    db_session,
):

    create_test_machine(
        db_session,
        "MC-TEST-001",
    )

    create_test_machine(
        db_session,
        "MC-TEST-002",
    )

    response = client.get(
        "/api/v1/machines"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    assert len(data) == 2

    codes = [
        item["code"]
        for item in data
    ]

    assert "MC-TEST-001" in codes

    assert "MC-TEST-002" in codes


# ============================================================
# Machine Detail
# ============================================================

def test_machine_detail(
    client,
    db_session,
):

    machine = create_test_machine(
        db_session
    )

    response = client.get(
        f"/api/v1/machines/{machine.id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == machine.id

    assert data["code"] == "MC-TEST-001"

    assert data["name"] == "测试CNC设备"

    assert data["model"] == "VMC-850"

    assert data["line_code"] == "LINE-A"

    assert data["status"] == "running"


# ============================================================
# Machine Not Found
# ============================================================

def test_machine_detail_not_found(
    client,
):

    response = client.get(
        "/api/v1/machines/99999"
    )

    assert response.status_code == 404


# ============================================================
# Create Machine
# ============================================================

def test_create_machine(
    client,
):

    payload = {
        "code": "MC-TEST-003",
        "name": "测试注塑机",
        "model": "MA1600",
        "line_code": "LINE-B",
        "status": "running",
    }

    response = client.post(
        "/api/v1/machines",
        json=payload,
    )

    assert response.status_code in (
        200,
        201,
    )

    data = response.json()

    assert data["code"] == "MC-TEST-003"

    assert data["name"] == "测试注塑机"

    assert data["model"] == "MA1600"

    assert data["line_code"] == "LINE-B"

    assert data["status"] == "running"

    assert "id" in data