import streamlit as st
import streamlit.components.v1 as components
import requests
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="RaioxSeller",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS GLOBAL
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background-color: #0a0a12 !important;
    color: #e2e2f0 !important;
}

/* REMOVE PADDING PADRÃO */
.block-container { padding: 0 !important; max-width: 100% !important; }
section[data-testid="stSidebar"] { background: #0f0f1a !important; border-right: 1px solid #1e1e2e !important; }
section[data-testid="stSidebar"] * { color: #e2e2f0 !important; }

/* SIDEBAR */
.sidebar-logo { padding: 20px 16px 12px; border-bottom: 1px solid #1e1e2e; margin-bottom: 8px; }
.sidebar-logo h2 { font-size: 16px; font-weight: 700; margin: 0; color: #e2e2f0; }
.sidebar-logo p { font-size: 11px; color: #6b6b8a; margin: 2px 0 0; }

/* CARDS */
.card {
    background: #13131f;
    border: 1px solid #1e1e2e;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 12px;
}
.card-sm {
    background: #13131f;
    border: 1px solid #1e1e2e;
    border-radius: 10px;
    padding: 14px;
}

/* SCORE GRANDE */
.score-box {
    text-align: center;
    border-radius: 12px;
    padding: 16px 24px;
    border: 2px solid;
}
.score-num { font-size: 48px; font-weight: 900; line-height: 1; }
.score-lbl { font-size: 11px; margin-top: 2px; }

/* MÉTRICAS */
.metric-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid #1e1e2e;
    font-size: 13px;
}
.metric-row:last-child { border-bottom: none; }
.metric-label { color: #6b6b8a; }
.metric-val { font-weight: 600; }

/* ALERTAS */
.alerta-critico {
    background: #2d1b1b;
    border-left: 4px solid #e52b2b;
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 10px;
}
.alerta-atencao {
    background: #2d2418;
    border-left: 4px solid #f5a623;
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 10px;
}
.alerta-info {
    background: #0d1f35;
    border-left: 4px solid #3b82f6;
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 10px;
}
.alerta-titulo { font-size: 13px; font-weight: 600; color: #e2e2f0; margin-bottom: 4px; }
.alerta-acao { font-size: 12px; color: #a0a0c0; margin-bottom: 4px; }
.alerta-ref { font-size: 11px; color: #6b6b8a; }

/* TAGS */
.tag {
    display: inline-block;
    font-size: 10px;
    font-weight: 500;
    padding: 3px 8px;
    border-radius: 4px;
    margin-right: 4px;
}
.tag-red { background: #501313; color: #f09575; }
.tag-yellow { background: #412402; color: #FAC775; }
.tag-green { background: #173404; color: #9FE1CB; }
.tag-blue { background: #042C53; color: #B5D4F4; }

/* BOTÕES */
div.stButton > button {
    background: #00a650 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 8px 20px !important;
}
div.stButton > button:hover { background: #008a42 !important; }

/* INPUT */
div.stTextInput > div > div > input {
    background: #1a1a2e !important;
    border: 1px solid #1e1e2e !important;
    border-radius: 8px !important;
    color: #e2e2f0 !important;
    font-size: 13px !important;
}

/* TABS */
div.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #1e1e2e !important;
    gap: 0 !important;
}
div.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #6b6b8a !important;
    font-size: 12px !important;
    padding: 8px 16px !important;
    border-radius: 0 !important;
}
div.stTabs [aria-selected="true"] {
    color: #00a650 !important;
    border-bottom: 2px solid #00a650 !important;
    font-weight: 600 !important;
}

/* SELECTBOX E OUTROS */
div.stSelectbox > div > div {
    background: #1a1a2e !important;
    border: 1px solid #1e1e2e !important;
    border-radius: 8px !important;
    color: #e2e2f0 !important;
}
div.stNumberInput > div > div > input {
    background: #1a1a2e !important;
    border: 1px solid #1e1e2e !important;
    border-radius: 8px !important;
    color: #e2e2f0 !important;
}

/* DATAFRAME */
div.stDataFrame { border: 1px solid #1e1e2e !important; border-radius: 10px !important; }
div.stDataFrame * { background: #13131f !important; color: #e2e2f0 !important; }

/* EXPANDER */
div.stExpander { background: #13131f !important; border: 1px solid #1e1e2e !important; border-radius: 10px !important; }

/* METRIC */
div.stMetric { background: #13131f; border: 1px solid #1e1e2e; border-radius: 10px; padding: 12px 16px; }
div.stMetric label { color: #6b6b8a !important; font-size: 11px !important; }
div.stMetric [data-testid="stMetricValue"] { color: #e2e2f0 !important; font-size: 22px !important; font-weight: 700 !important; }

/* ESCONDE ELEMENTOS PADRÃO */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

CLIENT_ID = "8361153242610469"
CLIENT_SECRET = st.secrets["CLIENT_SECRET"]
REDIRECT_URI = "https://httpbin.org/get"

def get_access_token(code):
    r = requests.post("https://api.mercadolibre.com/oauth/token", data={
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI
    })
    return r.json()

def diagnostico_conta(access_token, user_id):
    H = {"Authorization": f"Bearer {access_token}"}
    resultado = {
        "seller": "", "nivel": "", "mercadolider": "",
        "score_total": 100,
        "scores": {"reputacao": 100, "operacao": 100, "estoque": 100, "publicidade": 100, "atendimento": 100},
        "status": "", "alertas": [], "skus": [], "metricas": {},
        "gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M")
    }

    r = requests.get(f"https://api.mercadolibre.com/users/{user_id}", headers=H)
    dados = r.json()
    resultado["seller"] = dados.get("nickname", "")
    rep = dados.get("seller_reputation", {})
    metricas = rep.get("metrics", {})
    transacoes = rep.get("transactions", {})
    nivel = rep.get("level_id", "")
    resultado["nivel"] = nivel
    resultado["mercadolider"] = rep.get("power_seller_status") or "Não é MercadoLíder"

    nivel_scores = {"5_green": 100, "4_light_green": 75, "3_yellow": 55, "2_orange": 30, "1_red": 10}
    resultado["scores"]["reputacao"] = nivel_scores.get(nivel, 50)

    if nivel in ["1_red", "2_orange"]:
        resultado["alertas"].append({"tipo": "CRITICO", "categoria": "Reputação", "impacto": "ALTO",
            "mensagem": f"Reputação {nivel.split('_')[1].upper()}. Visibilidade e Buy Box comprometidos.",
            "acao": "Resolver reclamações abertas e reduzir cancelamentos imediatamente.",
            "referencia": "Meta: ≤2% reclamações, ≤1% cancelamentos, ≥90% envios no prazo"})
    elif nivel == "3_yellow":
        resultado["alertas"].append({"tipo": "ATENCAO", "categoria": "Reputação", "impacto": "MÉDIO",
            "mensagem": "Reputação AMARELA. Perda de posicionamento e Buy Box.",
            "acao": "Foco em reduzir atrasos e cancelamentos abaixo de 1%.",
            "referencia": "Meta Brasil: ≤2% reclamações, ≤1% cancelamentos, ≥90% no prazo"})

    ratings = transacoes.get("ratings", {})
    positivas = ratings.get("positive", 0)
    negativas = ratings.get("negative", 0)
    taxa_atraso = metricas.get("delayed_handling_time", {}).get("rate", 0)
    taxa_cancelamento = metricas.get("cancellations", {}).get("rate", 0)
    taxa_reclamacao = metricas.get("claims", {}).get("rate", 0)
    vendas_60d = metricas.get("sales", {}).get("completed", 0)

    score_op = 100
    if taxa_atraso > 0.10:
        score_op -= 40
        resultado["alertas"].append({"tipo": "CRITICO", "categoria": "Operação", "impacto": "ALTO",
            "mensagem": f"Atraso no envio: {round(taxa_atraso*100,1)}%. Meta: ≥90% no prazo.",
            "acao": "Aumente prazo de handling para 2 dias. Considere Full nos top SKUs.",
            "referencia": "Meta ML Brasil: ≥90% de envios dentro do prazo"})
    elif taxa_atraso > 0.05:
        score_op -= 20
        resultado["alertas"].append({"tipo": "ATENCAO", "categoria": "Operação", "impacto": "MÉDIO",
            "mensagem": f"Atraso no envio: {round(taxa_atraso*100,1)}%. Próximo do limite crítico.",
            "acao": "Ajuste prazo de handling nos anúncios.",
            "referencia": "Meta ML Brasil: ≥90% de envios dentro do prazo"})

    if taxa_cancelamento > 0.01:
        score_op -= 35
        resultado["alertas"].append({"tipo": "CRITICO", "categoria": "Operação", "impacto": "ALTO",
            "mensagem": f"Cancelamentos: {round(taxa_cancelamento*100,1)}%. Acima do limite de 1%.",
            "acao": "Investigue causa: estoque desatualizado, preço errado ou problema logístico.",
            "referencia": "Meta ML Brasil: ≤1% de cancelamentos pelo vendedor"})

    if taxa_reclamacao > 0.02:
        score_op -= 40
        resultado["alertas"].append({"tipo": "CRITICO", "categoria": "Operação", "impacto": "ALTO",
            "mensagem": f"Reclamações: {round(taxa_reclamacao*100,1)}%. Acima do limite de 2%.",
            "acao": "Responda todas as reclamações em até 48h.",
            "referencia": "Meta ML Brasil: ≤2% de reclamações nos últimos 60 dias"})

    resultado["scores"]["operacao"] = max(0, score_op)
    resultado["metricas"]["operacao"] = {
        "atraso": f"{round(taxa_atraso*100,1)}%",
        "cancelamento": f"{round(taxa_cancelamento*100,1)}%",
        "reclamacao": f"{round(taxa_reclamacao*100,1)}%",
        "vendas_60d": vendas_60d
    }
    resultado["metricas"]["reputacao"] = {
        "nivel": nivel, "positivas": f"{round(positivas*100,1)}%",
        "negativas": f"{round(negativas*100,1)}%",
        "total_vendas": transacoes.get("total", 0),
        "canceladas": transacoes.get("canceled", 0)
    }

    r_perguntas = requests.get(
        f"https://api.mercadolibre.com/questions/search?seller_id={user_id}&status=UNANSWERED", headers=H)
    perguntas = 0
    if r_perguntas.status_code == 200:
        perguntas = r_perguntas.json().get("total", 0)
    score_atend = 100
    if perguntas > 10:
        score_atend -= 40
        resultado["alertas"].append({"tipo": "CRITICO", "categoria": "Atendimento", "impacto": "ALTO",
            "mensagem": f"{perguntas} perguntas sem resposta.",
            "acao": "Responda todas as perguntas. Ideal: menos de 1 hora.",
            "referencia": "Tempo de resposta impacta conversão e posicionamento"})
    elif perguntas > 3:
        score_atend -= 20
        resultado["alertas"].append({"tipo": "ATENCAO", "categoria": "Atendimento", "impacto": "MÉDIO",
            "mensagem": f"{perguntas} perguntas sem resposta.",
            "acao": "Crie rotina de resposta diária. Ideal: menos de 1 hora.",
            "referencia": "ML considera bom tempo de resposta: até 1 hora"})
    resultado["scores"]["atendimento"] = max(0, score_atend)
    resultado["metricas"]["atendimento"] = {"perguntas_sem_resposta": perguntas}

    r_itens = requests.get(
        f"https://api.mercadolibre.com/users/{user_id}/items/search", headers=H)
    item_ids = r_itens.json().get("results", [])
    score_estoque = 100
    total_itens = len(item_ids)
    itens_ativos = 0
    itens_ruptura = 0
    itens_baixo = 0

    for item_id in item_ids:
        r_item = requests.get(f"https://api.mercadolibre.com/items/{item_id}", headers=H)
        item = r_item.json()
        titulo = item.get("title", "")
        titulo_curto = titulo[:45] + "..." if len(titulo) > 45 else titulo
        estoque = item.get("available_quantity", 0)
        status = item.get("status", "")
        vendas = item.get("sold_quantity", 0)
        preco = item.get("price", 0)
        logistica = item.get("shipping", {}).get("logistic_type", "")
        problemas = []

        if status == "active":
            itens_ativos += 1
        if estoque == 0 and status == "active":
            itens_ruptura += 1
            score_estoque -= 25
            problemas.append("🔴 Ruptura com anúncio ativo")
            resultado["alertas"].append({"tipo": "CRITICO", "categoria": "Estoque", "impacto": "ALTO",
                "mensagem": f"'{titulo_curto}' ATIVO com estoque ZERO.",
                "acao": "Pause o anúncio imediatamente ou reponha estoque urgente.",
                "referencia": "Anúncio ativo sem estoque queima budget de ads"})
        elif estoque == 0 and status == "closed" and vendas > 0:
            score_estoque -= 10
            problemas.append(f"🟡 Fechado — {vendas} vendas anteriores")
            resultado["alertas"].append({"tipo": "ATENCAO", "categoria": "Estoque", "impacto": "MÉDIO",
                "mensagem": f"'{titulo_curto}' fechado com {vendas} vendas anteriores.",
                "acao": f"Repor estoque e reativar. Potencial: R${preco} por venda.",
                "referencia": "Produto com histórico tem mais chance de conversão"})
        elif 0 < estoque <= 5 and status == "active":
            itens_baixo += 1
            problemas.append(f"🟡 Estoque crítico: {estoque} un.")
            resultado["alertas"].append({"tipo": "ATENCAO", "categoria": "Estoque", "impacto": "MÉDIO",
                "mensagem": f"'{titulo_curto}' com apenas {estoque} unidades.",
                "acao": "Repor estoque antes de atingir zero.",
                "referencia": "Ruptura frequente pode levar à desativação automática"})

        if logistica not in ["fulfillment", "xd_drop_off"] and status == "active":
            problemas.append("⚠️ Sem Full/Flex")

        resultado["skus"].append({
            "Produto": titulo_curto, "Preço": f"R${preco}",
            "Estoque": estoque, "Vendas": vendas,
            "Status": "✅ Ativo" if status == "active" else "⛔ Fechado",
            "Logística": logistica or "Padrão",
            "Situação": " | ".join(problemas) if problemas else "✅ OK"
        })

    resultado["scores"]["estoque"] = max(0, score_estoque)
    resultado["metricas"]["estoque"] = {
        "total_itens": total_itens, "itens_ativos": itens_ativos,
        "itens_ruptura": itens_ruptura, "itens_estoque_baixo": itens_baixo
    }

    r_adv = requests.get(
        "https://api.mercadolibre.com/advertising/advertisers?product_id=PADS",
        headers={**H, "Api-Version": "1"})
    score_ads = 100
    if r_adv.status_code == 200:
        advertisers = r_adv.json().get("advertisers", [])
        if advertisers:
            adv_id = advertisers[0].get("advertiser_id")
            hoje = datetime.now()
            r_camp = requests.get(
                f"https://api.mercadolibre.com/advertising/advertisers/{adv_id}/product_ads/campaigns/search"
                f"?date_from={hoje.year}-01-01&date_to={hoje.strftime('%Y-%m-%d')}&metrics=clicks,cost,roas",
                headers={**H, "Api-Version": "2"})
            if r_camp.status_code == 200:
                for c in r_camp.json().get("campaigns", []):
                    roas = c.get("metrics", {}).get("roas", 0) or 0
                    nome = c.get("name", "Campanha")
                    if roas and roas < 3:
                        score_ads -= 20
                        resultado["alertas"].append({"tipo": "CRITICO", "categoria": "Publicidade", "impacto": "ALTO",
                            "mensagem": f"Campanha '{nome}': ROAS {round(roas,1)}x — abaixo do mínimo.",
                            "acao": "Pause itens sem conversão. ROAS mínimo = 100 / margem%.",
                            "referencia": "Desde out/2025 o ML usa ROAS como métrica principal"})
    else:
        score_ads = 50
        resultado["alertas"].append({"tipo": "INFO", "categoria": "Publicidade", "impacto": "BAIXO",
            "mensagem": "Conta sem Product Ads ativo.",
            "acao": "Ative Product Ads nos SKUs com histórico de vendas e estoque ok.",
            "referencia": "Sellers com ads têm prioridade no posicionamento orgânico"})
    resultado["scores"]["publicidade"] = max(0, score_ads)

    pesos = {"reputacao": 0.30, "operacao": 0.25, "estoque": 0.20, "atendimento": 0.15, "publicidade": 0.10}
    resultado["score_total"] = int(sum(resultado["scores"][k] * v for k, v in pesos.items()))
    resultado["status"] = "SAUDAVEL" if resultado["score_total"] >= 80 else "ATENCAO" if resultado["score_total"] >= 60 else "CRITICO"
    ordem = {"CRITICO": 0, "ATENCAO": 1, "INFO": 2}
    resultado["alertas"].sort(key=lambda x: ordem.get(x["tipo"], 3))
    return resultado

def analisar_item(item_id, access_token, user_id):
    H = {"Authorization": f"Bearer {access_token}"}
    r = requests.get(f"https://api.mercadolibre.com/items/{item_id}", headers=H)
    if r.status_code != 200:
        return None
    item = r.json()

    titulo = item.get("title", "")
    preco = item.get("price", 0)
    estoque = item.get("available_quantity", 0)
    status = item.get("status", "")
    vendas = item.get("sold_quantity", 0)
    fotos = item.get("pictures", [])
    atributos = item.get("attributes", [])
    logistica = item.get("shipping", {}).get("logistic_type", "")

    r_desc = requests.get(f"https://api.mercadolibre.com/items/{item_id}/description", headers=H)
    descricao = r_desc.json().get("plain_text", "") if r_desc.status_code == 200 else ""

    scores = {}
    acoes = {}
    chars = len(titulo)
    scores["titulo"] = 90 if chars >= 55 else 60 if chars >= 40 else 25
    acoes["titulo"] = f"Bom — {chars}/60 caracteres." if chars >= 55 else f"{chars}/60 — use todos os 60 com marca + modelo + especificação."

    n_fotos = len(fotos)
    scores["fotos"] = 90 if n_fotos >= 6 else 60 if n_fotos >= 4 else 30 if n_fotos >= 2 else 5
    acoes["fotos"] = f"{n_fotos} fotos — bom." if n_fotos >= 6 else f"Apenas {n_fotos} fotos — ML recomenda mínimo 6 com 1200x1200px."

    n_attrs = len(atributos)
    scores["ficha"] = 90 if n_attrs >= 10 else 55 if n_attrs >= 6 else 25 if n_attrs >= 3 else 5
    acoes["ficha"] = f"{n_attrs} atributos — bom." if n_attrs >= 10 else f"Apenas {n_attrs} atributos — preencha toda a ficha técnica."

    chars_desc = len(descricao)
    scores["descricao"] = 85 if chars_desc >= 500 else 55 if chars_desc >= 200 else 25 if chars_desc > 0 else 0
    acoes["descricao"] = "Descrição completa." if chars_desc >= 500 else "Adicione: o que vem na caixa, compatibilidade e garantia."

    scores["preco"] = 75 if preco > 0 else 0
    acoes["preco"] = f"R${preco} — monitore paridade com Amazon e Shopee."

    r_rep = requests.get(f"https://api.mercadolibre.com/users/{user_id}", headers=H)
    nivel = r_rep.json().get("seller_reputation", {}).get("level_id", "") if r_rep.status_code == 200 else ""
    nivel_scores = {"5_green": 100, "4_light_green": 80, "3_yellow": 55, "2_orange": 30, "1_red": 10}
    scores["reputacao"] = nivel_scores.get(nivel, 50)
    nivel_labels = {"5_green": "Verde", "4_light_green": "Verde claro", "3_yellow": "Amarela", "2_orange": "Laranja", "1_red": "Vermelha"}
    acoes["reputacao"] = f"Reputação {nivel_labels.get(nivel, 'não identificada')} — impacta posicionamento."

    scores["logistica"] = 100 if logistica == "fulfillment" else 75 if logistica == "xd_drop_off" else 0
    acoes["logistica"] = "Full ativo — 3x mais chances de venda." if logistica == "fulfillment" else "Flex ativo." if logistica == "xd_drop_off" else "Envio padrão — ative Full para triplicar chances de venda."

    scores["conversao"] = 90 if vendas >= 20 else 60 if vendas >= 5 else 30 if vendas >= 1 else 0
    acoes["conversao"] = f"{vendas} vendas — histórico forte." if vendas >= 20 else f"{vendas} vendas." if vendas >= 1 else "Sem vendas — aguarde histórico antes de ads."

    pesos = {"titulo": 0.15, "fotos": 0.20, "ficha": 0.20, "descricao": 0.10,
             "preco": 0.10, "reputacao": 0.10, "logistica": 0.10, "conversao": 0.05}
    score_total = int(sum(scores[k] * pesos[k] for k in pesos))
    pode_anunciar = estoque > 0 and status == "active" and vendas >= 1

    return {
        "item_id": item_id, "titulo": titulo, "preco": preco,
        "estoque": estoque, "status": status, "vendas": vendas,
        "fotos": n_fotos, "logistica": logistica,
        "score_total": score_total, "scores": scores, "acoes": acoes,
        "pode_anunciar": pode_anunciar, "n_atributos": n_attrs
    }

def gauge(score, titulo):
    cor = "#00a650" if score >= 80 else "#f5a623" if score >= 60 else "#e52b2b"
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score,
        title={"text": titulo, "font": {"size": 12, "color": "#6b6b8a"}},
        number={"font": {"size": 28, "color": cor}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#1e1e2e"},
            "bar": {"color": cor, "thickness": 0.25},
            "bgcolor": "#13131f",
            "steps": [
                {"range": [0, 60], "color": "#2d1b1b"},
                {"range": [60, 80], "color": "#2d2418"},
                {"range": [80, 100], "color": "#0d2d1a"}
            ]
        }
    ))
    fig.update_layout(
        height=170, margin=dict(t=40, b=0, l=10, r=10),
        paper_bgcolor="#13131f", plot_bgcolor="#13131f",
        font={"color": "#e2e2f0"}
    )
    return fig

def cor_score(s):
    return "#e52b2b" if s < 60 else "#f5a623" if s < 80 else "#00a650"

def calcular_preco_ideal(cmv, comissao_pct, frete, imposto_pct, margem_pct):
    total_var = comissao_pct + imposto_pct + (margem_pct / 100)
    preco = (cmv + frete) / (1 - total_var)
    comissao = preco * comissao_pct
    imposto = preco * imposto_pct
    lucro = preco - cmv - comissao - frete - imposto
    return preco, comissao, imposto, lucro

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <h2>🔍 RaioxSeller</h2>
        <p>Diagnóstico de performance ML</p>
    </div>
    """, unsafe_allow_html=True)

    pagina = st.radio("", [
        "🏠 Visão geral",
        "📦 Analisar produto",
        "🧮 Calculadora",
        "📋 Plano de ação"
    ], label_visibility="collapsed")

    st.markdown("---")

    auth_url = f"https://auth.mercadolivre.com.br/authorization?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
    with st.expander("🔗 Conectar conta ML", expanded="access_token" not in st.session_state):
        st.markdown(f"**Passo 1:** [Autorizar conta]({auth_url})")
        st.caption("Copie o código TG-XXXXXXX da URL")
        code_input = st.text_input("**Passo 2:** Cole o código:", placeholder="TG-...", key="code_input")
        if st.button("Conectar", use_container_width=True):
            with st.spinner("Conectando..."):
                td = get_access_token(code_input)
                if td.get("access_token"):
                    st.session_state["access_token"] = td["access_token"]
                    st.session_state["user_id"] = str(td["user_id"])
                    st.success("✅ Conta conectada!")
                    st.rerun()
                else:
                    st.error("Código inválido.")

    if "access_token" in st.session_state:
        st.markdown("""
        <div style="background:#0d2d1a;border:1px solid #00a650;border-radius:8px;padding:10px 12px;font-size:12px;color:#9FE1CB;">
            ✅ Conta conectada
        </div>
        """, unsafe_allow_html=True)

if "access_token" not in st.session_state:
    st.markdown("""
    <div style="display:flex;align-items:center;justify-content:center;height:80vh;flex-direction:column;gap:16px;">
        <div style="font-size:48px;">🔍</div>
        <div style="font-size:20px;font-weight:700;color:#e2e2f0;">RaioxSeller</div>
        <div style="font-size:14px;color:#6b6b8a;">Conecte sua conta do Mercado Livre na barra lateral para começar.</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

ACCESS = st.session_state["access_token"]
UID = st.session_state["user_id"]

# ============================================================
# VISÃO GERAL
# ============================================================
if pagina == "🏠 Visão geral":
    col_title, col_refresh = st.columns([9, 1])
    with col_title:
        st.markdown('<div style="padding:24px 24px 0;">', unsafe_allow_html=True)
    with col_refresh:
        st.markdown('<div style="padding:20px 0 0;">', unsafe_allow_html=True)
        if st.button("🔄"):
            if "diagnostico" in st.session_state:
                del st.session_state["diagnostico"]
            st.rerun()

    if "diagnostico" not in st.session_state:
        with st.spinner("Analisando sua conta..."):
            st.session_state["diagnostico"] = diagnostico_conta(ACCESS, UID)

    r = st.session_state["diagnostico"]
    cor = "#00a650" if r["status"] == "SAUDAVEL" else "#f5a623" if r["status"] == "ATENCAO" else "#e52b2b"
    nivel_labels = {
        "5_green": "🟢 Verde", "4_light_green": "🟢 Verde claro",
        "3_yellow": "🟡 Amarelo", "2_orange": "🟠 Laranja", "1_red": "🔴 Vermelho"
    }
    criticos = len([a for a in r["alertas"] if a["tipo"] == "CRITICO"])
    atencoes = len([a for a in r["alertas"] if a["tipo"] == "ATENCAO"])

    st.markdown(f"""
    <div style="padding:24px 24px 0;">
        <div style="display:grid;grid-template-columns:1fr auto auto;gap:16px;background:#13131f;border:1px solid #1e1e2e;border-radius:12px;padding:20px;margin-bottom:16px;">
            <div>
                <div style="font-size:22px;font-weight:700;color:#e2e2f0;margin-bottom:4px;">Olá, {r['seller']} 👋</div>
                <div style="font-size:12px;color:#6b6b8a;margin-bottom:8px;">Diagnóstico gerado em {r['gerado_em']}</div>
                <div style="font-size:12px;color:#6b6b8a;">
                    Reputação: <span style="color:#e2e2f0;">{nivel_labels.get(r['nivel'], r['nivel'])}</span>
                    &nbsp;|&nbsp;
                    MercadoLíder: <span style="color:#e2e2f0;">{r['mercadolider'].title()}</span>
                </div>
            </div>
            <div style="text-align:center;background:{cor}15;border:2px solid {cor};border-radius:12px;padding:14px 24px;">
                <div style="font-size:48px;font-weight:900;color:{cor};line-height:1;">{r['score_total']}</div>
                <div style="font-size:11px;color:{cor};">Score /100</div>
            </div>
            <div style="text-align:center;background:#13131f;border:1px solid #1e1e2e;border-radius:12px;padding:14px 20px;">
                <div style="font-size:32px;font-weight:700;color:#e52b2b;">{criticos}</div>
                <div style="font-size:11px;color:#6b6b8a;">Críticos</div>
                <div style="font-size:24px;font-weight:700;color:#f5a623;margin-top:6px;">{atencoes}</div>
                <div style="font-size:11px;color:#6b6b8a;">Atenções</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="padding:0 24px;">', unsafe_allow_html=True)

    # ALERTAS CRÍTICOS
    st.markdown('<div style="font-size:15px;font-weight:600;color:#e2e2f0;margin:16px 0 10px;">🎯 Problemas críticos</div>', unsafe_allow_html=True)
    criticos_lista = [a for a in r["alertas"] if a["tipo"] == "CRITICO"]
    if criticos_lista:
        for i, a in enumerate(criticos_lista, 1):
            st.markdown(f"""
            <div class="alerta-critico">
                <div class="alerta-titulo">{i}. [{a['categoria']}] {a['mensagem']}</div>
                <div class="alerta-acao">→ {a['acao']}</div>
                <div class="alerta-ref">📌 {a['referencia']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown('<div style="background:#0d2d1a;border:1px solid #00a650;border-radius:8px;padding:14px;color:#9FE1CB;font-size:13px;">✅ Nenhum problema crítico. Operação saudável!</div>', unsafe_allow_html=True)

    # GAUGES
    st.markdown('<div style="font-size:15px;font-weight:600;color:#e2e2f0;margin:20px 0 10px;">📊 Score por categoria</div>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.plotly_chart(gauge(r["scores"]["reputacao"], "Reputação"), use_container_width=True)
    c2.plotly_chart(gauge(r["scores"]["operacao"], "Operação"), use_container_width=True)
    c3.plotly_chart(gauge(r["scores"]["estoque"], "Estoque"), use_container_width=True)
    c4.plotly_chart(gauge(r["scores"]["atendimento"], "Atendimento"), use_container_width=True)
    c5.plotly_chart(gauge(r["scores"]["publicidade"], "Publicidade"), use_container_width=True)

    # MÉTRICAS DETALHADAS
    st.markdown('<div style="font-size:15px;font-weight:600;color:#e2e2f0;margin:20px 0 10px;">📈 Métricas detalhadas</div>', unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["Reputação & Operação", "Estoque & SKUs", "Atendimento", "Todos os alertas"])

    with tab1:
        ca, cb = st.columns(2)
        with ca:
            m = r["metricas"].get("reputacao", {})
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div style="font-size:13px;font-weight:600;color:#e2e2f0;margin-bottom:12px;">Reputação</div>', unsafe_allow_html=True)
            for label, val in [
                ("Avaliações positivas", m.get("positivas", "-")),
                ("Avaliações negativas", m.get("negativas", "-")),
                ("Total de vendas", str(m.get("total_vendas", "-"))),
                ("Vendas canceladas", str(m.get("canceladas", "-"))),
            ]:
                st.markdown(f'<div class="metric-row"><span class="metric-label">{label}</span><span class="metric-val">{val}</span></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with cb:
            m = r["metricas"].get("operacao", {})
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div style="font-size:13px;font-weight:600;color:#e2e2f0;margin-bottom:12px;">Operação (últimos 60 dias)</div>', unsafe_allow_html=True)
            for label, val, meta in [
                ("Atraso no envio", m.get("atraso", "-"), "Meta: ≥90% no prazo"),
                ("Cancelamentos", m.get("cancelamento", "-"), "Meta: ≤1%"),
                ("Reclamações", m.get("reclamacao", "-"), "Meta: ≤2%"),
                ("Vendas no período", str(m.get("vendas_60d", "-")), ""),
            ]:
                st.markdown(f'<div class="metric-row"><span class="metric-label">{label}<br><small style="color:#444;">{meta}</small></span><span class="metric-val">{val}</span></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        m = r["metricas"].get("estoque", {})
        e1, e2, e3, e4 = st.columns(4)
        e1.metric("Total de itens", m.get("total_itens", 0))
        e2.metric("Itens ativos", m.get("itens_ativos", 0))
        e3.metric("Em ruptura", m.get("itens_ruptura", 0))
        e4.metric("Estoque crítico", m.get("itens_estoque_baixo", 0))
        if r["skus"]:
            df = pd.DataFrame(r["skus"])
            st.dataframe(df, use_container_width=True, hide_index=True)

    with tab3:
        m = r["metricas"].get("atendimento", {})
        st.metric("Perguntas sem resposta", m.get("perguntas_sem_resposta", 0))
        st.caption("Ideal: responder em menos de 1 hora.")

    with tab4:
        for a in r["alertas"]:
            if a["tipo"] == "CRITICO":
                st.markdown(f'<div class="alerta-critico"><div class="alerta-titulo">🔴 [{a["categoria"]}] {a["mensagem"]}</div><div class="alerta-acao">→ {a["acao"]}</div><div class="alerta-ref">📌 {a["referencia"]}</div></div>', unsafe_allow_html=True)
            elif a["tipo"] == "ATENCAO":
                st.markdown(f'<div class="alerta-atencao"><div class="alerta-titulo">🟡 [{a["categoria"]}] {a["mensagem"]}</div><div class="alerta-acao">→ {a["acao"]}</div><div class="alerta-ref">📌 {a["referencia"]}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="alerta-info"><div class="alerta-titulo">ℹ️ [{a["categoria"]}] {a["mensagem"]}</div><div class="alerta-acao">→ {a["acao"]}</div><div class="alerta-ref">📌 {a["referencia"]}</div></div>', unsafe_allow_html=True)

# ============================================================
# ANALISAR PRODUTO
# ============================================================
elif pagina == "📦 Analisar produto":
    st.markdown('<div style="padding:24px;">', unsafe_allow_html=True)
    st.markdown('<div style="font-size:20px;font-weight:700;color:#e2e2f0;margin-bottom:4px;">Analisar produto</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:12px;color:#6b6b8a;margin-bottom:20px;">Cole o MLB para diagnóstico completo de qualidade, ads e precificação</div>', unsafe_allow_html=True)

    col_in, col_btn = st.columns([4, 1])
    with col_in:
        mlb = st.text_input("", placeholder="Ex: MLB4341336433", label_visibility="collapsed")
    with col_btn:
        buscar = st.button("🔍 Analisar", use_container_width=True)

    if buscar and mlb:
        with st.spinner(f"Analisando {mlb}..."):
            item = analisar_item(mlb.strip().upper(), ACCESS, UID)

        if not item:
            st.markdown('<div class="alerta-critico"><div class="alerta-titulo">Produto não encontrado. Verifique o MLB.</div></div>', unsafe_allow_html=True)
        else:
            cor_s = cor_score(item["score_total"])

            st.markdown(f"""
            <div class="card" style="margin-top:16px;">
                <div style="display:grid;grid-template-columns:1fr auto;gap:16px;align-items:start;">
                    <div>
                        <div style="font-size:11px;color:#6b6b8a;font-family:monospace;margin-bottom:4px;">{item['item_id']}</div>
                        <div style="font-size:15px;font-weight:600;color:#e2e2f0;margin-bottom:8px;">{item['titulo']}</div>
                        <div>
                            <span class="tag tag-blue">R${item['preco']}</span>
                            <span class="tag {'tag-red' if item['estoque'] == 0 else 'tag-green'}">Estoque: {item['estoque']}</span>
                            <span class="tag tag-blue">Vendas: {item['vendas']}</span>
                            <span class="tag {'tag-green' if item['logistica'] == 'fulfillment' else 'tag-yellow'}">{item['logistica'] or 'Padrão'}</span>
                        </div>
                    </div>
                    <div style="text-align:center;background:{cor_s}15;border:2px solid {cor_s};border-radius:10px;padding:12px 20px;">
                        <div style="font-size:36px;font-weight:900;color:{cor_s};">{item['score_total']}</div>
                        <div style="font-size:10px;color:{cor_s};">/100</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            tab_fat, tab_ads, tab_preco = st.tabs(["📊 8 fatores do algoritmo", "📢 Recomendação de Ads", "💰 Preço ideal"])

            with tab_fat:
                fatores = [
                    ("📝 Título", item["scores"]["titulo"], item["acoes"]["titulo"]),
                    ("📸 Fotos", item["scores"]["fotos"], item["acoes"]["fotos"]),
                    ("📋 Ficha técnica", item["scores"]["ficha"], item["acoes"]["ficha"]),
                    ("📄 Descrição", item["scores"]["descricao"], item["acoes"]["descricao"]),
                    ("💲 Preço total", item["scores"]["preco"], item["acoes"]["preco"]),
                    ("⭐ Reputação", item["scores"]["reputacao"], item["acoes"]["reputacao"]),
                    ("🚚 Logística", item["scores"]["logistica"], item["acoes"]["logistica"]),
                    ("📈 Conversão", item["scores"]["conversao"], item["acoes"]["conversao"]),
                ]
                st.markdown('<div class="card">', unsafe_allow_html=True)
                for nome, score, acao in fatores:
                    fc = cor_score(score)
                    st.markdown(f"""
                    <div style="display:grid;grid-template-columns:120px 1fr 40px 1fr;gap:12px;align-items:center;padding:10px 0;border-bottom:1px solid #1e1e2e;">
                        <div style="font-size:12px;color:#e2e2f0;font-weight:500;">{nome}</div>
                        <div style="height:4px;background:#1e1e2e;border-radius:2px;overflow:hidden;">
                            <div style="width:{score}%;height:100%;background:{fc};border-radius:2px;"></div>
                        </div>
                        <div style="font-size:12px;font-weight:700;color:{fc};text-align:right;">{score}</div>
                        <div style="font-size:11px;color:#6b6b8a;">{acao}</div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with tab_ads:
                if not item["pode_anunciar"]:
                    motivos = []
                    if item["estoque"] == 0:
                        motivos.append("estoque zerado")
                    if item["status"] != "active":
                        motivos.append("anúncio fechado")
                    if item["vendas"] == 0:
                        motivos.append("sem histórico")
                    st.markdown(f'<div class="alerta-critico"><div class="alerta-titulo">⚠️ Não recomendado anunciar agora — {", ".join(motivos)}</div><div class="alerta-acao">Resolva os problemas acima antes de ativar ads.</div></div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="font-size:13px;color:#9FE1CB;margin-bottom:16px;">✅ Este produto está pronto para anunciar.</div>', unsafe_allow_html=True)
                    col_m1, col_m2, col_m3 = st.columns(3)
                    margem = col_m1.number_input("Margem líquida (%)", 1, 80, 20)
                    estagio = col_m2.selectbox("Estágio", ["novo", "crescimento", "consolidado"],
                        format_func=lambda x: {"novo": "Produto novo", "crescimento": "Em crescimento", "consolidado": "Consolidado"}[x])
                    budget_dia = col_m3.number_input("Budget diário (R$)", 10, 1000, 50)

                    roas_min = round(100 / margem, 1)
                    roas_rec = max(2, roas_min - 2) if estagio == "novo" else roas_min + 2 if estagio == "crescimento" else roas_min + 4
                    invest_mensal = budget_dia * 30
                    receita_ads = invest_mensal * roas_rec

                    r1, r2, r3, r4 = st.columns(4)
                    r1.metric("ROAS mínimo", f"{roas_min}x")
                    r2.metric("ROAS recomendado", f"{roas_rec}x")
                    r3.metric("Budget diário", f"R${budget_dia}")
                    r4.metric("Investimento mensal", f"R${invest_mensal:,}".replace(",", "."))

                    msgs = {
                        "novo": f"Produto novo: use ROAS {roas_rec}x para ganhar histórico. Aguarde 15 dias antes de ajustar.",
                        "crescimento": f"Em crescimento: ROAS {roas_rec}x e orçamento moderado. Aguarde 15 dias antes de ajustar lances.",
                        "consolidado": f"Consolidado: ROAS {roas_rec}x. Monitore TACOS — gasto ads / receita total da conta."
                    }
                    st.markdown(f'<div style="background:#0d2d1a;border:1px solid #00a650;border-radius:8px;padding:12px;font-size:12px;color:#9FE1CB;margin-top:12px;">💡 {msgs[estagio]}</div>', unsafe_allow_html=True)
                    st.caption("📌 Desde outubro/2025 o ML usa ROAS como métrica principal. Configure no painel de Product Ads.")

            with tab_preco:
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    cmv = st.number_input("Custo do produto (CMV)", 0.0, value=float(item['preco']) * 0.6, step=10.0)
                    tipo = st.selectbox("Tipo de anúncio", ["Clássico (12%)", "Premium (17%)"])
                    frete = st.selectbox("Frete", ["Padrão (~R$15)", "Full (R$0)", "Flex (~R$8)"])
                    imposto = st.selectbox("Regime fiscal", ["MEI (6%)", "Simples (10%)", "Lucro Presumido (15%)"])
                    margem_d = st.slider("Margem desejada (%)", 5, 50, 20)

                comissao_pct = 0.12 if "Clássico" in tipo else 0.17
                frete_val = 0 if "Full" in frete else 8 if "Flex" in frete else 15
                imposto_pct = 0.06 if "MEI" in imposto else 0.15 if "Lucro" in imposto else 0.10
                preco_ideal, com_val, imp_val, lucro = calcular_preco_ideal(cmv, comissao_pct, frete_val, imposto_pct, margem_d)
                margem_atual = ((item['preco'] - cmv - item['preco']*comissao_pct - frete_val - item['preco']*imposto_pct) / item['preco'] * 100) if item['preco'] > 0 else 0

                with col_p2:
                    st.markdown(f"""
                    <div class="card">
                        <div style="background:#00a65015;border:1px solid #00a650;border-radius:8px;padding:14px;text-align:center;margin-bottom:14px;">
                            <div style="font-size:11px;color:#00a650;margin-bottom:4px;">Preço ideal para {margem_d}% de margem</div>
                            <div style="font-size:32px;font-weight:900;color:#00a650;">R${preco_ideal:.2f}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    for label, val, cor_val in [
                        ("Preço atual", f"R${item['preco']}", "#e2e2f0"),
                        ("Comissão ML", f"- R${com_val:.2f}", "#e52b2b"),
                        ("Frete", f"- R${frete_val:.2f}", "#e52b2b"),
                        ("Impostos", f"- R${imp_val:.2f}", "#e52b2b"),
                        ("Lucro líquido", f"R${lucro:.2f}", "#00a650" if lucro > 0 else "#e52b2b"),
                    ]:
                        st.markdown(f'<div class="metric-row"><span class="metric-label">{label}</span><span class="metric-val" style="color:{cor_val};">{val}</span></div>', unsafe_allow_html=True)

                    cor_m = "#00a650" if margem_atual > 10 else "#f5a623" if margem_atual > 0 else "#e52b2b"
                    msg_m = f"✅ Margem atual: {margem_atual:.1f}%" if margem_atual > 10 else f"🟡 Margem apertada: {margem_atual:.1f}%" if margem_atual > 0 else f"⚠️ Vendendo no prejuízo: {margem_atual:.1f}%"
                    st.markdown(f'<div style="margin-top:12px;padding:10px;background:{cor_m}15;border-radius:6px;font-size:12px;color:{cor_m};">{msg_m}</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# CALCULADORA
# ============================================================
elif pagina == "🧮 Calculadora":
    st.markdown('<div style="padding:24px;">', unsafe_allow_html=True)
    st.markdown('<div style="font-size:20px;font-weight:700;color:#e2e2f0;margin-bottom:4px;">Calculadora de precificação</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:12px;color:#6b6b8a;margin-bottom:20px;">Calcule o preço ideal com todos os custos reais do ML</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        cmv = st.number_input("Custo do produto (CMV)", 0.0, value=150.0, step=5.0)
        tipo = st.selectbox("Tipo de anúncio", ["Clássico (12%)", "Premium (17%)"], key="calc_tipo")
        frete = st.selectbox("Frete", ["Padrão (~R$15)", "Full (R$0)", "Flex (~R$8)"], key="calc_frete")
        imposto = st.selectbox("Regime fiscal", ["MEI (6%)", "Simples (10%)", "Lucro Presumido (15%)"], key="calc_imp")
        margem_d = st.slider("Margem desejada (%)", 5, 60, 20, key="calc_margem")
        preco_atual = st.number_input("Seu preço atual (opcional)", 0.0, step=5.0, key="calc_preco")
        st.markdown('</div>', unsafe_allow_html=True)

    comissao_pct = 0.12 if "Clássico" in tipo else 0.17
    frete_val = 0 if "Full" in frete else 8 if "Flex" in frete else 15
    imposto_pct = 0.06 if "MEI" in imposto else 0.15 if "Lucro" in imposto else 0.10
    preco_ideal, com_val, imp_val, lucro = calcular_preco_ideal(cmv, comissao_pct, frete_val, imposto_pct, margem_d)
    margem_at = ((preco_atual - cmv - preco_atual*comissao_pct - frete_val - preco_atual*imposto_pct) / preco_atual * 100) if preco_atual > 0 else None

    with col2:
        st.markdown(f"""
        <div class="card">
            <div style="font-size:13px;font-weight:600;color:#e2e2f0;margin-bottom:14px;">Resultado</div>
            <div style="background:#00a65015;border:1px solid #00a650;border-radius:8px;padding:16px;text-align:center;margin-bottom:16px;">
                <div style="font-size:12px;color:#00a650;margin-bottom:4px;">Preço ideal para {margem_d}% de margem</div>
                <div style="font-size:40px;font-weight:900;color:#00a650;">R${preco_ideal:.2f}</div>
            </div>
        """, unsafe_allow_html=True)
        for label, val, cor_val in [
            ("Comissão ML", f"- R${com_val:.2f}", "#e52b2b"),
            ("Frete", f"- R${frete_val:.2f}", "#e52b2b"),
            ("Impostos", f"- R${imp_val:.2f}", "#e52b2b"),
            ("Lucro líquido", f"R${lucro:.2f}", "#00a650" if lucro > 0 else "#e52b2b"),
        ]:
            st.markdown(f'<div class="metric-row"><span class="metric-label">{label}</span><span class="metric-val" style="color:{cor_val};">{val}</span></div>', unsafe_allow_html=True)

        if margem_at is not None:
            cor_m = "#00a650" if margem_at > 10 else "#f5a623" if margem_at > 0 else "#e52b2b"
            msg_m = f"✅ Margem atual: {margem_at:.1f}%" if margem_at > 10 else f"🟡 Margem apertada: {margem_at:.1f}%" if margem_at > 0 else f"⚠️ Vendendo no prejuízo: {margem_at:.1f}%"
            st.markdown(f'<div style="margin-top:12px;padding:10px;background:{cor_m}15;border-radius:6px;font-size:12px;color:{cor_m};">{msg_m}</div>', unsafe_allow_html=True)
        st.caption("📌 Fórmula: Lucro = Preço - CMV - Comissão ML - Frete - Impostos")
        st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# PLANO DE AÇÃO
# ============================================================
elif pagina == "📋 Plano de ação":
    st.markdown('<div style="padding:24px;">', unsafe_allow_html=True)
    st.markdown('<div style="font-size:20px;font-weight:700;color:#e2e2f0;margin-bottom:4px;">Plano de ação</div>', unsafe_allow_html=True)

    if "diagnostico" not in st.session_state:
        with st.spinner("Carregando diagnóstico..."):
            st.session_state["diagnostico"] = diagnostico_conta(ACCESS, UID)

    r = st.session_state["diagnostico"]
    st.markdown(f'<div style="font-size:12px;color:#6b6b8a;margin-bottom:20px;">Baseado no diagnóstico de {r["gerado_em"]}</div>', unsafe_allow_html=True)

    criticos = [a for a in r["alertas"] if a["tipo"] == "CRITICO"]
    atencoes = [a for a in r["alertas"] if a["tipo"] == "ATENCAO"]

    if criticos:
        st.markdown('<div style="font-size:14px;font-weight:600;color:#e52b2b;margin-bottom:10px;">🔴 Ações imediatas — faça hoje</div>', unsafe_allow_html=True)
        for i, a in enumerate(criticos, 1):
            with st.expander(f"{i}. [{a['categoria']}] {a['mensagem'][:70]}..."):
                st.markdown(f"**Problema:** {a['mensagem']}")
                st.markdown(f"**O que fazer:** {a['acao']}")
                st.caption(f"📌 {a['referencia']}")

    if atencoes:
        st.markdown('<div style="font-size:14px;font-weight:600;color:#f5a623;margin:20px 0 10px;">🟡 Ações desta semana</div>', unsafe_allow_html=True)
        for i, a in enumerate(atencoes, 1):
            with st.expander(f"{i}. [{a['categoria']}] {a['mensagem'][:70]}..."):
                st.markdown(f"**Problema:** {a['mensagem']}")
                st.markdown(f"**O que fazer:** {a['acao']}")
                st.caption(f"📌 {a['referencia']}")

    if not criticos and not atencoes:
        st.markdown('<div style="background:#0d2d1a;border:1px solid #00a650;border-radius:10px;padding:20px;text-align:center;color:#9FE1CB;">🎉 Sua operação está saudável! Continue monitorando semanalmente.</div>', unsafe_allow_html=True)
