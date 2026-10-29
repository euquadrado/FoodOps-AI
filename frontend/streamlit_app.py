import os

import httpx
import streamlit as st

API = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
st.set_page_config(page_title="FoodOps AI", page_icon="🍲", layout="wide")
st.markdown(
    """<style>
[data-testid="stMetric"] {background:#172335;padding:20px;border-radius:12px;}
.block-container {padding-top:2rem;}
</style>""",
    unsafe_allow_html=True,
)


def request(path, payload=None):
    try:
        with httpx.Client(timeout=240) as client:
            response = client.post(API + path, json=payload) if payload else client.get(API + path)
        if response.is_error:
            st.error(response.json().get("detail", "Falha na API."))
            return None
        return response.json()
    except (httpx.HTTPError, ValueError):
        st.error("API indisponível. Confira se os serviços estão em execução.")
        return None


def show_diagnosis(data):
    st.write(data["summary"])
    st.markdown("**Problema identificado**")
    st.write(data["problem"])
    st.markdown("**Diagnóstico baseado nos registros**")
    st.write(data["diagnosis"])
    with st.expander("Evidências consultadas", expanded=True):
        for evidence in data["evidence"]:
            st.text(evidence)
    st.markdown("**Ação recomendada**")
    st.write(data["recommendation"])
    if data.get("hypotheses"):
        st.write({"Hipóteses, não fatos": data["hypotheses"]})
    if data.get("ai_explanation"):
        with st.expander("Análise complementar gerada por IA — pode conter erros"):
            st.write(data["ai_explanation"])
    st.caption(
        f"{data['mode'].upper()} · {data['elapsed_ms']:.0f} ms · " + ", ".join(data["tools_used"])
    )


st.title("🍲 FoodOps AI")
st.caption("Observabilidade e investigação de pedidos · ambiente inteiramente fictício")
health = request("/health")
if health:
    mode = health["mode"].upper()
    st.sidebar.success(f"● API conectada · {mode} MODE")
    st.sidebar.caption("DEMO usa regras locais. AI usa a OpenAI API com ferramentas de leitura.")
st.sidebar.markdown("### Roteiro de demonstração")
st.sidebar.write(
    "1052 · Timeout do restaurante\n\n1053 · Pagamento recusado\n\n"
    "1056 · Atraso\n\n1060 · Divergência de valor\n\n1061 · Causa desconhecida"
)
dashboard, explorer, assistant = st.tabs(["Dashboard", "Explorar pedidos", "Assistente"])
with dashboard:
    st.subheader("Visão da operação")
    metrics = request("/metrics")
    if metrics:
        labels = [
            ("Total de pedidos", "total"),
            ("Entregues", "delivered"),
            ("Cancelados", "cancelled"),
            ("Pagamentos recusados", "declined_payments"),
        ]
        for col, (label, key) in zip(st.columns(4), labels):
            col.metric(label, metrics[key])
    page = st.number_input("Página", min_value=1, value=1)
    rows = request(f"/orders?offset={(page - 1) * 20}&limit=20")
    if rows is not None:
        st.dataframe(rows, use_container_width=True, hide_index=True)
with explorer:
    st.subheader("Linha do tempo do pedido")
    with st.form("explorer"):
        order_id = st.number_input(
            "Número do pedido", min_value=1, max_value=2147483647, value=1052
        )
        submit = st.form_submit_button("Consultar pedido", type="primary")
    if submit:
        data = request(f"/orders/{order_id}")
        if data:
            st.json(data)
            st.markdown("**Pagamentos**")
            st.dataframe(request(f"/orders/{order_id}/payments") or [], hide_index=True)
            st.markdown("**Histórico de eventos**")
            st.dataframe(request(f"/orders/{order_id}/events") or [], hide_index=True)
with assistant:
    st.subheader("Investigue com evidências")
    st.caption("Informe um pedido por pergunta. Ex.: Por que o pedido 1052 foi cancelado?")
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if st.button("Limpar conversa"):
        st.session_state.messages = []
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.write(message["data"])
            else:
                show_diagnosis(message["data"])
    question = st.chat_input("Pergunte sobre um pedido…", max_chars=2000)
    if question:
        with st.chat_message("user"):
            st.write(question)
        with st.spinner("Consultando registros…"):
            result = request("/agent/diagnose", {"message": question})
        if result:
            st.session_state.messages.extend(
                [{"role": "user", "data": question}, {"role": "assistant", "data": result}]
            )
            with st.chat_message("assistant"):
                show_diagnosis(result)
