def test_not_found_exception_is_handled(client):
    response = client.get("/api/v1/materials/99999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Material not found",
    }


def test_bad_request_exception_is_handled(client):
    response = client.get(
        "/api/v1/production-records",
        params={
            "start_date": "2026-09-16",
            "end_date": "2026-09-15",
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Start date cannot be later than end date",
    }


def test_conflict_exception_is_handled(client):
    payload = {
        "code": "MC-DUPLICATE-001",
        "name": "Duplicate machine",
        "status": "offline",
    }

    first_response = client.post(
        "/api/v1/machines",
        json=payload,
    )
    second_response = client.post(
        "/api/v1/machines",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": (
            "Machine with code=MC-DUPLICATE-001 already exists"
        ),
    }
