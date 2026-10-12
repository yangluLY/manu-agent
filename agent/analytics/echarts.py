from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from agent.analytics.schemas import ChartSpec


def chart_spec_to_echarts(
    chart: ChartSpec,
) -> dict[str, Any] | None:
    """把 V3.7 ``ChartSpec`` 转换成前端可直接使用的 ECharts option。

    ``table`` 是图表不适用时的明确降级类型，因此返回 ``None``，调用方应
    使用 ``chart.data`` 渲染表格，而不是伪造一个空 ECharts 实例。
    """

    if chart.type == "table":
        return None

    source = [
        {
            key: _json_value(value)
            for key, value in row.items()
        }
        for row in chart.data
    ]

    base: dict[str, Any] = {
        "title": {
            "text": chart.title,
            "left": "center",
        },
        "dataset": {
            "source": source,
        },
        "tooltip": {},
    }

    if chart.type in {"bar", "line"}:
        if not chart.x_field or not chart.y_fields:
            raise ValueError(
                f"{chart.type} chart requires x_field and y_fields"
            )

        base.update(
            {
                "tooltip": {"trigger": "axis"},
                "legend": {"top": 32},
                "grid": {
                    "left": 56,
                    "right": 24,
                    "top": 72,
                    "bottom": 52,
                    "containLabel": True,
                },
                "xAxis": {
                    "type": "category",
                    "name": chart.x_field,
                },
                "yAxis": {"type": "value"},
                "series": [
                    {
                        "name": series.name,
                        "type": chart.type,
                        "encode": {
                            "x": chart.x_field,
                            "y": series.field,
                        },
                        **(
                            {"smooth": True}
                            if chart.type == "line"
                            else {}
                        ),
                    }
                    for series in chart.series
                ],
            }
        )
        return base

    if chart.type == "pie":
        if not chart.category_field or not chart.value_field:
            raise ValueError(
                "pie chart requires category_field and value_field"
            )

        base.update(
            {
                "tooltip": {"trigger": "item"},
                "legend": {
                    "type": "scroll",
                    "orient": "vertical",
                    "right": 16,
                    "top": 64,
                    "bottom": 16,
                },
                "series": [
                    {
                        "name": chart.title,
                        "type": "pie",
                        "radius": ["35%", "68%"],
                        "center": ["42%", "56%"],
                        "encode": {
                            "itemName": chart.category_field,
                            "value": chart.value_field,
                            "tooltip": [
                                chart.category_field,
                                chart.value_field,
                            ],
                        },
                    }
                ],
            }
        )
        return base

    raise ValueError(
        f"Unsupported chart type: {chart.type}"
    )


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    if isinstance(value, Enum):
        return _json_value(value.value)

    return str(value)
