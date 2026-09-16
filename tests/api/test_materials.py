from decimal import Decimal

from services.database.models.material import Material


def create_materials(
    db_session,
):

    low_stock = Material(
        code="MAT-TEST-001",
        name="低库存测试物料",
        unit="kg",
        stock_qty=Decimal("100.00"),
        safe_stock=Decimal("200.00"),
    )

    normal_stock = Material(
        code="MAT-TEST-002",
        name="正常库存测试物料",
        unit="kg",
        stock_qty=Decimal("500.00"),
        safe_stock=Decimal("200.00"),
    )

    db_session.add_all(
        [
            low_stock,
            normal_stock,
        ]
    )

    db_session.commit()

    return (
        low_stock,
        normal_stock,
    )


# ============================================================
# Low Stock
# ============================================================

def test_low_stock(
    client,
    db_session,
):

    low_stock, normal_stock = (
        create_materials(
            db_session
        )
    )

    response = client.get(
        "/api/v1/materials/low-stock"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    codes = [
        item["code"]
        for item in data
    ]

    # 库存低于安全库存
    # 应该被查询出来
    assert low_stock.code in codes

    # 正常库存
    # 不应该出现
    assert normal_stock.code not in codes