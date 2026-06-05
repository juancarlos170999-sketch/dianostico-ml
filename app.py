import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

CLIENT_ID = "8361153242610469"
CLIENT_SECRET = st.secrets["CLIENT_SECRET"]
REDIRECT_URI = "https://httpbin.org/get"

# ============================================================
# AUTH
# ============================================================
def get_access_token(code):
    r = requests.post("https://api.mercadolibre.com/oauth/token", data={
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI
    })
    return r.json()

# ============================================================
# DIAGNÓSTICO DA CONTA
# ============================================================
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
            "acao": "Investigate causa: estoque desatualizado, preço errado ou problema logístico.",
            "referencia": "Meta ML Brasil: ≤1% de cancelamentos pelo vendedor"})

    if taxa_reclamacao > 0.02:
        score_op -= 40
        resultado["alertas"].append({"tipo": "CRITICO", "categoria": "Operação", "impacto": "ALTO",
            "mensagem": f"Reclamações: {round(taxa_reclamacao*100,1)}%. Acima do limite de 2%.",
            "acao": "Responda todas as reclamações em até 48h. Revise descrição dos produtos.",
            "referencia": "Meta ML Brasil: ≤2% de reclamações nos últimos 60 dias"})

    resultado["scores"]["operacao"] = max(0, score_op)
    resultado["metricas"]["operacao"] = {
        "atraso": f"{round(taxa_atraso*100,1)}%",
        "cancelamento": f"{round(taxa_cancelamento*100,1)}%",
        "reclamacao": f"{round(taxa_reclamacao*100,1)}%",
        "vendas_60d": vendas_60d
    }
    resultado["metricas"]["reputacao"] = {
        "nivel": nivel,
        "positivas": f"{round(positivas*100,1)}%",
        "negativas": f"{round(negativas*100,1)}%",
        "total_vendas": transacoes.get("total", 0),
        "canceladas": transacoes.get("canceled", 0)
    }

    r_perguntas = requests.get(f"https://api.mercadolibre.com/questions/search?seller_id={user_id}&status=UNANSWERED", headers=H)
    perguntas = 0
    if r_perguntas.status_code == 200:
        perguntas = r_perguntas.json().get("total", 0)
    score_atend = 100
    if perguntas > 10:
        score_atend -= 40
        resultado["alertas"].append({"tipo": "CRITICO", "categoria": "Atendimento", "impacto": "ALTO",
            "mensagem": f"{perguntas} perguntas sem resposta. Compradores indo para concorrentes.",
            "acao": "Responda todas as perguntas. Ideal: menos de 1 hora por resposta.",
            "referencia": "Tempo de resposta impacta diretamente conversão e posicionamento"})
    elif perguntas > 3:
        score_atend -= 20
        resultado["alertas"].append({"tipo": "ATENCAO", "categoria": "Atendimento", "impacto": "MÉDIO",
            "mensagem": f"{perguntas} perguntas sem resposta.",
            "acao": "Crie rotina de resposta diária. Ideal: menos de 1 hora.",
            "referencia": "ML considera bom tempo de resposta: até 1 hora"})
    resultado["scores"]["atendimento"] = max(0, score_atend)
    resultado["metricas"]["atendimento"] = {"perguntas_sem_resposta": perguntas}

    r_itens = requests.get(f"https://api.mercadolibre.com/users/{user_id}/items/search", headers=H)
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
            problemas.append("🔴 Ruptura com ads ativo")
            resultado["alertas"].append({"tipo": "CRITICO", "categoria": "Estoque", "impacto": "ALTO",
                "mensagem": f"'{titulo_curto}' ATIVO com estoque ZERO.",
                "acao": "Pause o anúncio imediatamente ou reponha estoque urgente.",
                "referencia": "Anúncio ativo sem estoque queima budget de ads e derruba conversão"})
        elif estoque == 0 and status == "closed" and vendas > 0:
            score_estoque -= 10
            problemas.append(f"🟡 Fechado — {vendas} vendas anteriores")
            resultado["alertas"].append({"tipo": "ATENCAO", "categoria": "Estoque", "impacto": "MÉDIO",
                "mensagem": f"'{titulo_curto}' fechado com {vendas} vendas anteriores.",
                "acao": f"Repor estoque e reativar. Potencial: R${preco} por venda.",
                "referencia": "Produto com histórico tem mais chance de conversão quando reativado"})
        elif 0 < estoque <= 5 and status == "active":
            itens_baixo += 1
            problemas.append(f"🟡 Estoque crítico: {estoque} un.")
            resultado["alertas"].append({"tipo": "ATENCAO", "categoria": "Estoque", "impacto": "MÉDIO",
                "mensagem": f"'{titulo_curto}' com apenas {estoque} unidades.",
                "acao": "Repor estoque antes de atingir zero.",
                "referencia": "Ruptura frequente pode levar à desativação automática pelo ML"})

        if logistica not in ["fulfillment", "xd_drop_off"] and status == "active":
            problemas.append("⚠️ Sem Full/Flex")

        resultado["skus"].append({
            "Produto": titulo_curto,
            "Preço": f"R${preco}",
            "Estoque": estoque,
            "Vendas": vendas,
            "Status": "✅ Ativo" if status == "active" else "⛔ Fechado",
            "Logística": logistica or "Padrão",
            "Situação": " | ".join(problemas) if problemas else "✅ OK"
        })

    resultado["scores"]["estoque"] = max(0, score_estoque)
    resultado["metricas"]["estoque"] = {
        "total_itens": total_itens, "itens_ativos": itens_ativos,
        "itens_ruptura": itens_ruptura, "itens_estoque_baixo": itens_baixo
    }

    r_adv = requests.get("https://api.mercadolibre.com/advertising/advertisers?product_id=PADS",
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
                    m = c.get("metrics", {})
                    roas = m.get("roas", 0) or 0
                    nome = c.get("name", "Campanha")
                    if roas and roas < 3:
                        score_ads -= 20
                        resultado["alertas"].append({"tipo": "CRITICO", "categoria": "Publicidade", "impacto": "ALTO",
                            "mensagem": f"Campanha '{nome}': ROAS {round(roas,1)}x — abaixo do mínimo recomendado.",
                            "acao": "Pause itens sem conversão. ROAS mínimo para lucrar = 100 / margem%.",
                            "referencia": "Desde out/2025 o ML usa ROAS como métrica principal. Ideal: acima de 5x para margens de 20%"})
    else:
        score_ads = 50
        resultado["alertas"].append({"tipo": "INFO", "categoria": "Publicidade", "impacto": "BAIXO",
            "mensagem": "Conta sem Product Ads ativo.",
            "acao": "Ative Product Ads nos SKUs com histórico de vendas e estoque ok.",
            "referencia": "Sellers com ads têm prioridade no posicionamento orgânico do ML"})
    resultado["scores"]["publicidade"] = max(0, score_ads)

    pesos = {"reputacao": 0.30, "operacao": 0.25, "estoque": 0.20, "atendimento": 0.15, "publicidade": 0.10}
    resultado["score_total"] = int(sum(resultado["scores"][k] * v for k, v in pesos.items()))
    resultado["status"] = "SAUDAVEL" if resultado["score_total"] >= 80 else "ATENCAO" if resultado["score_total"] >= 60 else "CRITICO"
    ordem = {"CRITICO": 0, "ATENCAO": 1, "INFO": 2}
    resultado["alertas"].sort(key=lambda x: ordem.get(x["tipo"], 3))
    return resultado

# ============================================================
# ANÁLISE DE ITEM ESPECÍFICO
# ============================================================
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
    tipo_anuncio = item.get("listing_type_id", "")

    r_desc = requests.get(f"https://api.mercadolibre.com/items/{item_id}/description", headers=H)
    descricao = r_desc.json().get("plain_text", "") if r_desc.status_code == 200 else ""

    scores = {}
    acoes = {}
    chars = len(titulo)
    if chars >= 55:
        scores["titulo"] = 90
        acoes["titulo"] = f"Bom — {chars}/60 caracteres usados."
    elif chars >= 40:
        scores["titulo"] = 60
        acoes["titulo"] = f"Médio — {chars}/60 caracteres. Adicione especificação técnica."
    else:
        scores["titulo"] = 25
        acoes["titulo"] = f"Crítico — {chars}/60 caracteres. Use todos os 60 com marca + modelo + especificação."

    n_fotos = len(fotos)
    if n_fotos >= 6:
        scores["fotos"] = 90
        acoes["fotos"] = f"{n_fotos} fotos — bom. Mantenha fundo branco na principal."
    elif n_fotos >= 4:
        scores["fotos"] = 60
        acoes["fotos"] = f"{n_fotos} fotos — adicione mais {6-n_fotos} fotos. ML recomenda mínimo 6."
    elif n_fotos >= 2:
        scores["fotos"] = 30
        acoes["fotos"] = f"Apenas {n_fotos} fotos — adicione 6 fotos 1200x1200px com ângulos diferentes."
    else:
        scores["fotos"] = 5
        acoes["fotos"] = "Sem fotos suficientes — anúncio invisível. Adicione mínimo 6 fotos imediatamente."

    n_attrs = len(atributos)
    if n_attrs >= 10:
        scores["ficha"] = 90
        acoes["ficha"] = f"{n_attrs} atributos — bom. Verifique campos obrigatórios em branco."
    elif n_attrs >= 6:
        scores["ficha"] = 55
        acoes["ficha"] = f"{n_attrs} atributos — incompleto. Preencha todos os campos da categoria."
    elif n_attrs >= 3:
        scores["ficha"] = 25
        acoes["ficha"] = f"Apenas {n_attrs} atributos — crítico. Preencha toda a ficha técnica."
    else:
        scores["ficha"] = 5
        acoes["ficha"] = "Ficha técnica vazia — não aparece em filtros. Preencha urgente."

    chars_desc = len(descricao)
    if chars_desc >= 500:
        scores["descricao"] = 85
        acoes["descricao"] = "Descrição completa. Verifique se inclui o que vem na caixa e garantia."
    elif chars_desc >= 200:
        scores["descricao"] = 55
        acoes["descricao"] = "Descrição básica. Adicione: o que vem na caixa, compatibilidade e garantia."
    elif chars_desc > 0:
        scores["descricao"] = 25
        acoes["descricao"] = "Descrição muito curta. Expanda com benefícios e quebra de objeções."
    else:
        scores["descricao"] = 0
        acoes["descricao"] = "Sem descrição — adicione uma descrição completa para reduzir perguntas."

    scores["preco"] = 75 if preco > 0 else 0
    acoes["preco"] = f"R${preco} — monitore. ML exige paridade com Amazon e Shopee em até 3 dias."

    r_rep = requests.get(f"https://api.mercadolibre.com/users/{user_id}", headers=H)
    nivel = r_rep.json().get("seller_reputation", {}).get("level_id", "") if r_rep.status_code == 200 else ""
    nivel_scores = {"5_green": 100, "4_light_green": 80, "3_yellow": 55, "2_orange": 30, "1_red": 10}
    scores["reputacao"] = nivel_scores.get(nivel, 50)
    nivel_labels = {"5_green": "Verde", "4_light_green": "Verde claro", "3_yellow": "Amarela", "2_orange": "Laranja", "1_red": "Vermelha"}
    acoes["reputacao"] = f"Reputação {nivel_labels.get(nivel, 'não identificada')} — impacta posicionamento deste anúncio."

    if logistica == "fulfillment":
        scores["logistica"] = 100
        acoes["logistica"] = "Full ativo — máxima prioridade. 3x mais chances de venda."
    elif logistica == "xd_drop_off":
        scores["logistica"] = 75
        acoes["logistica"] = "Flex ativo — entrega no mesmo dia. Boa prioridade no algoritmo."
    else:
        scores["logistica"] = 0
        acoes["logistica"] = "Envio padrão — menor prioridade. Ative Full para triplicar chances de venda."

    if vendas >= 20:
        scores["conversao"] = 90
        acoes["conversao"] = f"{vendas} vendas — histórico forte. Responda perguntas em menos de 1 hora."
    elif vendas >= 5:
        scores["conversao"] = 60
        acoes["conversao"] = f"{vendas} vendas — moderado. Responda perguntas rapidamente."
    elif vendas >= 1:
        scores["conversao"] = 30
        acoes["conversao"] = f"Apenas {vendas} venda — fraco. Foque em título e fotos primeiro."
    else:
        scores["conversao"] = 0
        acoes["conversao"] = "Sem vendas — aguarde histórico antes de investir em ads."

    pesos = {"titulo": 0.15, "fotos": 0.20, "ficha": 0.20, "descricao": 0.10,
             "preco": 0.10, "reputacao": 0.10, "logistica": 0.10, "conversao": 0.05}
    score_total = int(sum(scores[k] * pesos[k] for k in pesos))
    pode_anunciar = estoque > 0 and status == "active" and vendas >= 1

    return {
        "item_id": item_id, "titulo": titulo, "preco": preco,
        "estoque": estoque, "status": status, "vendas": vendas,
        "fotos": n_fotos, "logistica": logistica, "tipo_anuncio": tipo_anuncio,
        "score_total": score_total, "scores": scores, "acoes": acoes,
        "pode_anunciar": pode_anunciar, "n_atributos": n_attrs
    }

# ============================================================
# HELPERS VISUAIS
# ============================================================
def gauge(score, titulo):
    cor = "#00a650" if score >= 80 else "#f5a623" if score >= 60 else "#e52b2b"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": titulo, "font": {"size": 12}},
        number={"font": {"size": 28, "color": cor}},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": cor, "thickness": 0.25},
            "steps": [
                {"range": [0, 60], "color": "#fde8e8"},
                {"range": [60, 80], "color": "#fef3cd"},
                {"range": [80, 100], "color": "#d4edda"}
            ]
        }
    ))
    fig.update_layout(height=170, margin=dict(t=40, b=0, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)")
    return fig

def cor_score(s):
    return "#e52b2b" if s < 60 else "#f5a623" if s < 80 else "#00a650"

def calcular_roas_ideal(margem_pct, estagio):
    roas_min = round(100 / margem_pct, 1) if margem_pct > 0 else 5
    if estagio == "novo":
        return max(2, roas_min - 2), roas_min
    elif estagio == "crescimento":
        return roas_min + 2, roas_min
    else:
        return roas_min + 4, roas_min

def calcular_preco_ideal(cmv, comissao_pct, frete, imposto_pct, margem_pct):
    total_var = comissao_pct + imposto_pct + (margem_pct / 100)
    preco = (cmv + frete) / (1 - total_var)
    comissao = preco * comissao_pct
    imposto = preco * imposto_pct
    lucro = preco - cmv - comissao - frete - imposto
    return preco, comissao, imposto, lucro

# ============================================================
# INTERFACE
# ============================================================
st.set_page_config(page_title="RaioxSeller", page_icon="🔍", layout="wide")

st.markdown("""
<style>
[data-testid="stSidebar"] { background: #0f0f1a; }
.metric-card { background: #1a1a2e; border-radius: 12px; padding: 16px; border: 1px solid #2a2a3e; }
</style>
""", unsafe_allow_html=True)

# SIDEBAR
with st.sidebar:
    st.markdown("## 🔍 RaioxSeller")
    st.caption("Diagnóstico de performance ML")
    st.divider()
    pagina = st.radio("Navegação", [
        "🏠 Visão geral",
        "📦 Analisar produto",
        "🧮 Calculadora de preço",
        "📋 Plano de ação"
    ], label_visibility="collapsed")
    st.divider()

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
                    st.success("Conta conectada!")
                    st.rerun()
                else:
                    st.error("Código inválido. Gere um novo.")

    if "access_token" in st.session_state:
        st.success(f"✅ Conta conectada")

# VERIFICAÇÃO
if "access_token" not in st.session_state:
    st.title("🔍 RaioxSeller")
    st.info("Conecte sua conta do Mercado Livre na barra lateral para começar.")
    st.stop()

ACCESS = st.session_state["access_token"]
UID = st.session_state["user_id"]

# ============================================================
# PÁGINA: VISÃO GERAL
# ============================================================
if pagina == "🏠 Visão geral":
    if "diagnostico" not in st.session_state:
        with st.spinner("Analisando sua conta completa..."):
            st.session_state["diagnostico"] = diagnostico_conta(ACCESS, UID)

    r = st.session_state["diagnostico"]

    col_refresh = st.columns([8, 1])[1]
    if col_refresh.button("🔄"):
        del st.session_state["diagnostico"]
        st.rerun()

    cor = "#00a650" if r["status"] == "SAUDAVEL" else "#f5a623" if r["status"] == "ATENCAO" else "#e52b2b"
    emoji = "🟢" if r["status"] == "SAUDAVEL" else "🟡" if r["status"] == "ATENCAO" else "🔴"

    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.markdown(f"## Olá, **{r['seller']}** 👋")
        st.caption(f"Diagnóstico gerado em {r['gerado_em']}")
        nivel_labels = {"5_green": "🟢 Verde", "4_light_green": "🟢 Verde claro",
                        "3_yellow": "🟡 Amarelo", "2_orange": "🟠 Laranja", "1_red": "🔴 Vermelho"}
        st.markdown(f"**Reputação:** {nivel_labels.get(r['nivel'], r['nivel'])} &nbsp;|&nbsp; **MercadoLíder:** {r['mercadolider'].title()}")
    with col2:
        st.markdown(f"""<div style='text-align:center;background:{cor}22;border:2px solid {cor};border-radius:12px;padding:14px;'>
            <div style='font-size:48px;font-weight:900;color:{cor};'>{r["score_total"]}</div>
            <div style='font-size:11px;color:{cor};'>Score Geral /100</div></div>""", unsafe_allow_html=True)
    with col3:
        criticos = len([a for a in r["alertas"] if a["tipo"] == "CRITICO"])
        atencoes = len([a for a in r["alertas"] if a["tipo"] == "ATENCAO"])
        st.markdown(f"""<div style='text-align:center;border:1px solid #444;border-radius:12px;padding:14px;'>
            <div style='font-size:32px;font-weight:700;color:#e52b2b;'>{criticos}</div>
            <div style='font-size:11px;color:#aaa;'>Críticos</div>
            <div style='font-size:24px;font-weight:700;color:#f5a623;margin-top:6px;'>{atencoes}</div>
            <div style='font-size:11px;color:#aaa;'>Atenções</div></div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown("### 🎯 Problemas críticos")
    criticos_lista = [a for a in r["alertas"] if a["tipo"] == "CRITICO"]
    if criticos_lista:
        for i, a in enumerate(criticos_lista, 1):
            st.error(f"**{i}. [{a['categoria']}]** {a['mensagem']}\n\n→ **{a['acao']}**\n\n📌 *{a['referencia']}*")
    else:
        st.success("✅ Nenhum problema crítico. Operação saudável!")

    st.markdown("### 📊 Score por categoria")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.plotly_chart(gauge(r["scores"]["reputacao"], "Reputação"), use_container_width=True)
    c2.plotly_chart(gauge(r["scores"]["operacao"], "Operação"), use_container_width=True)
    c3.plotly_chart(gauge(r["scores"]["estoque"], "Estoque"), use_container_width=True)
    c4.plotly_chart(gauge(r["scores"]["atendimento"], "Atendimento"), use_container_width=True)
    c5.plotly_chart(gauge(r["scores"]["publicidade"], "Publicidade"), use_container_width=True)

    st.markdown("### 📈 Métricas detalhadas")
    tab1, tab2, tab3, tab4 = st.tabs(["Reputação & Operação", "Estoque & SKUs", "Atendimento", "Todos os alertas"])

    with tab1:
        ca, cb = st.columns(2)
        with ca:
            st.markdown("**Reputação**")
            m = r["metricas"].get("reputacao", {})
            st.metric("Avaliações positivas", m.get("positivas", "-"))
            st.metric("Avaliações negativas", m.get("negativas", "-"))
            st.metric("Total de vendas", m.get("total_vendas", "-"))
        with cb:
            st.markdown("**Operação** *(últimos 60 dias)*")
            m = r["metricas"].get("operacao", {})
            st.metric("Atraso no envio", m.get("atraso", "-"), delta="Meta: ≥90% no prazo", delta_color="off")
            st.metric("Cancelamentos", m.get("cancelamento", "-"), delta="Meta: ≤1%", delta_color="off")
            st.metric("Reclamações", m.get("reclamacao", "-"), delta="Meta: ≤2%", delta_color="off")
            st.metric("Vendas no período", m.get("vendas_60d", "-"))

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
        st.caption("Ideal: responder em menos de 1 hora. Impacta conversão e posicionamento.")

    with tab4:
        for a in r["alertas"]:
            if a["tipo"] == "CRITICO":
                st.error(f"🔴 **[{a['categoria']}]** {a['mensagem']}\n\n→ {a['acao']}\n\n📌 *{a['referencia']}*")
            elif a["tipo"] == "ATENCAO":
                st.warning(f"🟡 **[{a['categoria']}]** {a['mensagem']}\n\n→ {a['acao']}\n\n📌 *{a['referencia']}*")
            else:
                st.info(f"ℹ️ **[{a['categoria']}]** {a['mensagem']}\n\n→ {a['acao']}\n\n📌 *{a['referencia']}*")

# ============================================================
# PÁGINA: ANALISAR PRODUTO
# ============================================================
elif pagina == "📦 Analisar produto":
    st.markdown("## 📦 Analisar produto por MLB")
    st.caption("Cole o código MLB do produto para ver diagnóstico completo de qualidade, recomendação de ads e análise de preço.")

    col_input, col_btn = st.columns([4, 1])
    with col_input:
        mlb = st.text_input("", placeholder="Ex: MLB4341336433", label_visibility="collapsed")
    with col_btn:
        buscar = st.button("🔍 Analisar", use_container_width=True)

    if buscar and mlb:
        with st.spinner(f"Analisando {mlb}..."):
            item = analisar_item(mlb.strip().upper(), ACCESS, UID)

        if not item:
            st.error("Produto não encontrado. Verifique o MLB e tente novamente.")
        else:
            cor_s = cor_score(item["score_total"])
            st.divider()

            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.markdown(f"### {item['titulo']}")
                st.caption(f"MLB: {item['item_id']}")
                tags = []
                tags.append(f"R${item['preco']}")
                tags.append(f"Estoque: {item['estoque']}")
                tags.append(f"Vendas: {item['vendas']}")
                tags.append(item['logistica'] or "Padrão")
                st.markdown(" &nbsp;|&nbsp; ".join(f"`{t}`" for t in tags))
            with col_b:
                st.markdown(f"""<div style='text-align:center;background:{cor_s}22;border:2px solid {cor_s};border-radius:12px;padding:12px;'>
                    <div style='font-size:40px;font-weight:900;color:{cor_s};'>{item['score_total']}</div>
                    <div style='font-size:11px;color:{cor_s};'>Score /100</div></div>""", unsafe_allow_html=True)

            st.divider()

            tab_fat, tab_ads, tab_preco = st.tabs(["📊 8 fatores do algoritmo", "📢 Recomendação de Ads", "💰 Preço ideal"])

            with tab_fat:
                fatores = [
                    ("Título", "📝", item["scores"]["titulo"], item["acoes"]["titulo"]),
                    ("Fotos", "📸", item["scores"]["fotos"], item["acoes"]["fotos"]),
                    ("Ficha técnica", "📋", item["scores"]["ficha"], item["acoes"]["ficha"]),
                    ("Descrição", "📄", item["scores"]["descricao"], item["acoes"]["descricao"]),
                    ("Preço total", "💲", item["scores"]["preco"], item["acoes"]["preco"]),
                    ("Reputação da conta", "⭐", item["scores"]["reputacao"], item["acoes"]["reputacao"]),
                    ("Logística", "🚚", item["scores"]["logistica"], item["acoes"]["logistica"]),
                    ("Conversão/histórico", "📈", item["scores"]["conversao"], item["acoes"]["conversao"]),
                ]
                for nome, emoji_f, score, acao in fatores:
                    c1, c2, c3 = st.columns([2, 1, 3])
                    c1.markdown(f"{emoji_f} **{nome}**")
                    cor_f = cor_score(score)
                    c2.markdown(f"<span style='color:{cor_f};font-weight:700;'>{score}/100</span>", unsafe_allow_html=True)
                    c3.caption(acao)
                    st.progress(score / 100)

            with tab_ads:
                if not item["pode_anunciar"]:
                    motivos = []
                    if item["estoque"] == 0:
                        motivos.append("estoque zerado")
                    if item["status"] != "active":
                        motivos.append("anúncio fechado")
                    if item["vendas"] == 0:
                        motivos.append("sem histórico de vendas")
                    st.error(f"⚠️ **Não recomendado anunciar agora** — {', '.join(motivos)}.")
                    if item["estoque"] == 0:
                        st.info("Reponha o estoque primeiro. Anunciar com estoque zero é desperdício de budget.")
                    if item["vendas"] == 0:
                        st.info("Produto novo sem histórico. Aguarde 15 dias de dados orgânicos antes de ativar ads.")
                else:
                    st.success("✅ Este produto está pronto para anunciar.")
                    st.divider()
                    col_m1, col_m2, col_m3 = st.columns(3)
                    margem = col_m1.number_input("Sua margem líquida (%)", min_value=1, max_value=80, value=20)
                    fat_mensal = col_m2.selectbox("Faturamento mensal", ["Até R$5k", "R$5k–R$20k", "R$20k–R$50k", "R$50k–R$200k", "Acima de R$200k"])
                    estagio = col_m3.selectbox("Estágio do produto", ["novo", "crescimento", "consolidado"],
                        format_func=lambda x: {"novo": "Produto novo", "crescimento": "Em crescimento", "consolidado": "Consolidado"}[x])

                    budget_map = {"Até R$5k": 15, "R$5k–R$20k": 25, "R$20k–R$50k": 50, "R$50k–R$200k": 150, "Acima de R$200k": 400}
                    budget_dia = budget_map[fat_mensal]
                    roas_rec, roas_min = calcular_roas_ideal(margem, estagio)

                    st.divider()
                    r1, r2, r3, r4 = st.columns(4)
                    r1.metric("ROAS mínimo para lucrar", f"{roas_min}x")
                    r2.metric("ROAS objetivo recomendado", f"{roas_rec}x")
                    r3.metric("Orçamento diário sugerido", f"R${budget_dia}/dia")
                    r4.metric("Investimento mensal", f"~R${budget_dia*30:,}/mês".replace(",", "."))

                    msgs = {
                        "novo": f"Produto novo: use ROAS {roas_rec}x mais baixo para ganhar histórico. Aguarde 15 dias antes de qualquer ajuste.",
                        "crescimento": f"Em crescimento: ROAS {roas_rec}x e orçamento moderado. Aguarde 15 dias antes de ajustar lances.",
                        "consolidado": f"Consolidado: pode apertar o ROAS para {roas_rec}x e aumentar orçamento. Monitore TACOS — gasto ads / receita total."
                    }
                    st.info(f"💡 {msgs[estagio]}")
                    st.caption("📌 Desde outubro/2025 o ML usa ROAS como métrica principal. Configure o ROAS objetivo no painel de Product Ads.")

            with tab_preco:
                st.markdown(f"**Preço atual:** R${item['preco']}")
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    cmv = st.number_input("Custo do produto (CMV)", min_value=0.0, value=float(item['preco']) * 0.6, step=10.0)
                    tipo = st.selectbox("Tipo de anúncio", ["Clássico (12%)", "Premium (17%)"])
                    frete = st.selectbox("Frete", ["Padrão (~R$15)", "Full (incluso R$0)", "Flex (~R$8)"])
                    imposto = st.selectbox("Regime fiscal", ["MEI (6%)", "Simples Nacional (10%)", "Lucro Presumido (15%)"])
                    margem_d = st.slider("Margem desejada (%)", 5, 50, 20)

                comissao_pct = 0.12 if "Clássico" in tipo else 0.17
                frete_val = 0 if "Full" in frete else 8 if "Flex" in frete else 15
                imposto_pct = 0.06 if "MEI" in imposto else 0.15 if "Lucro" in imposto else 0.10

                preco_ideal, com_val, imp_val, lucro = calcular_preco_ideal(cmv, comissao_pct, frete_val, imposto_pct, margem_d)
                margem_atual = ((item['preco'] - cmv - item['preco']*comissao_pct - frete_val - item['preco']*imposto_pct) / item['preco'] * 100) if item['preco'] > 0 else 0

                with col_p2:
                    st.markdown("**Resultado**")
                    st.metric("Preço ideal para margem desejada", f"R${preco_ideal:,.0f}".replace(",", "."))
                    st.metric("Preço atual", f"R${item['preco']}", delta=f"{'acima' if item['preco'] >= preco_ideal else 'abaixo'} do ideal")
                    st.metric("Comissão ML", f"- R${com_val:,.0f}".replace(",", "."))
                    st.metric("Impostos", f"- R${imp_val:,.0f}".replace(",", "."))
                    st.metric("Lucro líquido no preço ideal", f"R${lucro:,.0f}".replace(",", "."),
                        delta=f"{margem_d}% de margem")
                    if margem_atual < 0:
                        st.error(f"⚠️ Com o preço atual você está vendendo no prejuízo ({margem_atual:.1f}% de margem).")
                    elif margem_atual < 10:
                        st.warning(f"🟡 Margem atual de {margem_atual:.1f}% — muito apertada.")
                    else:
                        st.success(f"✅ Margem atual estimada: {margem_atual:.1f}%")

# ============================================================
# PÁGINA: CALCULADORA
# ============================================================
elif pagina == "🧮 Calculadora de preço":
    st.markdown("## 🧮 Calculadora de precificação")
    st.caption("Calcule o preço ideal considerando todos os custos reais do Mercado Livre.")

    col1, col2 = st.columns(2)
    with col1:
        cmv = st.number_input("Custo do produto (CMV)", min_value=0.0, value=150.0, step=5.0)
        tipo = st.selectbox("Tipo de anúncio", ["Clássico (12%)", "Premium (17%)"])
        frete = st.selectbox("Modalidade de frete", ["Padrão (~R$15)", "Full (incluso R$0)", "Flex (~R$8)"])
        imposto = st.selectbox("Regime fiscal", ["MEI (6%)", "Simples Nacional (10%)", "Lucro Presumido (15%)"])
        margem_d = st.slider("Margem desejada (%)", 5, 60, 20)
        preco_atual = st.number_input("Seu preço atual (opcional)", min_value=0.0, value=0.0, step=5.0)

    comissao_pct = 0.12 if "Clássico" in tipo else 0.17
    frete_val = 0 if "Full" in frete else 8 if "Flex" in frete else 15
    imposto_pct = 0.06 if "MEI" in imposto else 0.15 if "Lucro" in imposto else 0.10
    preco_ideal, com_val, imp_val, lucro = calcular_preco_ideal(cmv, comissao_pct, frete_val, imposto_pct, margem_d)

    with col2:
        st.markdown("### Resultado")
        st.metric("Preço ideal", f"R${preco_ideal:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.metric("Comissão ML", f"- R${com_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.metric("Frete", f"- R${frete_val:.2f}".replace(".", ","))
        st.metric("Impostos", f"- R${imp_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.metric("Lucro líquido", f"R${lucro:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        if preco_atual > 0:
            margem_at = ((preco_atual - cmv - preco_atual*comissao_pct - frete_val - preco_atual*imposto_pct) / preco_atual * 100)
            if margem_at < 0:
                st.error(f"⚠️ Vendendo no prejuízo: {margem_at:.1f}% de margem no preço atual.")
            elif margem_at < 10:
                st.warning(f"🟡 Margem atual: {margem_at:.1f}% — muito apertada.")
            else:
                st.success(f"✅ Margem atual: {margem_at:.1f}%")

        st.caption("📌 Fórmula: Lucro = Preço - CMV - Comissão ML - Frete - Impostos")

# ============================================================
# PÁGINA: PLANO DE AÇÃO
# ============================================================
elif pagina == "📋 Plano de ação":
    st.markdown("## 📋 Plano de ação")

    if "diagnostico" not in st.session_state:
        with st.spinner("Carregando diagnóstico..."):
            st.session_state["diagnostico"] = diagnostico_conta(ACCESS, UID)

    r = st.session_state["diagnostico"]
    criticos = [a for a in r["alertas"] if a["tipo"] == "CRITICO"]
    atencoes = [a for a in r["alertas"] if a["tipo"] == "ATENCAO"]

    if criticos:
        st.markdown("### 🔴 Ações imediatas — faça hoje")
        for i, a in enumerate(criticos, 1):
            with st.expander(f"{i}. [{a['categoria']}] {a['mensagem'][:60]}..."):
                st.markdown(f"**Problema:** {a['mensagem']}")
                st.markdown(f"**O que fazer:** {a['acao']}")
                st.caption(f"📌 {a['referencia']}")

    if atencoes:
        st.markdown("### 🟡 Ações desta semana")
        for i, a in enumerate(atencoes, 1):
            with st.expander(f"{i}. [{a['categoria']}] {a['mensagem'][:60]}..."):
                st.markdown(f"**Problema:** {a['mensagem']}")
                st.markdown(f"**O que fazer:** {a['acao']}")
                st.caption(f"📌 {a['referencia']}")

    if not criticos and not atencoes:
        st.success("🎉 Sua operação está saudável! Continue monitorando semanalmente.")
