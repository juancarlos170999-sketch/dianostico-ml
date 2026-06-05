import streamlit as st
import requests
from datetime import datetime
import plotly.graph_objects as go
import pandas as pd

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

def diagnostico_completo(access_token, user_id):
    H = {"Authorization": f"Bearer {access_token}"}
    resultado = {
        "seller": "", "nivel": "", "mercadolider": "",
        "score_total": 100,
        "scores": {"reputacao": 100, "operacao": 100, "estoque": 100, "publicidade": 100, "atendimento": 100},
        "status": "", "alertas": [], "skus": [],
        "metricas": {},
        "gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M")
    }

    # ==================== BLOCO 1: REPUTAÇÃO ====================
    r = requests.get(f"https://api.mercadolibre.com/users/{user_id}", headers=H)
    dados = r.json()
    resultado["seller"] = dados.get("nickname", "")
    rep = dados.get("seller_reputation", {})
    metricas = rep.get("metrics", {})
    transacoes = rep.get("transactions", {})
    nivel = rep.get("level_id", "")
    resultado["nivel"] = nivel
    resultado["mercadolider"] = rep.get("power_seller_status") or "Não é MercadoLíder"

    # Score de reputação baseado no nível real
    nivel_scores = {
        "5_green": 100, "4_light_green": 75,
        "3_yellow": 55, "2_orange": 30, "1_red": 10
    }
    resultado["scores"]["reputacao"] = nivel_scores.get(nivel, 50)

    if nivel in ["1_red", "2_orange"]:
        resultado["alertas"].append({
            "tipo": "CRITICO", "categoria": "Reputação", "impacto": "ALTO",
            "mensagem": f"Reputação {nivel.split('_')[1].upper()}. Visibilidade e Buy Box comprometidos.",
            "acao": "Prioridade máxima: resolver reclamações abertas e reduzir cancelamentos imediatamente.",
            "referencia": "Meta: < 3% reclamações, < 2% cancelamentos, < 15% atraso"
        })
    elif nivel == "3_yellow":
        resultado["alertas"].append({
            "tipo": "ATENCAO", "categoria": "Reputação", "impacto": "MÉDIO",
            "mensagem": "Reputação AMARELA. Perda de posicionamento e Buy Box.",
            "acao": "Foco em reduzir atrasos abaixo de 15% e cancelamentos abaixo de 2%.",
            "referencia": "Meta Brasil: < 3% reclamações, < 2% cancelamentos, < 15% atraso"
        })

    # Avaliações
    ratings = transacoes.get("ratings", {})
    positivas = ratings.get("positive", 0)
    negativas = ratings.get("negative", 0)
    if negativas > 0.04:
        resultado["alertas"].append({
            "tipo": "ATENCAO", "categoria": "Reputação", "impacto": "MÉDIO",
            "mensagem": f"Taxa de avaliações negativas: {round(negativas*100,1)}%. Ideal: abaixo de 4%.",
            "acao": "Investigar motivos de insatisfação e melhorar descrição dos produtos.",
            "referencia": "Avaliações positivas ideais: acima de 88%"
        })

    resultado["metricas"]["reputacao"] = {
        "nivel": nivel,
        "positivas": f"{round(positivas*100,1)}%",
        "negativas": f"{round(negativas*100,1)}%",
        "total_vendas": transacoes.get("total", 0),
        "canceladas": transacoes.get("canceled", 0)
    }

    # ==================== BLOCO 2: OPERAÇÃO ====================
    taxa_atraso = metricas.get("delayed_handling_time", {}).get("rate", 0)
    taxa_cancelamento = metricas.get("cancellations", {}).get("rate", 0)
    taxa_reclamacao = metricas.get("claims", {}).get("rate", 0)
    vendas_60d = metricas.get("sales", {}).get("completed", 0)

    score_op = 100

    # Atraso no envio — limite Brasil: 15%
    if taxa_atraso > 0.15:
        score_op -= 40
        resultado["alertas"].append({
            "tipo": "CRITICO", "categoria": "Operação", "impacto": "ALTO",
            "mensagem": f"Atraso no envio: {round(taxa_atraso*100,1)}%. ACIMA do limite de 15% para reputação verde.",
            "acao": "Revisar prazo de handling. Considerar Mercado Envios Full para garantir SLA.",
            "referencia": "Limite Brasil para verde: < 15% de atraso nos últimos 60 dias"
        })
    elif taxa_atraso > 0.10:
        score_op -= 20
        resultado["alertas"].append({
            "tipo": "ATENCAO", "categoria": "Operação", "impacto": "MÉDIO",
            "mensagem": f"Atraso no envio: {round(taxa_atraso*100,1)}%. Próximo do limite crítico de 15%.",
            "acao": "Ajustar prazo de handling nos anúncios e otimizar processo de expedição.",
            "referencia": "Limite Brasil para verde: < 15% de atraso"
        })

    # Cancelamentos — limite Brasil: 2%
    if taxa_cancelamento > 0.02:
        score_op -= 35
        resultado["alertas"].append({
            "tipo": "CRITICO", "categoria": "Operação", "impacto": "ALTO",
            "mensagem": f"Taxa de cancelamento: {round(taxa_cancelamento*100,1)}%. ACIMA do limite de 2%.",
            "acao": "Investigar causa dos cancelamentos: estoque desatualizado, preço errado ou problema logístico.",
            "referencia": "Limite Brasil para verde: < 2% de cancelamentos pelo vendedor"
        })
    elif taxa_cancelamento > 0.01:
        score_op -= 15
        resultado["alertas"].append({
            "tipo": "ATENCAO", "categoria": "Operação", "impacto": "MÉDIO",
            "mensagem": f"Taxa de cancelamento: {round(taxa_cancelamento*100,1)}%. Monitorar de perto.",
            "acao": "Manter estoque atualizado e revisar processos de confirmação de pedido.",
            "referencia": "Limite Brasil para verde: < 2% de cancelamentos"
        })

    # Reclamações — limite Brasil: 3%
    if taxa_reclamacao > 0.03:
        score_op -= 40
        resultado["alertas"].append({
            "tipo": "CRITICO", "categoria": "Operação", "impacto": "ALTO",
            "mensagem": f"Taxa de reclamações: {round(taxa_reclamacao*100,1)}%. ACIMA do limite de 3%.",
            "acao": "Responder todas as reclamações em até 48h. Revisar descrição dos produtos para reduzir divergências.",
            "referencia": "Limite Brasil para verde: < 3% de reclamações nos últimos 60 dias"
        })
    elif taxa_reclamacao > 0.02:
        score_op -= 20
        resultado["alertas"].append({
            "tipo": "ATENCAO", "categoria": "Operação", "impacto": "MÉDIO",
            "mensagem": f"Taxa de reclamações: {round(taxa_reclamacao*100,1)}%. Próximo do limite crítico.",
            "acao": "Melhorar descrição dos produtos e pós-venda para reduzir insatisfação.",
            "referencia": "Limite Brasil para verde: < 3% de reclamações"
        })

    resultado["scores"]["operacao"] = max(0, score_op)
    resultado["metricas"]["operacao"] = {
        "atraso": f"{round(taxa_atraso*100,1)}%",
        "cancelamento": f"{round(taxa_cancelamento*100,1)}%",
        "reclamacao": f"{round(taxa_reclamacao*100,1)}%",
        "vendas_60d": vendas_60d
    }

    # ==================== BLOCO 3: ATENDIMENTO ====================
    r_perguntas = requests.get(
        f"https://api.mercadolibre.com/questions/search?seller_id={user_id}&status=UNANSWERED",
        headers=H
    )
    perguntas_sem_resposta = 0
    if r_perguntas.status_code == 200:
        perguntas_sem_resposta = r_perguntas.json().get("total", 0)

    score_atend = 100
    if perguntas_sem_resposta > 10:
        score_atend -= 40
        resultado["alertas"].append({
            "tipo": "CRITICO", "categoria": "Atendimento", "impacto": "ALTO",
            "mensagem": f"{perguntas_sem_resposta} perguntas sem resposta. Compradores indo para concorrentes.",
            "acao": "Responder todas as perguntas em aberto. Ideal: resposta em menos de 1 hora.",
            "referencia": "Perguntas sem resposta reduzem conversão e posicionamento no algoritmo do ML"
        })
    elif perguntas_sem_resposta > 3:
        score_atend -= 20
        resultado["alertas"].append({
            "tipo": "ATENCAO", "categoria": "Atendimento", "impacto": "MÉDIO",
            "mensagem": f"{perguntas_sem_resposta} perguntas sem resposta.",
            "acao": "Criar rotina de resposta diária. Tempo ideal: menos de 1 hora por pergunta.",
            "referencia": "ML considera bom tempo de resposta: até 1 hora"
        })

    resultado["scores"]["atendimento"] = max(0, score_atend)
    resultado["metricas"]["atendimento"] = {
        "perguntas_sem_resposta": perguntas_sem_resposta
    }

    # ==================== BLOCO 4: ESTOQUE E SKUs ====================
    r_itens = requests.get(
        f"https://api.mercadolibre.com/users/{user_id}/items/search",
        headers=H
    )
    item_ids = r_itens.json().get("results", [])
    score_estoque = 100
    total_itens = len(item_ids)
    itens_ativos = 0
    itens_ruptura = 0
    itens_estoque_baixo = 0
    receita_parada = 0

    for item_id in item_ids:
        r_item = requests.get(f"https://api.mercadolibre.com/items/{item_id}", headers=H)
        item = r_item.json()
        titulo = item.get("title", "")
        titulo_curto = titulo[:45] + "..." if len(titulo) > 45 else titulo
        estoque = item.get("available_quantity", 0)
        status = item.get("status", "")
        vendas = item.get("sold_quantity", 0)
        preco = item.get("price", 0)
        tipo_anuncio = item.get("listing_type_id", "")
        saude = item.get("health", 0) or 0
        logistica = item.get("shipping", {}).get("logistic_type", "")
        problemas = []

        if status == "active":
            itens_ativos += 1

        # Ruptura com anúncio ativo — crítico
        if estoque == 0 and status == "active":
            itens_ruptura += 1
            score_estoque -= 25
            problemas.append("🔴 Ruptura com anúncio ativo")
            resultado["alertas"].append({
                "tipo": "CRITICO", "categoria": "Estoque", "impacto": "ALTO",
                "mensagem": f"'{titulo_curto}' ATIVO com estoque ZERO. Compradores chegam e não compram.",
                "acao": "Pausar anúncio imediatamente ou repor estoque urgente.",
                "referencia": "Anúncio ativo sem estoque queima budget de ads e derruba conversão"
            })

        # Fechado com histórico de vendas
        elif estoque == 0 and status == "closed" and vendas > 0:
            score_estoque -= 10
            receita_parada += preco
            problemas.append(f"🟡 Fechado — {vendas} vendas anteriores")
            resultado["alertas"].append({
                "tipo": "ATENCAO", "categoria": "Estoque", "impacto": "MÉDIO",
                "mensagem": f"'{titulo_curto}' fechado com histórico de {vendas} vendas. Receita parada.",
                "acao": f"Repor estoque e reativar. Potencial por venda: R${preco}.",
                "referencia": "Produto com histórico de vendas tem mais chance de conversão quando reativado"
            })

        # Estoque baixo
        elif 0 < estoque <= 5 and status == "active":
            itens_estoque_baixo += 1
            problemas.append(f"🟡 Estoque crítico: {estoque} un.")
            resultado["alertas"].append({
                "tipo": "ATENCAO", "categoria": "Estoque", "impacto": "MÉDIO",
                "mensagem": f"'{titulo_curto}' com apenas {estoque} unidades. Risco de ruptura iminente.",
                "acao": "Repor estoque antes de atingir zero para não perder posicionamento.",
                "referencia": "Ruptura frequente pode levar à desativação automática pelo ML"
            })

        # Tipo de anúncio
        if tipo_anuncio == "gold_special":
            problemas.append("ℹ️ Anúncio Clássico")
        elif tipo_anuncio == "gold_pro":
            problemas.append("✅ Anúncio Premium")

        # Logística
        if logistica == "fulfillment":
            problemas.append("✅ Full")
        elif logistica == "xd_drop_off":
            problemas.append("✅ Flex")
        elif logistica not in ["fulfillment", "xd_drop_off"] and status == "active":
            problemas.append("⚠️ Sem Full/Flex")
            resultado["alertas"].append({
                "tipo": "ATENCAO", "categoria": "Posicionamento", "impacto": "MÉDIO",
                "mensagem": f"'{titulo_curto}' sem Full ou Flex. Desvantagem no algoritmo.",
                "acao": "Migrar para Mercado Envios Full para ganhar posicionamento e Buy Box.",
                "referencia": "Full garante entrega em 1-2 dias e prioridade no algoritmo do ML"
            })

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
        "total_itens": total_itens,
        "itens_ativos": itens_ativos,
        "itens_ruptura": itens_ruptura,
        "itens_estoque_baixo": itens_estoque_baixo,
        "receita_parada": f"R${receita_parada}"
    }

    # ==================== BLOCO 5: PUBLICIDADE ====================
    r_adv = requests.get(
        "https://api.mercadolibre.com/advertising/advertisers?product_id=PADS",
        headers={**H, "Api-Version": "1"}
    )
    score_ads = 100

    if r_adv.status_code == 200:
        advertisers = r_adv.json().get("advertisers", [])
        if advertisers:
            advertiser_id = advertisers[0].get("advertiser_id")
            hoje = datetime.now()
            date_to = hoje.strftime("%Y-%m-%d")
            date_from = f"{hoje.year}-01-01"

            r_camp = requests.get(
                f"https://api.mercadolibre.com/advertising/advertisers/{advertiser_id}/product_ads/campaigns/search"
                f"?date_from={date_from}&date_to={date_to}&metrics=clicks,cost,acos,prints,ctr",
                headers={**H, "Api-Version": "2"}
            )

            if r_camp.status_code == 200:
                campanhas = r_camp.json().get("campaigns", [])
                for c in campanhas:
                    m = c.get("metrics", {})
                    acos = m.get("acos", 0) or 0
                    ctr = m.get("ctr", 0) or 0
                    custo = m.get("cost", 0) or 0
                    clicks = m.get("clicks", 0) or 0
                    nome = c.get("name", "Campanha")
                    status_camp = c.get("status", "")

                    # ACOS alto
                    if acos > 0.20:
                        score_ads -= 20
                        resultado["alertas"].append({
                            "tipo": "CRITICO", "categoria": "Publicidade", "impacto": "ALTO",
                            "mensagem": f"Campanha '{nome}': ACOS {round(acos*100,1)}%. Acima do ideal de 15-20%.",
                            "acao": "Pausar itens sem conversão, revisar lances e negativar palavras-chave irrelevantes.",
                            "referencia": "ACOS ideal varia por categoria. Geral: abaixo de 15-20%"
                        })

                    # CTR baixo
                    if ctr and ctr < 0.005:
                        score_ads -= 10
                        resultado["alertas"].append({
                            "tipo": "ATENCAO", "categoria": "Publicidade", "impacto": "MÉDIO",
                            "mensagem": f"Campanha '{nome}': CTR de {round(ctr*100,2)}%. Abaixo de 0.5%.",
                            "acao": "Revisar título, foto principal e preço. CTR baixo indica anúncio pouco atrativo.",
                            "referencia": "CTR abaixo de 0.5% indica problema de relevância ou qualidade do anúncio"
                        })

                    # Budget sem retorno
                    if custo > 0 and clicks == 0:
                        score_ads -= 15
                        resultado["alertas"].append({
                            "tipo": "CRITICO", "categoria": "Publicidade", "impacto": "ALTO",
                            "mensagem": f"Campanha '{nome}': R${custo} gastos sem nenhum clique registrado.",
                            "acao": "Pausar campanha e revisar configuração. Possível problema de segmentação.",
                            "referencia": "Gasto sem clique indica problema grave na configuração da campanha"
                        })

                resultado["metricas"]["publicidade"] = {
                    "campanhas": len(campanhas),
                    "advertiser_id": advertiser_id
                }
            else:
                resultado["metricas"]["publicidade"] = {"campanhas": 0}
        else:
            score_ads = 50
            resultado["alertas"].append({
                "tipo": "INFO", "categoria": "Publicidade", "impacto": "BAIXO",
                "mensagem": "Conta sem Product Ads ativo.",
                "acao": "Ativar Product Ads para aumentar visibilidade e vendas. Comece com budget pequeno.",
                "referencia": "Mercado Ads cresceu 26% em 2024. Sellers sem ads perdem posicionamento."
            })
            resultado["metricas"]["publicidade"] = {"campanhas": 0}
    else:
        score_ads = 50
        resultado["alertas"].append({
            "tipo": "INFO", "categoria": "Publicidade", "impacto": "BAIXO",
            "mensagem": "Conta sem Product Ads ativo.",
            "acao": "Ativar Product Ads para aumentar visibilidade.",
            "referencia": "Sellers com ads têm prioridade no posicionamento orgânico."
        })
        resultado["metricas"]["publicidade"] = {"campanhas": 0}

    resultado["scores"]["publicidade"] = max(0, score_ads)

    # ==================== SCORE FINAL ====================
    pesos = {
        "reputacao": 0.30,
        "operacao": 0.25,
        "estoque": 0.20,
        "atendimento": 0.15,
        "publicidade": 0.10
    }
    resultado["score_total"] = int(sum(
        resultado["scores"][k] * v for k, v in pesos.items()
    ))

    if resultado["score_total"] >= 80:
        resultado["status"] = "SAUDAVEL"
    elif resultado["score_total"] >= 60:
        resultado["status"] = "ATENCAO"
    else:
        resultado["status"] = "CRITICO"

    # Ordena alertas por prioridade
    ordem = {"CRITICO": 0, "ATENCAO": 1, "INFO": 2}
    resultado["alertas"].sort(key=lambda x: ordem.get(x["tipo"], 3))

    return resultado


