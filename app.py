import streamlit as st
import requests
from datetime import datetime

CLIENT_ID = "8361153242610469"
CLIENT_SECRET = st.secrets["CLIENT_SECRET"]
REDIRECT_URI = "https://httpbin.org/get"

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
        "seller": "", "score": 100, "status": "",
        "alertas": [], "gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M")
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
