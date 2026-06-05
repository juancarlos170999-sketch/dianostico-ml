import streamlit as st
import requests
from datetime import datetime

CLIENT_ID = "8361153242610469"
CLIENT_SECRET = "3o8z0V9ogn90pA3Gr6hCLUdJC1TYi1Pd"
REDIRECT_URI = "https://dianostico-ml-lldf9fyphmfxxhserhiw6q.streamlit.app"

def get_access_token(code):
    response = requests.post(
        "https://api.mercadolibre.com/oauth/token",
        data={
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
            "redirect_uri": REDIRECT_URI
        }
    )
    return response.json()

def diagnostico_completo(access_token, user_id):
    headers = {"Authorization": f"Bearer {access_token}"}
    resultado = {
        "seller": "",
        "score": 100,
        "status": "",
        "alertas": [],
        "gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M")
    }

    r = requests.get(f"https://api.mercadolibre.com/users/{user_id}", headers=headers)
    dados = r.json()
    resultado["seller"] = dados.get("nickname", "")
    reputacao = dados.get("seller_reputation", {})
    nivel = reputacao.get("level_id")

    if nivel == "1_red":
        resultado["score"] -= 40
        resultado["alertas"].append({"tipo": "CRITICO", "categoria": "Reputação", "mensagem": "Reputação vermelha. Visibilidade severamente comprometida.", "acao": "Resolver todas as reclamações abertas imediatamente."})
    elif nivel == "2_orange":
        resultado["score"] -= 30
        resultado["alertas"].append({"tipo": "CRITICO", "categoria": "Reputação", "mensagem": "Reputação laranja. Risco alto de perda de posicionamento.", "acao": "Reduzir cancelamentos e atrasos nos próximos 30 dias."})
    elif nivel == "3_yellow":
        resultado["score"] -= 15
        resultado["alertas"].append({"tipo": "ATENCAO", "categoria": "Reputação", "mensagem": "Reputação amarela. Abaixo do ideal para competir.", "acao": "Melhorar prazo de envio e reduzir atrasos abaixo de 10%."})

    taxa_atraso = reputacao.get("metrics", {}).get("delayed_handling_time", {}).get("rate", 0)
    if taxa_atraso > 0.10:
        resultado["score"] -= 15
        resultado["alertas"].append({"tipo": "ATENCAO", "categoria": "Operação", "mensagem": f"Taxa de atraso no envio: {round(taxa_atraso*100,1)}%. Limite para verde: 10%.", "acao": "Revisar prazo de handling nos anúncios."})

    r_itens = requests.get(f"https://api.mercadolibre.com/users/{user_id}/items/search", headers=headers)
    item_ids = r_itens.json().get("results", [])
    for item_id in item_ids:
        r_item = requests.get(f"https://api.mercadolibre.com/items/{item_id}", headers=headers)
        item = r_item.json()
        titulo = item.get("title", "")
        estoque = item.get("available_quantity", 0)
        status = item.get("status", "")
        vendas = item.get("sold_quantity", 0)
        preco = item.get("price", 0)
        if estoque == 0 and status == "closed" and vendas > 0:
            resultado["score"] -= 20
            resultado["alertas"].append({"tipo": "CRITICO", "categoria": "Estoque", "mensagem": f"'{titulo}' fechado com {vendas} vendas anteriores. Receita parada.", "acao": f"Repor estoque e reativar anúncio. Potencial: R${preco} por venda."})
        elif estoque == 0 and status == "active":
            resultado["score"] -= 25
            resultado["alertas"].append({"tipo": "CRITICO", "categoria": "Estoque", "mensagem": f"'{titulo}' ativo com estoque ZERADO.", "acao": "Repor estoque imediatamente ou pausar o anúncio."})

    r_adv = requests.get("https://api.mercadolibre.com/advertising/advertisers?product_id=PADS", headers={**headers, "Api-Version": "1"})
    if r_adv.status_code == 200:
        advertisers = r_adv.json().get("advertisers", [])
        if advertisers:
            advertiser_id = advertisers[0].get("advertiser_id")
            r_camp = requests.get(f"https://api.mercadolibre.com/advertising/advertisers/{advertiser_id}/product_ads/campaigns/search?date_from=2025-01-01&date_to=2025-12-31&metrics=clicks,cost,acos", headers={**headers, "Api-Version": "2"})
            if r_camp.status_code == 200:
                for c in r_camp.json().get("campaigns", []):
                    acos = c.get("metrics", {}).get("acos", 0)
                    nome = c.get("name", "")
                    if acos and acos > 0.20:
                        resultado["score"] -= 15
                        resultado["alertas"].append({"tipo": "CRITICO", "categoria": "Publicidade", "mensagem": f"Campanha '{nome}' com ACOS de {round(acos*100,1)}%.", "acao": "Revisar lances ou pausar itens sem conversão."})
    else:
        resultado["alertas"].append({"tipo": "INFO", "categoria": "Publicidade", "mensagem": "Conta sem Product Ads ativo.", "acao": "Considere ativar Product Ads para aumentar visibilidade."})

    resultado["score"] = max(0, resultado["score"])
    resultado["status"] = "SAUDAVEL" if resultado["score"] >= 80 else "ATENCAO" if resultado["score"] >= 60 else "CRITICO"
    return resultado

# INTERFACE
st.set_page_config(page_title="Diagnóstico ML", page_icon="🔍", layout="centered")
st.title("🔍 Diagnóstico de Performance")
st.markdown("Conecte sua conta do Mercado Livre e receba um diagnóstico completo da sua operação.")

params = st.query_params
code = params.get("code")

if not code:
    auth_url = f"https://auth.mercadolivre.com.br/authorization?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
    st.markdown(f"""
    <div style='text-align:center; padding: 40px;'>
        <a href='{auth_url}' target='_self'>
            <button style='background:#FFE600; color:#333; border:none; padding:16px 32px; font-size:18px; border-radius:8px; cursor:pointer; font-weight:bold;'>
                🔗 Conectar conta do Mercado Livre
            </button>
        </a>
    </div>
    """, unsafe_allow_html=True)
else:
    with st.spinner("Gerando diagnóstico da sua conta..."):
        token_data = get_access_token(code)
        access_token = token_data.get("access_token")
        user_id = str(token_data.get("user_id"))

        if not access_token:
            st.error("Erro ao conectar. Tente novamente.")
            st.stop()

        resultado = diagnostico_completo(access_token, user_id)

        cor_emoji = "🟢" if resultado["status"] == "SAUDAVEL" else "🟡" if resultado["status"] == "ATENCAO" else "🔴"

        st.markdown(f"### Olá, {resultado['seller']} 👋")
        st.markdown(f"**Diagnóstico gerado em:** {resultado['gerado_em']}")

        col1, col2 = st.columns(2)
        col1.metric("Score Geral", f"{resultado['score']}/100")
        col2.metric("Status", f"{cor_emoji} {resultado['status']}")

        st.divider()
        st.markdown(f"### {len(resultado['alertas'])} alertas encontrados")

        for alerta in resultado["alertas"]:
            if alerta["tipo"] == "CRITICO":
                st.error(f"**🔴 [{alerta['categoria']}]** {alerta['mensagem']}\n\n→ {alerta['acao']}")
            elif alerta["tipo"] == "ATENCAO":
                st.warning(f"**🟡 [{alerta['categoria']}]** {alerta['mensagem']}\n\n→ {alerta['acao']}")
            else:
                st.info(f"**ℹ️ [{alerta['categoria']}]** {alerta['mensagem']}\n\n→ {alerta['acao']}")
