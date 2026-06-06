import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import hashlib
from supabase import create_client

CLIENT_ID = "8361153242610469"
CLIENT_SECRET = st.secrets["CLIENT_SECRET"]
REDIRECT_URI = "https://httpbingo.org/get"
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="RaioxSeller", page_icon="🔍", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;900&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; background: #0a0a12 !important; color: #e2e2f0 !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }
section[data-testid="stSidebar"] { background: #0f0f1a !important; border-right: 1px solid #1e1e2e !important; }
section[data-testid="stSidebar"] [data-testid="stRadio"] label { padding: 9px 16px !important; border-left: 2px solid transparent !important; font-size: 13px !important; }
section[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) { background: #0d2d1a !important; border-left: 2px solid #00a650 !important; color: #00a650 !important; }
section[data-testid="stSidebar"] [data-testid="stRadio"] input { display: none !important; }
section[data-testid="stSidebar"] [data-testid="stExpander"] { background: #13131f !important; border: 1px solid #1e1e2e !important; border-radius: 8px !important; }
#MainMenu, footer, header { visibility: hidden; }
div.stButton > button { background: #00a650 !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; font-size: 13px !important; }
div.stButton > button:hover { background: #008a42 !important; }
div.stTextInput > div > div > input { background: #1a1a2e !important; border: 1px solid #1e1e2e !important; border-radius: 8px !important; color: #e2e2f0 !important; }
div.stSelectbox > div > div { background: #1a1a2e !important; border: 1px solid #1e1e2e !important; color: #e2e2f0 !important; }
div.stNumberInput > div > div > input { background: #1a1a2e !important; border: 1px solid #1e1e2e !important; color: #e2e2f0 !important; }
div.stTabs [data-baseweb="tab-list"] { background: transparent !important; border-bottom: 1px solid #1e1e2e !important; gap: 0 !important; }
div.stTabs [data-baseweb="tab"] { background: transparent !important; color: #6b6b8a !important; font-size: 12px !important; padding: 8px 16px !important; }
div.stTabs [aria-selected="true"] { color: #00a650 !important; border-bottom: 2px solid #00a650 !important; font-weight: 600 !important; }
div.stMetric { background: #13131f; border: 1px solid #1e1e2e; border-radius: 10px; padding: 12px 16px; }
div.stMetric label { color: #6b6b8a !important; font-size: 11px !important; }
div.stMetric [data-testid="stMetricValue"] { color: #e2e2f0 !important; font-size: 22px !important; font-weight: 700 !important; }
div.stDataFrame { border: 1px solid #1e1e2e !important; border-radius: 10px !important; overflow: hidden !important; }
div.stExpander { background: #13131f !important; border: 1px solid #1e1e2e !important; border-radius: 10px !important; }
</style>
""", unsafe_allow_html=True)

def hash_senha(s): return hashlib.sha256(s.encode()).hexdigest()
def cor_score(s): return "#e52b2b" if s < 60 else "#f5a623" if s < 80 else "#00a650"

def get_access_token(code):
    r = requests.post("https://api.mercadolibre.com/oauth/token", data={
        "grant_type": "authorization_code", "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET, "code": code, "redirect_uri": REDIRECT_URI
    })
    return r.json()

def gauge(score, titulo):
    cor = "#00a650" if score >= 80 else "#f5a623" if score >= 60 else "#e52b2b"
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score,
        title={"text": titulo, "font": {"size": 11, "color": "#6b6b8a"}},
        number={"font": {"size": 26, "color": cor}},
        gauge={"axis": {"range": [0, 100]}, "bar": {"color": cor, "thickness": 0.25},
               "bgcolor": "#13131f",
               "steps": [{"range": [0,60], "color": "#2d1b1b"}, {"range": [60,80], "color": "#2d2418"}, {"range": [80,100], "color": "#0d2d1a"}]}
    ))
    fig.update_layout(height=160, margin=dict(t=40,b=0,l=10,r=10), paper_bgcolor="#13131f", plot_bgcolor="#13131f")
    return fig

def salvar_diagnostico(usuario_id, conta_ml_id, nickname, resultado):
    try:
        supabase.table("diagnosticos").insert({
            "usuario_id": usuario_id, "conta_ml_id": conta_ml_id, "ml_nickname": nickname,
            "score_total": resultado["score_total"], "score_reputacao": resultado["scores"]["reputacao"],
            "score_operacao": resultado["scores"]["operacao"], "score_estoque": resultado["scores"]["estoque"],
            "score_atendimento": resultado["scores"]["atendimento"], "score_publicidade": resultado["scores"]["publicidade"],
            "status": resultado["status"], "alertas": resultado["alertas"], "metricas": resultado["metricas"]
        }).execute()
    except: pass

def buscar_historico(usuario_id, conta_ml_id):
    try:
        r = supabase.table("diagnosticos").select("score_total,criado_em").eq("usuario_id", usuario_id).eq("conta_ml_id", conta_ml_id).order("criado_em", desc=True).limit(6).execute()
        return r.data
    except: return []

def diagnostico_conta(access_token, user_id):
    H = {"Authorization": f"Bearer {access_token}"}
    resultado = {"seller": "", "nivel": "", "mercadolider": "", "score_total": 100,
        "scores": {"reputacao":100,"operacao":100,"estoque":100,"publicidade":100,"atendimento":100},
        "status": "", "alertas": [], "skus": [], "metricas": {}, "gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M")}

    r = requests.get(f"https://api.mercadolibre.com/users/{user_id}", headers=H)
    dados = r.json()
    resultado["seller"] = dados.get("nickname","")
    rep = dados.get("seller_reputation",{})
    metricas = rep.get("metrics",{})
    transacoes = rep.get("transactions",{})
    nivel = rep.get("level_id","")
    resultado["nivel"] = nivel
    resultado["mercadolider"] = rep.get("power_seller_status") or "Não é MercadoLíder"
    nivel_scores = {"5_green":100,"4_light_green":75,"3_yellow":55,"2_orange":30,"1_red":10}
    resultado["scores"]["reputacao"] = nivel_scores.get(nivel, 50)

    if nivel in ["1_red","2_orange"]:
        resultado["alertas"].append({"tipo":"CRITICO","categoria":"Reputação","mensagem":f"Reputação {nivel.split('_')[1].upper()}. Visibilidade e Buy Box comprometidos.","acao":"Resolver reclamações e cancelamentos imediatamente.","referencia":"Meta: ≤2% reclamações, ≤1% cancelamentos, ≥90% no prazo"})
    elif nivel == "3_yellow":
        resultado["alertas"].append({"tipo":"ATENCAO","categoria":"Reputação","mensagem":"Reputação AMARELA. Perda de posicionamento e Buy Box.","acao":"Reduzir atrasos e cancelamentos abaixo de 1%.","referencia":"Meta: ≤2% reclamações, ≤1% cancelamentos, ≥90% no prazo"})

    ratings = transacoes.get("ratings",{})
    positivas = ratings.get("positive",0)
    taxa_atraso = metricas.get("delayed_handling_time",{}).get("rate",0)
    taxa_cancelamento = metricas.get("cancellations",{}).get("rate",0)
    taxa_reclamacao = metricas.get("claims",{}).get("rate",0)
    vendas_60d = metricas.get("sales",{}).get("completed",0)

    score_op = 100
    if taxa_atraso > 0.10:
        score_op -= 40
        resultado["alertas"].append({"tipo":"CRITICO","categoria":"Operação","mensagem":f"Atraso no envio: {round(taxa_atraso*100,1)}%. Meta: ≥90% no prazo.","acao":"Aumente prazo de handling para 2 dias. Considere Full nos top SKUs.","referencia":"Meta ML Brasil: ≥90% de envios dentro do prazo"})
    elif taxa_atraso > 0.05:
        score_op -= 20
        resultado["alertas"].append({"tipo":"ATENCAO","categoria":"Operação","mensagem":f"Atraso no envio: {round(taxa_atraso*100,1)}%. Próximo do limite.","acao":"Ajuste prazo de handling nos anúncios.","referencia":"Meta ML Brasil: ≥90% de envios dentro do prazo"})
    if taxa_cancelamento > 0.01:
        score_op -= 35
        resultado["alertas"].append({"tipo":"CRITICO","categoria":"Operação","mensagem":f"Cancelamentos: {round(taxa_cancelamento*100,1)}%. Acima de 1%.","acao":"Investigue causa: estoque desatualizado ou problema logístico.","referencia":"Meta ML Brasil: ≤1% de cancelamentos"})
    if taxa_reclamacao > 0.02:
        score_op -= 40
        resultado["alertas"].append({"tipo":"CRITICO","categoria":"Operação","mensagem":f"Reclamações: {round(taxa_reclamacao*100,1)}%. Acima de 2%.","acao":"Responda todas as reclamações em até 48h.","referencia":"Meta ML Brasil: ≤2% de reclamações"})
    resultado["scores"]["operacao"] = max(0, score_op)
    resultado["metricas"]["operacao"] = {"atraso":f"{round(taxa_atraso*100,1)}%","cancelamento":f"{round(taxa_cancelamento*100,1)}%","reclamacao":f"{round(taxa_reclamacao*100,1)}%","vendas_60d":vendas_60d}
    resultado["metricas"]["reputacao"] = {"nivel":nivel,"positivas":f"{round(positivas*100,1)}%","total_vendas":transacoes.get("total",0)}

    r_perguntas = requests.get(f"https://api.mercadolibre.com/questions/search?seller_id={user_id}&status=UNANSWERED", headers=H)
    perguntas = r_perguntas.json().get("total",0) if r_perguntas.status_code == 200 else 0
    score_atend = 100
    if perguntas > 10:
        score_atend -= 40
        resultado["alertas"].append({"tipo":"CRITICO","categoria":"Atendimento","mensagem":f"{perguntas} perguntas sem resposta.","acao":"Responda todas. Ideal: menos de 1 hora.","referencia":"Perguntas sem resposta reduzem conversão e posicionamento"})
    elif perguntas > 3:
        score_atend -= 20
        resultado["alertas"].append({"tipo":"ATENCAO","categoria":"Atendimento","mensagem":f"{perguntas} perguntas sem resposta.","acao":"Crie rotina de resposta diária. Ideal: menos de 1 hora.","referencia":"ML considera bom: resposta em até 1 hora"})
    resultado["scores"]["atendimento"] = max(0, score_atend)
    resultado["metricas"]["atendimento"] = {"perguntas_sem_resposta":perguntas}

    r_itens = requests.get(f"https://api.mercadolibre.com/users/{user_id}/items/search", headers=H)
    item_ids = r_itens.json().get("results",[])
    score_estoque = 100
    total_itens = len(item_ids)
    itens_ativos = itens_ruptura = itens_baixo = sem_full = 0

    for item_id in item_ids:
        r_item = requests.get(f"https://api.mercadolibre.com/items/{item_id}", headers=H)
        item = r_item.json()
        titulo = item.get("title","")
        tc = titulo[:45]+"..." if len(titulo)>45 else titulo
        estoque = item.get("available_quantity",0)
        status = item.get("status","")
        vendas = item.get("sold_quantity",0)
        preco = item.get("price",0)
        logistica = item.get("shipping",{}).get("logistic_type","")
        problemas = []
        if status == "active":
            itens_ativos += 1
            if logistica not in ["fulfillment","xd_drop_off"]: sem_full += 1
        if estoque == 0 and status == "active":
            itens_ruptura += 1; score_estoque -= 25
            problemas.append("🔴 Ruptura com anúncio ativo")
            resultado["alertas"].append({"tipo":"CRITICO","categoria":"Estoque","mensagem":f"'{tc}' ATIVO com estoque ZERO.","acao":"Pause o anúncio imediatamente ou reponha estoque.","referencia":"Anúncio ativo sem estoque queima budget de ads"})
        elif estoque == 0 and status == "closed" and vendas > 0:
            score_estoque -= 10; problemas.append(f"🟡 Fechado — {vendas} vendas")
            resultado["alertas"].append({"tipo":"ATENCAO","categoria":"Estoque","mensagem":f"'{tc}' fechado com {vendas} vendas anteriores.","acao":f"Repor estoque e reativar. Potencial: R${preco}/venda.","referencia":"Produto com histórico tem mais chance de conversão"})
        elif 0 < estoque <= 5 and status == "active":
            itens_baixo += 1; problemas.append(f"🟡 Estoque crítico: {estoque} un.")
            resultado["alertas"].append({"tipo":"ATENCAO","categoria":"Estoque","mensagem":f"'{tc}' com apenas {estoque} unidades.","acao":"Repor estoque antes de atingir zero.","referencia":"Ruptura frequente pode levar à desativação automática"})
        if logistica not in ["fulfillment","xd_drop_off"] and status == "active": problemas.append("⚠️ Sem Full/Flex")
        resultado["skus"].append({"Produto":tc,"Preço":f"R${preco}","Estoque":estoque,"Vendas":vendas,
            "Status":"✅ Ativo" if status=="active" else "⛔ Fechado",
            "Logística":"Full" if logistica=="fulfillment" else "Flex" if logistica=="xd_drop_off" else "Padrão",
            "Situação":" | ".join(problemas) if problemas else "✅ OK"})

    resultado["scores"]["estoque"] = max(0, score_estoque)
    resultado["metricas"]["estoque"] = {"total_itens":total_itens,"itens_ativos":itens_ativos,"itens_ruptura":itens_ruptura,"itens_estoque_baixo":itens_baixo,"sem_full":sem_full}
    if sem_full > 0:
        resultado["alertas"].append({"tipo":"ATENCAO","categoria":"Logística","mensagem":f"{sem_full} itens ativos sem Full ou Flex.","acao":"Ative Full nos top SKUs para triplicar chances de venda.","referencia":"Full = 3x mais chances de venda + prioridade no algoritmo"})

    r_adv = requests.get("https://api.mercadolibre.com/advertising/advertisers?product_id=PADS", headers={**H,"Api-Version":"1"})
    score_ads = 100
    if r_adv.status_code == 200:
        advertisers = r_adv.json().get("advertisers",[])
        if advertisers:
            adv_id = advertisers[0].get("advertiser_id")
            hoje = datetime.now()
            r_camp = requests.get(f"https://api.mercadolibre.com/advertising/advertisers/{adv_id}/product_ads/campaigns/search?date_from={hoje.year}-01-01&date_to={hoje.strftime('%Y-%m-%d')}&metrics=clicks,cost,roas", headers={**H,"Api-Version":"2"})
            if r_camp.status_code == 200:
                for c in r_camp.json().get("campaigns",[]):
                    roas = c.get("metrics",{}).get("roas",0) or 0
                    nome = c.get("name","Campanha")
                    if roas and roas < 3:
                        score_ads -= 20
                        resultado["alertas"].append({"tipo":"CRITICO","categoria":"Publicidade","mensagem":f"Campanha '{nome}': ROAS {round(roas,1)}x — abaixo do mínimo.","acao":"Pause itens sem conversão. ROAS mínimo = 100 / margem%.","referencia":"Desde out/2025 o ML usa ROAS como métrica principal"})
    else:
        score_ads = 50
        resultado["alertas"].append({"tipo":"INFO","categoria":"Publicidade","mensagem":"Conta sem Product Ads ativo.","acao":"Ative Product Ads nos SKUs com histórico e estoque ok.","referencia":"Sellers com ads têm prioridade no posicionamento"})
    resultado["scores"]["publicidade"] = max(0, score_ads)

    pesos = {"reputacao":0.30,"operacao":0.25,"estoque":0.20,"atendimento":0.15,"publicidade":0.10}
    resultado["score_total"] = int(sum(resultado["scores"][k]*v for k,v in pesos.items()))
    resultado["status"] = "SAUDAVEL" if resultado["score_total"]>=80 else "ATENCAO" if resultado["score_total"]>=60 else "CRITICO"
    resultado["alertas"].sort(key=lambda x: {"CRITICO":0,"ATENCAO":1,"INFO":2}.get(x["tipo"],3))
    return resultado

def analisar_item(item_id, access_token, user_id):
    H = {"Authorization": f"Bearer {access_token}"}
    r = requests.get(f"https://api.mercadolibre.com/items/{item_id}", headers=H)
    if r.status_code != 200: return None
    item = r.json()
    titulo = item.get("title",""); preco = item.get("price",0)
    estoque = item.get("available_quantity",0); status = item.get("status","")
    vendas = item.get("sold_quantity",0); fotos = item.get("pictures",[])
    atributos = item.get("attributes",[]); logistica = item.get("shipping",{}).get("logistic_type","")
    tipo_anuncio = item.get("listing_type_id","")
    r_desc = requests.get(f"https://api.mercadolibre.com/items/{item_id}/description", headers=H)
    descricao = r_desc.json().get("plain_text","") if r_desc.status_code==200 else ""
    scores = {}; acoes = {}; refs = {}

    chars = len(titulo)
    scores["titulo"] = 90 if chars>=55 else 60 if chars>=40 else 20
    acoes["titulo"] = f"Bom — {chars}/60 caracteres." if chars>=55 else f"{chars}/60 — use: Produto + Marca + Modelo + Características principais."
    refs["titulo"] = "Regra ML: Produto + Marca + Modelo + Características. Nunca repita palavras — algoritmo ignora repetições."

    n_fotos = len(fotos)
    scores["fotos"] = 90 if n_fotos>=6 else 55 if n_fotos>=4 else 25 if n_fotos>=2 else 0
    acoes["fotos"] = f"{n_fotos} fotos — bom." if n_fotos>=6 else f"{n_fotos}/6 fotos. Adicione {6-n_fotos} fotos: ângulos, detalhe, escala, embalagem."
    refs["fotos"] = "ML avalia quantidade, qualidade e variedade. Meta: 6+ fotos 1200x1200px com fundo branco."

    n_attrs = len(atributos)
    tem_gtin = any(a.get("id") in ["GTIN","EAN"] for a in atributos)
    scores["ficha"] = 90 if n_attrs>=10 else 55 if n_attrs>=6 else 25 if n_attrs>=3 else 0
    acoes["ficha"] = f"{n_attrs} atributos. {'✅ GTIN presente.' if tem_gtin else '⚠️ Adicione GTIN/EAN para +40% visibilidade.'}" if n_attrs>=6 else f"Apenas {n_attrs} atributos — crítico. Ficha é o principal fator de SEO do ML."
    refs["ficha"] = "Ficha técnica é mais importante que descrição para SEO. GTIN/EAN aumenta visibilidade em até 40%."

    chars_desc = len(descricao)
    scores["descricao"] = 85 if chars_desc>=500 else 55 if chars_desc>=200 else 25 if chars_desc>0 else 0
    acoes["descricao"] = "Completa." if chars_desc>=500 else "Adicione: o que vem na caixa, compatibilidade e garantia." if chars_desc>0 else "Sem descrição — adicione uma completa."
    refs["descricao"] = "Descrição deve cobrir pontos de objeção, palavras-chave secundárias e prova de qualidade."

    scores["preco"] = 75 if preco>0 else 0
    acoes["preco"] = f"R${preco} — monitore paridade com Amazon e Shopee."
    refs["preco"] = "ML penaliza se encontrar produto mais barato em outro marketplace. Prazo para ajuste: 3 dias."

    r_rep = requests.get(f"https://api.mercadolibre.com/users/{user_id}", headers=H)
    nivel = r_rep.json().get("seller_reputation",{}).get("level_id","") if r_rep.status_code==200 else ""
    scores["reputacao"] = {"5_green":100,"4_light_green":80,"3_yellow":55,"2_orange":30,"1_red":10}.get(nivel,50)
    nivel_nome = {'5_green':'Verde','4_light_green':'Verde claro','3_yellow':'Amarela','2_orange':'Laranja','1_red':'Vermelha'}.get(nivel,'desconhecida')
    acoes["reputacao"] = f"Reputação {nivel_nome} — impacta posicionamento deste anúncio."
    refs["reputacao"] = "Reputação do seller afeta posicionamento individual de cada anúncio. Verde = máxima exposição."
    scores["logistica"] = 100 if logistica=="fulfillment" else 75 if logistica=="xd_drop_off" else 0
    acoes["logistica"] = "Full ativo — 3x mais chances de venda." if logistica=="fulfillment" else "Flex ativo — entrega no mesmo dia." if logistica=="xd_drop_off" else "Envio padrão — ative Full para triplicar chances de venda."
    refs["logistica"] = "Full = 3x mais chances de venda + prioridade nas buscas + entrega hoje/amanhã."

    scores["conversao"] = 100 if vendas>=50 else 80 if vendas>=20 else 55 if vendas>=5 else 30 if vendas>=1 else 0
    acoes["conversao"] = f"{vendas} vendas — {'forte' if vendas>=20 else 'moderado' if vendas>=5 else 'fraco'}." if vendas>=1 else "Sem vendas — aguarde 15-28 dias de histórico orgânico antes de ativar ads."
    refs["conversao"] = "Histórico de conversão é sinal forte do algoritmo. Produto novo precisa de 15-28 dias para otimização."

    pesos = {"titulo":0.15,"fotos":0.20,"ficha":0.20,"descricao":0.10,"preco":0.10,"reputacao":0.10,"logistica":0.10,"conversao":0.05}
    score_total = int(sum(scores[k]*pesos[k] for k in pesos))
    return {"item_id":item_id,"titulo":titulo,"preco":preco,"estoque":estoque,"status":status,"vendas":vendas,
        "fotos":n_fotos,"logistica":logistica,"tipo_anuncio":tipo_anuncio,"score_total":score_total,
        "scores":scores,"acoes":acoes,"refs":refs,"pode_anunciar":estoque>0 and status=="active" and vendas>=1,"n_atributos":n_attrs}

def calcular_preco(cmv, comissao_pct, frete_val, imposto_pct, margem_pct):
    total_var = comissao_pct + imposto_pct + margem_pct/100
    if total_var >= 1: return 0,0,0,0
    preco = (cmv + frete_val) / (1 - total_var)
    com = preco * comissao_pct; imp = preco * imposto_pct
    lucro = preco - cmv - com - frete_val - imp
    return preco, com, imp, lucro

# ============ LOGIN ============
def tela_login():
    col = st.columns([1,1,1])[1]
    with col:
        st.markdown("""
        <div style="background:#13131f;border:1px solid #1e1e2e;border-radius:16px;padding:36px 32px;margin-top:80px;">
            <div style="font-size:26px;font-weight:800;color:#e2e2f0;margin-bottom:4px;">🔍 RaioxSeller</div>
            <div style="font-size:13px;color:#6b6b8a;margin-bottom:28px;">Diagnóstico de performance para sellers ML</div>
        </div>
        """, unsafe_allow_html=True)
        aba = st.radio("", ["Entrar","Criar conta"], horizontal=True, label_visibility="collapsed")
        email = st.text_input("Email", placeholder="seu@email.com")
        senha = st.text_input("Senha", type="password", placeholder="••••••••")
        if aba == "Criar conta":
            nome = st.text_input("Nome", placeholder="Seu nome")
            plano = st.selectbox("Plano", ["starter","pro","agencia"], format_func=lambda x: {"starter":"Starter — R$97/mês","pro":"Pro — R$197/mês","agencia":"Agência — R$397/mês"}[x])
            if st.button("Criar conta", use_container_width=True):
                if not email or not senha: st.error("Preencha email e senha."); return
                try:
                    existe = supabase.table("usuarios").select("id").eq("email",email).execute()
                    if existe.data: st.error("Email já cadastrado."); return
                    supabase.table("usuarios").insert({"email":email,"senha_hash":hash_senha(senha),"nome":nome,"plano":plano}).execute()
                    st.success("Conta criada! Faça login.")
                except Exception as e: st.error(f"Erro: {e}")
        else:
            if st.button("Entrar", use_container_width=True):
                if not email or not senha: st.error("Preencha email e senha."); return
                try:
                    r = supabase.table("usuarios").select("*").eq("email",email).eq("senha_hash",hash_senha(senha)).execute()
                    if not r.data: st.error("Email ou senha incorretos."); return
                    st.session_state["usuario"] = r.data[0]; st.rerun()
                except Exception as e: st.error(f"Erro: {e}")

# ============ SIDEBAR ============
def render_sidebar(usuario):
    with st.sidebar:
        st.markdown(f"""
        <div style="padding:20px 16px 12px;border-bottom:1px solid #1e1e2e;margin-bottom:8px;">
            <div style="font-size:15px;font-weight:700;color:#e2e2f0;">🔍 RaioxSeller</div>
            <div style="font-size:11px;color:#6b6b8a;">Diagnóstico ML</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div style="font-size:10px;color:#444;letter-spacing:0.08em;padding:8px 16px 4px;text-transform:uppercase;">Análise</div>', unsafe_allow_html=True)
        pagina = st.radio("", ["🏠 Visão geral","📦 Analisar produto","🧮 Calculadora","📋 Plano de ação"], label_visibility="collapsed")
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
                        token = td["access_token"]; ml_uid = str(td["user_id"])
                        r_user = requests.get(f"https://api.mercadolibre.com/users/{ml_uid}", headers={"Authorization":f"Bearer {token}"})
                        nickname = r_user.json().get("nickname", ml_uid)
                        try:
                            existe = supabase.table("contas_ml").select("id").eq("usuario_id",usuario["id"]).eq("ml_user_id",ml_uid).execute()
                            if existe.data:
                                conta_id = existe.data[0]["id"]
                                supabase.table("contas_ml").update({"access_token":token,"ml_nickname":nickname}).eq("id",conta_id).execute()
                            else:
                                rc = supabase.table("contas_ml").insert({"usuario_id":usuario["id"],"ml_user_id":ml_uid,"ml_nickname":nickname,"access_token":token}).execute()
                                conta_id = rc.data[0]["id"]
                        except: conta_id = None
                        st.session_state["access_token"] = token
                        st.session_state["user_id"] = ml_uid
                        st.session_state["conta_ml_id"] = conta_id
                        st.success(f"✅ {nickname} conectado!"); st.rerun()
                    else: st.error("Código inválido.")
        if "access_token" in st.session_state:
            st.markdown('<div style="background:#0d2d1a;border:1px solid #00a650;border-radius:8px;padding:10px 12px;font-size:12px;color:#9FE1CB;">✅ Conta ML conectada</div>', unsafe_allow_html=True)
        st.markdown("---")
        plano_cores = {"starter":"#3b82f6","pro":"#f5a623","agencia":"#00a650"}
        plano = usuario.get("plano","starter")
        st.markdown(f"""
        <div style="padding:8px 0;font-size:11px;color:#6b6b8a;">
            <div style="color:#e2e2f0;font-weight:600;margin-bottom:4px;">{usuario.get('nome') or usuario.get('email')}</div>
            <span style="background:{plano_cores.get(plano,'#444')};color:#fff;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:600;">{plano.upper()}</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Sair", use_container_width=True):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()
    return pagina

# ============ VISÃO GERAL ============
def pagina_visao_geral(usuario):
    if "access_token" not in st.session_state:
        st.markdown('<div style="display:flex;align-items:center;justify-content:center;height:70vh;flex-direction:column;gap:12px;"><div style="font-size:40px;">🔗</div><div style="font-size:16px;font-weight:600;color:#e2e2f0;">Conecte sua conta do ML</div><div style="font-size:13px;color:#6b6b8a;">Use o painel lateral para autorizar sua conta.</div></div>', unsafe_allow_html=True)
        return

    ACCESS = st.session_state["access_token"]; UID = st.session_state["user_id"]
    conta_ml_id = st.session_state.get("conta_ml_id")
    _, col_b = st.columns([9,1])
    with col_b:
        if st.button("🔄"):
            if "diagnostico" in st.session_state: del st.session_state["diagnostico"]
            st.rerun()

    if "diagnostico" not in st.session_state:
        with st.spinner("Analisando sua conta..."):
            r = diagnostico_conta(ACCESS, UID)
            st.session_state["diagnostico"] = r
            if conta_ml_id: salvar_diagnostico(usuario["id"], conta_ml_id, r["seller"], r)
    else:
        r = st.session_state["diagnostico"]

    cor = "#00a650" if r["status"]=="SAUDAVEL" else "#f5a623" if r["status"]=="ATENCAO" else "#e52b2b"
    nivel_labels = {"5_green":"🟢 Verde","4_light_green":"🟢 Verde claro","3_yellow":"🟡 Amarelo","2_orange":"🟠 Laranja","1_red":"🔴 Vermelho"}
    criticos = [a for a in r["alertas"] if a["tipo"]=="CRITICO"]
    atencoes = [a for a in r["alertas"] if a["tipo"]=="ATENCAO"]
    m_est = r["metricas"].get("estoque",{})

    badges = []
    if r["nivel"]=="3_yellow": badges.append('<span style="background:#2d2418;color:#FAC775;padding:3px 10px;border-radius:4px;font-size:11px;font-weight:600;">⚠ Reputação Amarela</span>')
    if m_est.get("sem_full",0)>0: badges.append('<span style="background:#2d1b1b;color:#f09575;padding:3px 10px;border-radius:4px;font-size:11px;font-weight:600;">⚠ Sem Full</span>')
    if r["nivel"] in ["1_red","2_orange"]: badges.append(f'<span style="background:#2d1b1b;color:#f09575;padding:3px 10px;border-radius:4px;font-size:11px;font-weight:600;">⚠ Reputação {r["nivel"].split("_")[1].title()}</span>')

    st.markdown(f"""
    <div style="padding:24px 24px 0;">
        <div style="background:#13131f;border:1px solid #1e1e2e;border-radius:12px;padding:20px;margin-bottom:16px;">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div style="flex:1;">
                    <div style="font-size:11px;color:#6b6b8a;margin-bottom:2px;">{r['seller']} · Mercado Livre Brasil · {r['gerado_em']}</div>
                    <div style="font-size:20px;font-weight:700;color:#e2e2f0;margin-bottom:6px;">{r['seller']}</div>
                    <div style="font-size:12px;color:#6b6b8a;margin-bottom:10px;">{nivel_labels.get(r['nivel'],r['nivel'])} · {r['mercadolider'].title()}</div>
                    <div style="display:flex;gap:6px;flex-wrap:wrap;">{"".join(badges)}</div>
                </div>
                <div style="text-align:center;background:{cor}15;border:2px solid {cor};border-radius:12px;padding:14px 22px;min-width:90px;">
                    <div style="font-size:44px;font-weight:900;color:{cor};line-height:1;">{r['score_total']}</div>
                    <div style="font-size:10px;color:{cor};font-weight:600;margin-top:2px;">{r['status']}</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if criticos:
        n_rup = m_est.get("itens_ruptura",0)
        msg = f"Sua conta tem <strong>{len(criticos)} problema{'s' if len(criticos)>1 else ''} crítico{'s' if len(criticos)>1 else ''}</strong>"
        if n_rup > 0: msg += f". {n_rup} SKU{'s' if n_rup>1 else ''} com estoque zero e anúncio ativo — budget sendo queimado sem vendas. <strong>Resolva hoje.</strong>"
        st.markdown(f'<div style="margin:0 24px 16px;background:#2d1b1b;border:1px solid #e52b2b40;border-radius:10px;padding:14px 18px;font-size:13px;color:#f09575;">⚠️ {msg}</div>', unsafe_allow_html=True)

    st.markdown('<div style="padding:0 24px;">', unsafe_allow_html=True)
    sc = r["scores"]
    s_cols = st.columns(5)
    for col, (nome, key) in zip(s_cols,[("Reputação","reputacao"),("Operação","operacao"),("Estoque","estoque"),("Atendimento","atendimento"),("Publicidade","publicidade")]):
        c = cor_score(sc[key])
        col.markdown(f'<div style="background:#13131f;border:1px solid #1e1e2e;border-radius:10px;padding:12px;text-align:center;margin-bottom:12px;"><div style="font-size:28px;font-weight:800;color:{c};">{sc[key]}</div><div style="font-size:11px;color:#6b6b8a;">{nome}</div></div>', unsafe_allow_html=True)

    st.markdown('<div style="font-size:12px;font-weight:600;color:#6b6b8a;letter-spacing:0.06em;margin:16px 0 10px;">PROBLEMAS ENCONTRADOS</div>', unsafe_allow_html=True)
    todos = criticos + atencoes
    if todos:
        for i in range(0, len(todos), 2):
            cols = st.columns(2)
            for j, col in enumerate(cols):
                if i+j < len(todos):
                    a = todos[i+j]
                    tc = "#e52b2b" if a["tipo"]=="CRITICO" else "#f5a623"
                    tb = "#2d1b1b" if a["tipo"]=="CRITICO" else "#2d2418"
                    tl = "Crítico" if a["tipo"]=="CRITICO" else "Atenção"
                    col.markdown(f"""
                    <div style="background:{tb};border:1px solid {tc}30;border-radius:10px;padding:16px;margin-bottom:10px;">
                        <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px;">
                            <span style="background:{tc};color:#fff;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700;">{tl}</span>
                            <span style="font-size:11px;color:#6b6b8a;">{a['categoria']}</span>
                        </div>
                        <div style="font-size:13px;font-weight:600;color:#e2e2f0;margin-bottom:6px;">{a['mensagem']}</div>
                        <div style="font-size:12px;color:#a0a0c0;margin-bottom:4px;">{a['acao']}</div>
                        <div style="font-size:10px;color:#6b6b8a;">🔖 {a['referencia']}</div>
                    </div>
                    """, unsafe_allow_html=True)

    st.markdown('<div style="font-size:13px;font-weight:600;color:#e2e2f0;margin:20px 0 10px;">📊 Score por categoria</div>', unsafe_allow_html=True)
    g1,g2,g3,g4,g5 = st.columns(5)
    g1.plotly_chart(gauge(sc["reputacao"],"Reputação"), use_container_width=True)
    g2.plotly_chart(gauge(sc["operacao"],"Operação"), use_container_width=True)
    g3.plotly_chart(gauge(sc["estoque"],"Estoque"), use_container_width=True)
    g4.plotly_chart(gauge(sc["atendimento"],"Atendimento"), use_container_width=True)
    g5.plotly_chart(gauge(sc["publicidade"],"Publicidade"), use_container_width=True)

    historico = buscar_historico(usuario["id"], conta_ml_id) if conta_ml_id else []
    if len(historico) > 1:
        st.markdown('<div style="font-size:13px;font-weight:600;color:#e2e2f0;margin:20px 0 10px;">📈 Evolução do score</div>', unsafe_allow_html=True)
        datas = [h["criado_em"][:10] for h in reversed(historico)]
        scores_hist = [h["score_total"] for h in reversed(historico)]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=datas, y=scores_hist, mode="lines+markers", line=dict(color="#00a650",width=2), marker=dict(size=6,color="#00a650")))
        fig.update_layout(height=200, paper_bgcolor="#13131f", plot_bgcolor="#13131f", margin=dict(t=10,b=30,l=30,r=10), xaxis=dict(color="#6b6b8a"), yaxis=dict(color="#6b6b8a",range=[0,100]))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div style="font-size:13px;font-weight:600;color:#e2e2f0;margin:20px 0 10px;">📈 Métricas detalhadas</div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["Reputação & Operação","Estoque & SKUs","Atendimento"])
    with tab1:
        ca, cb = st.columns(2)
        with ca:
            m = r["metricas"].get("reputacao",{})
            st.metric("Avaliações positivas", m.get("positivas","-"))
            st.metric("Total de vendas", str(m.get("total_vendas","-")))
        with cb:
            m = r["metricas"].get("operacao",{})
            st.metric("Atraso no envio", m.get("atraso","-"), delta="Meta: ≥90% no prazo", delta_color="off")
            st.metric("Cancelamentos", m.get("cancelamento","-"), delta="Meta: ≤1%", delta_color="off")
            st.metric("Reclamações", m.get("reclamacao","-"), delta="Meta: ≤2%", delta_color="off")
    with tab2:
        m = r["metricas"].get("estoque",{})
        e1,e2,e3,e4 = st.columns(4)
        e1.metric("Total itens", m.get("total_itens",0))
        e2.metric("Itens ativos", m.get("itens_ativos",0))
        e3.metric("Em ruptura", m.get("itens_ruptura",0))
        e4.metric("Estoque crítico", m.get("itens_estoque_baixo",0))
        if r["skus"]: st.dataframe(pd.DataFrame(r["skus"]), use_container_width=True, hide_index=True)
    with tab3:
        m = r["metricas"].get("atendimento",{})
        st.metric("Perguntas sem resposta", m.get("perguntas_sem_resposta",0))
        st.caption("Ideal: responder em menos de 1 hora.")
    st.markdown('</div>', unsafe_allow_html=True)

# ============ ANALISAR PRODUTO ============
def pagina_analisar(usuario):
    if "access_token" not in st.session_state:
        st.markdown('<div style="padding:24px;color:#6b6b8a;font-size:13px;">Conecte sua conta ML na barra lateral primeiro.</div>', unsafe_allow_html=True); return

    st.markdown('<div style="padding:24px;">', unsafe_allow_html=True)
    st.markdown('<div style="font-size:20px;font-weight:700;color:#e2e2f0;margin-bottom:4px;">Analisar produto</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:12px;color:#6b6b8a;margin-bottom:20px;">Cole o MLB para diagnóstico completo — qualidade do algoritmo, simulador de ads e precificação</div>', unsafe_allow_html=True)

    col_in, col_btn = st.columns([4,1])
    with col_in: mlb = st.text_input("", placeholder="Ex: MLB4341336433", label_visibility="collapsed")
    with col_btn: buscar = st.button("🔍 Analisar", use_container_width=True)

    if buscar and mlb:
        with st.spinner(f"Analisando {mlb.strip().upper()}..."):
            item = analisar_item(mlb.strip().upper(), st.session_state["access_token"], st.session_state["user_id"])
        if not item:
            st.markdown('<div style="background:#2d1b1b;border:1px solid #e52b2b40;border-radius:8px;padding:14px;color:#f09575;font-size:13px;">Produto não encontrado. Verifique o MLB.</div>', unsafe_allow_html=True)
        else:
            cs = cor_score(item["score_total"])
            log_label = "Full" if item["logistica"]=="fulfillment" else "Flex" if item["logistica"]=="xd_drop_off" else "Padrão"
            lc = "#9FE1CB" if item["logistica"]=="fulfillment" else "#FAC775" if item["logistica"]=="xd_drop_off" else "#f09575"
            lb = "#0d2d1a" if item["logistica"]=="fulfillment" else "#2d2418" if item["logistica"]=="xd_drop_off" else "#2d1b1b"
            st.markdown(f"""
            <div style="background:#13131f;border:1px solid #1e1e2e;border-radius:12px;padding:18px;margin:16px 0;">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                    <div style="flex:1;">
                        <div style="font-size:11px;color:#6b6b8a;font-family:monospace;margin-bottom:4px;">{item['item_id']}</div>
                        <div style="font-size:15px;font-weight:600;color:#e2e2f0;margin-bottom:10px;">{item['titulo']}</div>
                        <div style="display:flex;gap:6px;flex-wrap:wrap;">
                            <span style="background:#1a1a2e;color:#a0a0c0;padding:3px 8px;border-radius:4px;font-size:11px;">R${item['preco']}</span>
                            <span style="background:{'#2d1b1b' if item['estoque']==0 else '#0d2d1a'};color:{'#f09575' if item['estoque']==0 else '#9FE1CB'};padding:3px 8px;border-radius:4px;font-size:11px;">Estoque: {item['estoque']}</span>
                            <span style="background:#1a1a2e;color:#a0a0c0;padding:3px 8px;border-radius:4px;font-size:11px;">Vendas: {item['vendas']}</span>
                            <span style="background:{lb};color:{lc};padding:3px 8px;border-radius:4px;font-size:11px;">{log_label}</span>
                        </div>
                    </div>
                    <div style="text-align:center;background:{cs}15;border:2px solid {cs};border-radius:10px;padding:12px 20px;margin-left:16px;">
                        <div style="font-size:36px;font-weight:900;color:{cs};line-height:1;">{item['score_total']}</div>
                        <div style="font-size:10px;color:{cs};margin-top:2px;">Score /100</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            tab_fat, tab_ads, tab_preco = st.tabs(["📊 8 fatores do algoritmo","📢 Simulador de Ads","💰 Precificação"])

            with tab_fat:
                fatores = [
                    ("Título", item["scores"]["titulo"], item["acoes"]["titulo"], item["refs"]["titulo"]),
                    ("Fotos", item["scores"]["fotos"], item["acoes"]["fotos"], item["refs"]["fotos"]),
                    ("Ficha técnica", item["scores"]["ficha"], item["acoes"]["ficha"], item["refs"]["ficha"]),
                    ("Descrição", item["scores"]["descricao"], item["acoes"]["descricao"], item["refs"]["descricao"]),
                    ("Preço total", item["scores"]["preco"], item["acoes"]["preco"], item["refs"]["preco"]),
                    ("Reputação", item["scores"]["reputacao"], item["acoes"]["reputacao"], item["refs"]["reputacao"]),
                    ("Logística", item["scores"]["logistica"], item["acoes"]["logistica"], item["refs"]["logistica"]),
                    ("Conversão", item["scores"]["conversao"], item["acoes"]["conversao"], item["refs"]["conversao"]),
                ]
                st.markdown('<div style="background:#13131f;border:1px solid #1e1e2e;border-radius:12px;padding:16px;">', unsafe_allow_html=True)
                for nome, score, acao, ref in fatores:
                    fc = cor_score(score)
                    st.markdown(f"""
                    <div style="display:grid;grid-template-columns:110px 1fr 36px;gap:12px;align-items:center;padding:10px 0;border-bottom:1px solid #1e1e2e;">
                        <div style="font-size:12px;color:#e2e2f0;font-weight:500;">{nome}</div>
                        <div>
                            <div style="height:4px;background:#1e1e2e;border-radius:2px;overflow:hidden;margin-bottom:4px;"><div style="width:{score}%;height:100%;background:{fc};border-radius:2px;"></div></div>
                            <div style="font-size:11px;color:#6b6b8a;">{acao}</div>
                            <div style="font-size:10px;color:#444;margin-top:2px;">📌 {ref}</div>
                        </div>
                        <div style="font-size:13px;font-weight:700;color:{fc};text-align:right;">{score}</div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with tab_ads:
                if not item["pode_anunciar"]:
                    motivos = []
                    if item["estoque"]==0: motivos.append("estoque zerado")
                    if item["status"]!="active": motivos.append("anúncio fechado")
                    if item["vendas"]==0: motivos.append("sem histórico de vendas")
                    st.markdown(f'<div style="background:#2d1b1b;border:1px solid #e52b2b40;border-radius:10px;padding:16px;margin-bottom:12px;"><div style="font-size:13px;font-weight:600;color:#f09575;margin-bottom:6px;">⚠️ Não recomendado anunciar agora</div><div style="font-size:12px;color:#a0a0c0;margin-bottom:6px;">Motivo: {", ".join(motivos)}</div><div style="font-size:11px;color:#6b6b8a;">📌 Resolva os problemas antes de ativar ads. Anunciar sem histórico ou estoque desperdiça budget.</div></div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="background:#0d2d1a;border:1px solid #00a65040;border-radius:8px;padding:12px;font-size:12px;color:#9FE1CB;margin-bottom:16px;">✅ Este produto está pronto para anunciar.</div>', unsafe_allow_html=True)

                col_m1, col_m2, col_m3 = st.columns(3)
                margem_ads = col_m1.number_input("Margem líquida (%)", 1, 80, 20, key="ads_m")
                estagio = col_m2.selectbox("Estágio", ["novo","crescimento","consolidado"], format_func=lambda x: {"novo":"Novo (<15 vendas)","crescimento":"Crescimento (15-50)","consolidado":"Consolidado (50+)"}[x])
                budget_dia = col_m3.number_input("Budget diário (R$)", 10, 2000, 50, key="ads_b")
                roas_min = round(100/margem_ads, 1)
                roas_rec = max(2, roas_min-2) if estagio=="novo" else roas_min+2 if estagio=="crescimento" else roas_min+4
                r1,r2,r3,r4 = st.columns(4)
                r1.metric("ROAS mínimo p/ lucrar", f"{roas_min}x")
                r2.metric("ROAS objetivo", f"{roas_rec}x")
                r3.metric("Budget diário", f"R${budget_dia}")
                r4.metric("Investimento mensal", f"R${budget_dia*30:,}".replace(",","."))
                msgs = {"novo":f"Produto novo: ROAS {roas_rec}x para ganhar histórico. Aguarde 15-28 dias antes de ajustar lances.","crescimento":f"Em crescimento: ROAS {roas_rec}x. Aguarde 28 dias de dados antes de ajustar.","consolidado":f"Consolidado: ROAS {roas_rec}x. Monitore TACOS (gasto ads / receita total da conta)."}
                st.markdown(f'<div style="background:#0d1f35;border:1px solid #3b82f640;border-radius:8px;padding:12px;font-size:12px;color:#7ab3f0;margin-top:12px;">💡 {msgs[estagio]}</div>', unsafe_allow_html=True)
                st.markdown('<div style="font-size:11px;color:#444;margin-top:8px;">📌 Desde outubro/2025 o ML usa ROAS como métrica principal. Conclusão estatística confiável só após 28 dias de campanha.</div>', unsafe_allow_html=True)

            with tab_preco:
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    cmv_p = st.number_input("CMV (custo do produto)", 0.0, value=float(item['preco'])*0.6, step=10.0, key="pp_cmv")
                    tipo_p = st.selectbox("Tipo de anúncio", ["Clássico (11-14%)","Premium (16-19%)"], key="pp_tipo")
                    frete_p = st.selectbox("Frete", ["Padrão (~R$15)","Full (R$0)","Flex (~R$8)"], key="pp_frete")
                    imposto_p = st.selectbox("Regime fiscal", ["MEI (6%)","Simples Nacional (10%)","Lucro Presumido (15%)"], key="pp_imp")
                    margem_p = st.slider("Margem desejada (%)", 5, 50, 20, key="pp_m")
                com_pct = 0.12 if "Clássico" in tipo_p else 0.17
                fr_v = 0 if "Full" in frete_p else 8 if "Flex" in frete_p else 15
                imp_pct = 0.06 if "MEI" in imposto_p else 0.15 if "Lucro" in imposto_p else 0.10
                pi, cv, iv, lv = calcular_preco(cmv_p, com_pct, fr_v, imp_pct, margem_p)
                ma = ((item['preco']-cmv_p-item['preco']*com_pct-fr_v-item['preco']*imp_pct)/item['preco']*100) if item['preco']>0 else 0
                with col_p2:
                    st.markdown(f"""<div style="background:#13131f;border:1px solid #1e1e2e;border-radius:12px;padding:18px;">
                        <div style="background:#00a65015;border:1px solid #00a65040;border-radius:8px;padding:14px;text-align:center;margin-bottom:14px;">
                            <div style="font-size:11px;color:#00a650;margin-bottom:4px;">Preço ideal para {margem_p}% de margem</div>
                            <div style="font-size:34px;font-weight:900;color:#00a650;">R${pi:.2f}</div>
                        </div>""", unsafe_allow_html=True)
                    for lbl, val, c in [("Preço atual",f"R${item['preco']}","#e2e2f0"),("Comissão ML",f"- R${cv:.2f}","#e52b2b"),("Frete",f"- R${fr_v:.2f}","#e52b2b"),("Impostos",f"- R${iv:.2f}","#e52b2b"),("Lucro líquido",f"R${lv:.2f}","#00a650" if lv>0 else "#e52b2b")]:
                        st.markdown(f'<div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #1e1e2e;font-size:13px;"><span style="color:#6b6b8a;">{lbl}</span><span style="font-weight:600;color:{c};">{val}</span></div>', unsafe_allow_html=True)
                    cm_a = "#00a650" if ma>10 else "#f5a623" if ma>0 else "#e52b2b"
                    msg_a = f"✅ Margem atual: {ma:.1f}%" if ma>10 else f"🟡 Margem apertada: {ma:.1f}%" if ma>0 else f"⚠️ Vendendo no prejuízo: {ma:.1f}%"
                    st.markdown(f'<div style="margin-top:10px;padding:10px;background:{cm_a}15;border-radius:6px;font-size:12px;color:{cm_a};">{msg_a}</div>', unsafe_allow_html=True)
                    st.markdown('<div style="font-size:10px;color:#444;margin-top:8px;">📌 Comissões 2026: Clássico 11-14%, Premium 16-19%. Desde mar/2026 custo fixo é variável por peso/dimensão (produtos abaixo de R$79).</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ============ CALCULADORA ============
def pagina_calculadora():
    st.markdown('<div style="padding:24px;">', unsafe_allow_html=True)
    st.markdown('<div style="font-size:20px;font-weight:700;color:#e2e2f0;margin-bottom:4px;">Calculadora de precificação</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:12px;color:#6b6b8a;margin-bottom:20px;">Calcule o preço ideal com todos os custos reais do ML 2026</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        cmv = st.number_input("Custo do produto (CMV)", 0.0, value=150.0, step=5.0)
        tipo = st.selectbox("Tipo de anúncio", ["Clássico (11-14%)","Premium (16-19%)"])
        frete = st.selectbox("Frete", ["Padrão (~R$15)","Full (R$0)","Flex (~R$8)"])
        imposto = st.selectbox("Regime fiscal", ["MEI (6%)","Simples Nacional (10%)","Lucro Presumido (15%)"])
        margem_d = st.slider("Margem desejada (%)", 5, 60, 20)
        preco_atual = st.number_input("Seu preço atual (opcional)", 0.0, step=5.0)
    com_pct = 0.12 if "Clássico" in tipo else 0.17
    fr_v = 0 if "Full" in frete else 8 if "Flex" in frete else 15
    imp_pct = 0.06 if "MEI" in imposto else 0.15 if "Lucro" in imposto else 0.10
    pi, cv, iv, lv = calcular_preco(cmv, com_pct, fr_v, imp_pct, margem_d)
    with col2:
        st.markdown(f"""<div style="background:#13131f;border:1px solid #1e1e2e;border-radius:12px;padding:20px;">
            <div style="background:#00a65015;border:1px solid #00a65040;border-radius:8px;padding:16px;text-align:center;margin-bottom:16px;">
                <div style="font-size:12px;color:#00a650;margin-bottom:4px;">Preço ideal para {margem_d}% de margem</div>
                <div style="font-size:38px;font-weight:900;color:#00a650;">R${pi:.2f}</div>
            </div>""", unsafe_allow_html=True)
        for lbl, val, c in [("Comissão ML",f"- R${cv:.2f}","#e52b2b"),("Frete",f"- R${fr_v:.2f}","#e52b2b"),("Impostos",f"- R${iv:.2f}","#e52b2b"),("Lucro líquido",f"R${lv:.2f}","#00a650" if lv>0 else "#e52b2b")]:
            st.markdown(f'<div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #1e1e2e;font-size:13px;"><span style="color:#6b6b8a;">{lbl}</span><span style="font-weight:600;color:{c};">{val}</span></div>', unsafe_allow_html=True)
        if preco_atual > 0:
            ma = ((preco_atual-cmv-preco_atual*com_pct-fr_v-preco_atual*imp_pct)/preco_atual*100)
            cm_a = "#00a650" if ma>10 else "#f5a623" if ma>0 else "#e52b2b"
            msg_a = f"✅ Margem atual: {ma:.1f}%" if ma>10 else f"🟡 Margem apertada: {ma:.1f}%" if ma>0 else f"⚠️ Vendendo no prejuízo: {ma:.1f}%"
            st.markdown(f'<div style="margin-top:12px;padding:10px;background:{cm_a}15;border-radius:6px;font-size:12px;color:{cm_a};">{msg_a}</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:10px;color:#444;margin-top:10px;">📌 Comissões 2026: Clássico 11-14%, Premium 16-19%. Custo fixo variável por peso/dimensão para produtos abaixo de R$79 (desde mar/2026).</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ============ PLANO DE AÇÃO ============
def pagina_plano():
    st.markdown('<div style="padding:24px;">', unsafe_allow_html=True)
    st.markdown('<div style="font-size:20px;font-weight:700;color:#e2e2f0;margin-bottom:4px;">Plano de ação</div>', unsafe_allow_html=True)
    if "diagnostico" not in st.session_state:
        st.markdown('<div style="background:#13131f;border:1px solid #1e1e2e;border-radius:10px;padding:20px;color:#6b6b8a;font-size:13px;">Gere o diagnóstico primeiro na Visão Geral.</div>', unsafe_allow_html=True)
        return
    r = st.session_state["diagnostico"]
    st.markdown(f'<div style="font-size:12px;color:#6b6b8a;margin-bottom:20px;">Baseado no diagnóstico de {r["gerado_em"]}</div>', unsafe_allow_html=True)
    criticos = [a for a in r["alertas"] if a["tipo"]=="CRITICO"]
    atencoes = [a for a in r["alertas"] if a["tipo"]=="ATENCAO"]
    if criticos:
        st.markdown('<div style="font-size:13px;font-weight:700;color:#e52b2b;margin-bottom:10px;">🔴 Faça hoje</div>', unsafe_allow_html=True)
        for i, a in enumerate(criticos, 1):
            with st.expander(f"{i}. [{a['categoria']}] {a['mensagem'][:70]}"):
                st.markdown(f"**Problema:** {a['mensagem']}")
                st.markdown(f"**O que fazer:** {a['acao']}")
                st.caption(f"📌 {a['referencia']}")
    if atencoes:
        st.markdown('<div style="font-size:13px;font-weight:700;color:#f5a623;margin:20px 0 10px;">🟡 Esta semana</div>', unsafe_allow_html=True)
        for i, a in enumerate(atencoes, 1):
            with st.expander(f"{i}. [{a['categoria']}] {a['mensagem'][:70]}"):
                st.markdown(f"**Problema:** {a['mensagem']}")
                st.markdown(f"**O que fazer:** {a['acao']}")
                st.caption(f"📌 {a['referencia']}")
    if not criticos and not atencoes:
        st.markdown('<div style="background:#0d2d1a;border:1px solid #00a650;border-radius:10px;padding:20px;text-align:center;color:#9FE1CB;">🎉 Operação saudável! Continue monitorando semanalmente.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ============ MAIN ============
if "usuario" not in st.session_state:
    tela_login()
else:
    usuario = st.session_state["usuario"]
    pagina = render_sidebar(usuario)
    if pagina == "🏠 Visão geral": pagina_visao_geral(usuario)
    elif pagina == "📦 Analisar produto": pagina_analisar(usuario)
    elif pagina == "🧮 Calculadora": pagina_calculadora()
    elif pagina == "📋 Plano de ação": pagina_plano()