def gauge(score, titulo):
    cor = "#00a650" if score >= 80 else "#f5a623" if score >= 60 else "#e52b2b"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": titulo, "font": {"size": 12}},
        number={"font": {"size": 28, "color": cor}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "gray"},
            "bar": {"color": cor, "thickness": 0.25},
            "steps": [
                {"range": [0, 60], "color": "#fde8e8"},
                {"range": [60, 80], "color": "#fef3cd"},
                {"range": [80, 100], "color": "#d4edda"}
            ],
            "threshold": {"line": {"color": cor, "width": 3}, "thickness": 0.75, "value": score}
        }
    ))
    fig.update_layout(height=170, margin=dict(t=40, b=0, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)")
    return fig


# ==================== INTERFACE ====================
st.set_page_config(page_title="Diagnóstico ML", page_icon="🔍", layout="wide")

st.markdown("""
<style>
.metric-card {
    background: #1e1e2e;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 8px;
}
.alerta-critico {
    border-left: 4px solid #e52b2b;
    background: #2d1b1b;
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 8px;
}
.alerta-atencao {
    border-left: 4px solid #f5a623;
    background: #2d2418;
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 8px;
}
.alerta-info {
    border-left: 4px solid #3b82f6;
    background: #1b2035;
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

st.title("🔍 Diagnóstico de Performance — Mercado Livre")
st.caption("Análise completa da sua conta: reputação, operação, estoque, atendimento e publicidade.")

auth_url = (
    f"https://auth.mercadolivre.com.br/authorization"
    f"?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
)

with st.expander("🔗 Como conectar sua conta", expanded=True):
    st.markdown(f"**Passo 1:** [👉 Clique aqui para autorizar sua conta do ML]({auth_url})")
    st.caption("Você será redirecionado para o httpbin.org. Copie o código que aparece depois de `code=` na URL.")
    code = st.text_input("**Passo 2:** Cole o código TG-XXXXXXX aqui:", placeholder="TG-...")

if code:
    with st.spinner("🔄 Analisando sua conta completa... aguarde alguns segundos."):
        token_data = get_access_token(code)
        access_token = token_data.get("access_token")
        user_id = str(token_data.get("user_id"))

        if not access_token:
            st.error("❌ Código inválido ou expirado. Gere um novo código no Passo 1.")
            st.stop()

        r = diagnostico_completo(access_token, user_id)

    # ---- HEADER ----
    st.markdown("---")
    cor = "#00a650" if r["status"] == "SAUDAVEL" else "#f5a623" if r["status"] == "ATENCAO" else "#e52b2b"
    emoji_status = "🟢" if r["status"] == "SAUDAVEL" else "🟡" if r["status"] == "ATENCAO" else "🔴"

    col_h1, col_h2, col_h3 = st.columns([3, 1, 1])
    with col_h1:
        st.markdown(f"## Olá, **{r['seller']}** 👋")
        st.caption(f"Diagnóstico gerado em {r['gerado_em']}")
        nivel_labels = {
            "5_green": "🟢 Verde", "4_light_green": "🟢 Verde claro",
            "3_yellow": "🟡 Amarelo", "2_orange": "🟠 Laranja", "1_red": "🔴 Vermelho"
        }
        st.markdown(f"**Reputação:** {nivel_labels.get(r['nivel'], r['nivel'])} &nbsp;|&nbsp; **MercadoLíder:** {r['mercadolider'].title() if r['mercadolider'] else 'Não'}")
    with col_h2:
        st.markdown(f"""
        <div style='text-align:center; background:{cor}22; border:2px solid {cor}; border-radius:12px; padding:14px;'>
            <div style='font-size:48px; font-weight:900; color:{cor};'>{r["score_total"]}</div>
            <div style='font-size:11px; color:{cor};'>Score Geral /100</div>
        </div>""", unsafe_allow_html=True)
    with col_h3:
        criticos = len([a for a in r["alertas"] if a["tipo"] == "CRITICO"])
        atencoes = len([a for a in r["alertas"] if a["tipo"] == "ATENCAO"])
        st.markdown(f"""
        <div style='text-align:center; border:1px solid #444; border-radius:12px; padding:14px;'>
            <div style='font-size:32px; font-weight:700; color:#e52b2b;'>{criticos}</div>
            <div style='font-size:11px; color:#aaa;'>Críticos</div>
            <div style='font-size:24px; font-weight:700; color:#f5a623; margin-top:6px;'>{atencoes}</div>
            <div style='font-size:11px; color:#aaa;'>Atenções</div>
        </div>""", unsafe_allow_html=True)

    # ---- RESUMO EXECUTIVO ----
    st.markdown("---")
    st.markdown("### 🎯 Problemas críticos — ação imediata")
    criticos_lista = [a for a in r["alertas"] if a["tipo"] == "CRITICO"]
    if criticos_lista:
        for i, alerta in enumerate(criticos_lista, 1):
            st.error(f"**{i}. [{alerta['categoria']}]** {alerta['mensagem']}\n\n→ **{alerta['acao']}**\n\n📌 *{alerta['referencia']}*")
    else:
        st.success("✅ Nenhum problema crítico. Sua operação está saudável!")

    # ---- GAUGES ----
    st.markdown("---")
    st.markdown("### 📊 Score por categoria")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.plotly_chart(gauge(r["scores"]["reputacao"], "Reputação"), use_container_width=True)
    c2.plotly_chart(gauge(r["scores"]["operacao"], "Operação"), use_container_width=True)
    c3.plotly_chart(gauge(r["scores"]["estoque"], "Estoque"), use_container_width=True)
    c4.plotly_chart(gauge(r["scores"]["atendimento"], "Atendimento"), use_container_width=True)
    c5.plotly_chart(gauge(r["scores"]["publicidade"], "Publicidade"), use_container_width=True)

    # ---- MÉTRICAS DETALHADAS ----
    st.markdown("---")
    st.markdown("### 📈 Métricas detalhadas")

    tab1, tab2, tab3, tab4 = st.tabs(["Reputação & Operação", "Estoque & SKUs", "Atendimento", "Todos os alertas"])

    with tab1:
        col_r, col_o = st.columns(2)
        with col_r:
            st.markdown("**Reputação**")
            m = r["metricas"].get("reputacao", {})
            st.metric("Avaliações positivas", m.get("positivas", "-"))
            st.metric("Avaliações negativas", m.get("negativas", "-"))
            st.metric("Total de vendas", m.get("total_vendas", "-"))
            st.metric("Vendas canceladas", m.get("canceladas", "-"))
        with col_o:
            st.markdown("**Operação** *(últimos 60 dias)*")
            m = r["metricas"].get("operacao", {})
            st.metric("Atraso no envio", m.get("atraso", "-"), delta="Meta: < 15%", delta_color="off")
            st.metric("Cancelamentos", m.get("cancelamento", "-"), delta="Meta: < 2%", delta_color="off")
            st.metric("Reclamações", m.get("reclamacao", "-"), delta="Meta: < 3%", delta_color="off")
            st.metric("Vendas no período", m.get("vendas_60d", "-"))

    with tab2:
        m = r["metricas"].get("estoque", {})
        col_e1, col_e2, col_e3, col_e4 = st.columns(4)
        col_e1.metric("Total de itens", m.get("total_itens", 0))
        col_e2.metric("Itens ativos", m.get("itens_ativos", 0))
        col_e3.metric("Em ruptura", m.get("itens_ruptura", 0))
        col_e4.metric("Estoque crítico", m.get("itens_estoque_baixo", 0))

        st.markdown("**Ranking de SKUs**")
        if r["skus"]:
            df = pd.DataFrame(r["skus"])
            st.dataframe(
                df, use_container_width=True, hide_index=True,
                column_config={
                    "Produto": st.column_config.TextColumn("Produto", width="large"),
                    "Preço": st.column_config.TextColumn("Preço", width="small"),
                    "Estoque": st.column_config.NumberColumn("Estoque", width="small"),
                    "Vendas": st.column_config.NumberColumn("Vendas", width="small"),
                    "Status": st.column_config.TextColumn("Status", width="small"),
                    "Logística": st.column_config.TextColumn("Logística", width="small"),
                    "Situação": st.column_config.TextColumn("Situação", width="large"),
                }
            )

    with tab3:
        m = r["metricas"].get("atendimento", {})
        st.metric("Perguntas sem resposta", m.get("perguntas_sem_resposta", 0))
        st.caption("Tempo ideal de resposta: menos de 1 hora. Perguntas sem resposta reduzem conversão e posicionamento.")

    with tab4:
        for alerta in r["alertas"]:
            if alerta["tipo"] == "CRITICO":
                st.error(f"🔴 **[{alerta['categoria']}]** {alerta['mensagem']}\n\n→ {alerta['acao']}\n\n📌 *{alerta['referencia']}*")
            elif alerta["tipo"] == "ATENCAO":
                st.warning(f"🟡 **[{alerta['categoria']}]** {alerta['mensagem']}\n\n→ {alerta['acao']}\n\n📌 *{alerta['referencia']}*")
            else:
                st.info(f"ℹ️ **[{alerta['categoria']}]** {alerta['mensagem']}\n\n→ {alerta['acao']}\n\n📌 *{alerta['referencia']}*")
