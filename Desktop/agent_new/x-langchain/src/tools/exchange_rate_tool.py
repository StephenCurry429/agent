from typing import Any, Dict

import requests
from langchain.tools import tool


API_URL = "https://api.exchangerate.host/convert"


def _fetch_exchange_rate(from_currency: str, to_currency: str) -> str:
    """
    查询两种货币之间的当前汇率。

    Args:
        from_currency: 源货币代码，例如 USD
        to_currency: 目标货币代码，例如 CNY

    Returns:
        汇率信息字符串
    """
    try:
        if not from_currency or not to_currency:
            return "错误：货币代码不能为空，请提供 from_currency 和 to_currency，例如 USD、CNY。"

        if not isinstance(from_currency, str) or not isinstance(to_currency, str):
            return "错误：货币代码必须是字符串类型，例如 'USD'、'CNY'。"

        params: Dict[str, str] = {
            "from": from_currency.upper(),
            "to": to_currency.upper(),
        }

        response: requests.Response = requests.get(API_URL, params=params, timeout=10)
        response.raise_for_status()
        data: Dict[str, Any] = response.json()

        if not data.get("success", True):
            return f"错误：汇率接口返回失败，信息：{data}"

        result = data.get("result")
        date = data.get("date")
        if result is None:
            return "错误：未从汇率接口获取到有效结果。"

        return (
            f"{params['from']} -> {params['to']} 当前汇率：{result} "
            f"(数据日期：{date or '未知'})"
        )
    except requests.RequestException as exc:
        return f"获取汇率信息失败（网络错误）：{exc}"
    except Exception as exc:  # noqa: BLE001
        return f"获取汇率信息失败：{exc}"


@tool
def exchange_rate_tool(from_currency: str, to_currency: str) -> str:
    """
    查询两种货币之间的当前汇率。

    Args:
        from_currency: 源货币代码，例如 USD
        to_currency: 目标货币代码，例如 CNY

    Returns:
        汇率信息字符串
    """
    return _fetch_exchange_rate(from_currency, to_currency)

