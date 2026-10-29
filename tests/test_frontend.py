"""Interface exercised with a mocked HTTP boundary; never calls an external API."""

from pathlib import Path
from unittest.mock import Mock

import httpx
from streamlit.testing.v1 import AppTest


def test_frontend_dashboard_explorer_and_chat(monkeypatch):
    diagnosis = {
        "summary": "Pedido 1052",
        "problem": "Timeout",
        "diagnosis": "Restaurante não confirmou.",
        "evidence": ["RESTAURANT_TIMEOUT"],
        "recommendation": "Verificar confirmação.",
        "mode": "demo",
        "elapsed_ms": 1,
        "tools_used": ["get_order_diagnosis"],
    }

    def get(url):
        if url.endswith("/health"):
            data = {"mode": "demo"}
        elif url.endswith("/metrics"):
            data = {"total": 100, "delivered": 10, "cancelled": 40, "declined_payments": 10}
        elif url.endswith("/orders/1052"):
            data = {"id": 1052, "status": "cancelled"}
        else:
            data = []
        return httpx.Response(200, json=data)

    client = Mock()
    client.__enter__ = Mock(return_value=client)
    client.__exit__ = Mock(return_value=False)
    client.get.side_effect = get
    client.post.return_value = httpx.Response(200, json=diagnosis)
    monkeypatch.setattr(httpx, "Client", Mock(return_value=client))
    script = Path(__file__).resolve().parents[1] / "frontend" / "streamlit_app.py"
    page = AppTest.from_file(script).run(timeout=30)
    assert not page.exception
    assert page.metric[0].value == "100"
    page.button[0].click().run()
    assert not page.exception
    assert any("1052" in item.value for item in page.json)
    page.chat_input[0].set_value("Por que o pedido 1052 foi cancelado?").run()
    assert not page.exception
    assert len(page.chat_message) == 2
    assert any("Restaurante não confirmou" in item.value for item in page.markdown)
