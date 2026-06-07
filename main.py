from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from supabase import create_client
import requests
import hashlib
import os
from datetime import datetime
from fastapi import Request

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://mfyabqodkjbpvykfkiwj.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_YfRzYbb-YbKxMK1OcdvRKA_OrhdjIt1")
CLIENT_ID = os.environ.get("ML_CLIENT_ID", "8361153242610469")
CLIENT_SECRET = os.environ.get("ML_CLIENT_SECRET", "3o8z0V9ogn90pA3Gr6hCLUdJC1TYi1Pd")
REDIRECT_URI = os.environ.get("REDIRECT_URI", "https://httpbingo.org/get")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def hash_senha(s): return hashlib.sha256(s.encode()).hexdigest()
def cor_score(s): return "red" if s < 60 else "yellow" if s < 80 else "green"

# ============ AUTH ============
class LoginData(BaseModel):
    email: str
    senha: str
    nome: str = ""
    plano: str = "starter"

@app.post("/auth/register")
def register(data: LoginData):
    try:
        existe = supabase.table("usuarios").select("id").eq("email", data.email).execute()
        if existe.data:
            raise HTTPException(status_code=400, detail="Email já cadastrado")
        r = supabase.table("usuarios").insert({
            "email": data.email,
            "senha_hash": hash_senha(data.senha),
            "nome": data.nome,
            "plano": data.plano
        }).execute()
        return {"success": True, "usuario": r.data[0]}
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/login")
def login(data: LoginData):
    try:
        r = supabase.table("usuarios").select("*").eq("email", data.email).eq("senha_hash", hash_senha(data.senha)).execute()
        if not r.data:
            raise HTTPException(status_code=401, detail="Email ou senha incorretos")
        return {"success": True, "usuario": r.data[0]}
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

# ============ ML AUTH ============
class CodeData(BaseModel):
    code: str
    usuario_id: str

@app.post("/ml/connect")
def ml_connect(data: CodeData):
    try:
        r = requests.post("https://api.mercadolibre.com/oauth/token", data={
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": data.code,
            "redirect_uri": REDIRECT_URI
        })
        td = r.json()
        if not td.get("access_token"):
            raise HTTPException(status_code=400, detail="Código inválido")
        
        token = td["access_token"]
        ml_uid = str(td["user_id"])
        r_user = requests.get(f"https://api.mercadolibre.com/users/{ml_uid}", headers={"Authorization": f"Bearer {token}"})
        nickname = r_user.json().get("nickname", ml_uid)

        existe = supabase.table("contas_ml").select("id").eq("usuario_id", data.usuario_id).eq("ml_user_id", ml_uid).execute()
        if existe.data:
            conta_id = existe.data[0]["id"]
            supabase.table("contas_ml").update({"access_token": token, "ml_nickname": nickname}).eq("id", conta_id).execute()
        else:
            rc = supabase.table("contas_ml").insert({
                "usuario_id": data.usuario_id,
                "ml_user_id": ml_uid,
                "ml_nickname": nickname,
                "access_token": token
            }).execute()
            conta_id = rc.data[0]["id"]

        return {"success": True, "access_token": token, "ml_user_id": ml_uid, "nickname": nickname, "conta_ml_id": conta_id}
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
    # ============ PAGAMENTO ============
MP_ACCESS_TOKEN_TEST = "TEST-717563241748022-060623-4ad997f3b63c9e541829c12ed3cbab25-165491273"
MP_ACCESS_TOKEN_PROD = os.environ.get("MP_ACCESS_TOKEN_PROD", "")

PLANOS = {
    "starter": {"nome": "RaioxSeller Starter", "valor": 97.00},
    "pro": {"nome": "RaioxSeller Pro", "valor": 197.00},
    "agencia": {"nome": "RaioxSeller Agência", "valor": 397.00}
}

class AssinaturaData(BaseModel):
    plano: str
    usuario_id: str
    email: str
    nome: str = ""

@app.post("/pagamento/criar")
def criar_assinatura(data: AssinaturaData):
    if data.plano not in PLANOS:
        raise HTTPException(status_code=400, detail="Plano inválido")
    
    plano = PLANOS[data.plano]
    token = MP_ACCESS_TOKEN_TEST
    
    try:
        # Cria plano de assinatura no MP
        r_plano = requests.post(
            "https://api.mercadopago.com/preapproval_plan",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={
                "reason": plano["nome"],
                "auto_recurring": {
                    "frequency": 1,
                    "frequency_type": "months",
                    "transaction_amount": plano["valor"],
                    "currency_id": "BRL"
                },
                "payment_methods_allowed": {
                    "payment_types": [{"id": "credit_card"}, {"id": "debit_card"}],
                    "payment_methods": [{"id": "pix"}]
                },
                "back_url": "https://raioxseller-frontend.vercel.app/sucesso"
            }
        )
        plano_data = r_plano.json()
        plano_id = plano_data.get("id")
        
        if not plano_id:
            raise HTTPException(status_code=500, detail=f"Erro ao criar plano: {plano_data}")
        
        # Cria assinatura para o usuário
        r_ass = requests.post(
            "https://api.mercadopago.com/preapproval",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={
                "preapproval_plan_id": plano_id,
                "reason": plano["nome"],
                "payer_email": data.email,
                "auto_recurring": {
                    "frequency": 1,
                    "frequency_type": "months",
                    "transaction_amount": plano["valor"],
                    "currency_id": "BRL"
                },
                "back_url": "https://raioxseller-frontend.vercel.app/sucesso",
                "external_reference": f"{data.usuario_id}_{data.plano}"
            }
        )
        ass_data = r_ass.json()
        init_point = ass_data.get("init_point")
        
        if not init_point:
            raise HTTPException(status_code=500, detail=f"Erro ao criar assinatura: {ass_data}")
        
        return {"success": True, "checkout_url": init_point, "assinatura_id": ass_data.get("id")}
    
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

    @app.post("/pagamento/webhook")
    async def webhook_pagamento(request: Request):
    try:
        body = await request.json()
        tipo = body.get("type")
        
        if tipo == "subscription_preapproval":
            ass_id = body.get("data", {}).get("id")
            if ass_id:
                token = MP_ACCESS_TOKEN_TEST
                r = requests.get(
                    f"https://api.mercadopago.com/preapproval/{ass_id}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                ass = r.json()
                status = ass.get("status")
                ref = ass.get("external_reference", "")
                
                if "_" in ref and status == "authorized":
                    usuario_id, plano = ref.split("_", 1)
                    supabase.table("usuarios").update({"plano": plano}).eq("id", usuario_id).execute()
        
        return {"status": "ok"}
    except: return {"status": "ok"}

# ============ DIAGNÓSTICO ============
@app.get("/diagnostico/{user_id}")
def diagnostico(user_id: str, token: str, usuario_id: str, conta_ml_id: str = ""):
    H = {"Authorization": f"Bearer {token}"}
    resultado = {
        "seller": "", "nivel": "", "mercadolider": "", "score_total": 100,
        "scores": {"reputacao":100,"operacao":100,"estoque":100,"publicidade":100,"atendimento":100},
        "status": "", "alertas": [], "skus": [], "metricas": {},
        "gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M")
    }

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
        resultado["alertas"].append({"tipo":"CRITICO","categoria":"Operação","mensagem":f"Atraso no envio: {round(taxa_atraso*100,1)}%. Meta: ≥90% no prazo.","acao":"Aumente prazo de handling para 2 dias.","referencia":"Meta ML Brasil: ≥90% de envios dentro do prazo"})
    elif taxa_atraso > 0.05:
        score_op -= 20
        resultado["alertas"].append({"tipo":"ATENCAO","categoria":"Operação","mensagem":f"Atraso no envio: {round(taxa_atraso*100,1)}%.","acao":"Ajuste prazo de handling nos anúncios.","referencia":"Meta ML Brasil: ≥90% de envios dentro do prazo"})
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
    perguntas = r_perguntas.json().get("total",0) if r_perguntas.status_code==200 else 0
    score_atend = 100
    if perguntas > 10:
        score_atend -= 40
        resultado["alertas"].append({"tipo":"CRITICO","categoria":"Atendimento","mensagem":f"{perguntas} perguntas sem resposta.","acao":"Responda todas. Ideal: menos de 1 hora.","referencia":"Perguntas sem resposta reduzem conversão e posicionamento"})
    elif perguntas > 3:
        score_atend -= 20
        resultado["alertas"].append({"tipo":"ATENCAO","categoria":"Atendimento","mensagem":f"{perguntas} perguntas sem resposta.","acao":"Crie rotina de resposta diária.","referencia":"ML considera bom: resposta em até 1 hora"})
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
        if status=="active":
            itens_ativos += 1
            if logistica not in ["fulfillment","xd_drop_off"]: sem_full += 1
        if estoque==0 and status=="active":
            itens_ruptura += 1; score_estoque -= 25
            problemas.append("Ruptura com anúncio ativo")
            resultado["alertas"].append({"tipo":"CRITICO","categoria":"Estoque","mensagem":f"'{tc}' ATIVO com estoque ZERO.","acao":"Pause o anúncio imediatamente ou reponha estoque.","referencia":"Anúncio ativo sem estoque queima budget de ads"})
        elif estoque==0 and status=="closed" and vendas>0:
            score_estoque -= 10
            resultado["alertas"].append({"tipo":"ATENCAO","categoria":"Estoque","mensagem":f"'{tc}' fechado com {vendas} vendas anteriores.","acao":f"Repor estoque e reativar. Potencial: R${preco}/venda.","referencia":"Produto com histórico tem mais chance de conversão"})
        elif 0<estoque<=5 and status=="active":
            itens_baixo += 1
            resultado["alertas"].append({"tipo":"ATENCAO","categoria":"Estoque","mensagem":f"'{tc}' com apenas {estoque} unidades.","acao":"Repor estoque antes de atingir zero.","referencia":"Ruptura frequente pode levar à desativação automática"})
        if logistica not in ["fulfillment","xd_drop_off"] and status=="active": problemas.append("Sem Full/Flex")
        resultado["skus"].append({"produto":tc,"preco":preco,"estoque":estoque,"vendas":vendas,"status":status,"logistica":logistica or "Padrao","situacao":" | ".join(problemas) if problemas else "OK"})

    resultado["scores"]["estoque"] = max(0, score_estoque)
    resultado["metricas"]["estoque"] = {"total_itens":total_itens,"itens_ativos":itens_ativos,"itens_ruptura":itens_ruptura,"itens_estoque_baixo":itens_baixo,"sem_full":sem_full}
    if sem_full>0:
        resultado["alertas"].append({"tipo":"ATENCAO","categoria":"Logística","mensagem":f"{sem_full} itens ativos sem Full ou Flex.","acao":"Ative Full nos top SKUs para triplicar chances de venda.","referencia":"Full = 3x mais chances de venda + prioridade no algoritmo"})

    r_adv = requests.get("https://api.mercadolibre.com/advertising/advertisers?product_id=PADS", headers={**H,"Api-Version":"1"})
    score_ads = 50
    if r_adv.status_code==200:
        advertisers = r_adv.json().get("advertisers",[])
        if advertisers:
            score_ads = 100
            adv_id = advertisers[0].get("advertiser_id")
            hoje = datetime.now()
            r_camp = requests.get(f"https://api.mercadolibre.com/advertising/advertisers/{adv_id}/product_ads/campaigns/search?date_from={hoje.year}-01-01&date_to={hoje.strftime('%Y-%m-%d')}&metrics=clicks,cost,roas", headers={**H,"Api-Version":"2"})
            if r_camp.status_code==200:
                for c in r_camp.json().get("campaigns",[]):
                    roas = c.get("metrics",{}).get("roas",0) or 0
                    nome = c.get("name","Campanha")
                    if roas and roas<3:
                        score_ads -= 20
                        resultado["alertas"].append({"tipo":"CRITICO","categoria":"Publicidade","mensagem":f"Campanha '{nome}': ROAS {round(roas,1)}x — abaixo do mínimo.","acao":"Pause itens sem conversão. ROAS mínimo = 100 / margem%.","referencia":"Desde out/2025 o ML usa ROAS como métrica principal"})
        else:
            resultado["alertas"].append({"tipo":"INFO","categoria":"Publicidade","mensagem":"Conta sem Product Ads ativo.","acao":"Ative Product Ads nos SKUs com histórico e estoque ok.","referencia":"Sellers com ads têm prioridade no posicionamento"})
    resultado["scores"]["publicidade"] = max(0, score_ads)

    pesos = {"reputacao":0.30,"operacao":0.25,"estoque":0.20,"atendimento":0.15,"publicidade":0.10}
    resultado["score_total"] = int(sum(resultado["scores"][k]*v for k,v in pesos.items()))
    resultado["status"] = "SAUDAVEL" if resultado["score_total"]>=80 else "ATENCAO" if resultado["score_total"]>=60 else "CRITICO"
    resultado["alertas"].sort(key=lambda x: {"CRITICO":0,"ATENCAO":1,"INFO":2}.get(x["tipo"],3))

    # Salva no Supabase
    if conta_ml_id:
        try:
            supabase.table("diagnosticos").insert({
                "usuario_id": usuario_id, "conta_ml_id": conta_ml_id,
                "ml_nickname": resultado["seller"], "score_total": resultado["score_total"],
                "score_reputacao": resultado["scores"]["reputacao"],
                "score_operacao": resultado["scores"]["operacao"],
                "score_estoque": resultado["scores"]["estoque"],
                "score_atendimento": resultado["scores"]["atendimento"],
                "score_publicidade": resultado["scores"]["publicidade"],
                "status": resultado["status"], "alertas": resultado["alertas"], "metricas": resultado["metricas"]
            }).execute()
        except: pass

    return resultado

# ============ ITEM ============
@app.get("/item/{item_id}")
def analisar_item(item_id: str, token: str, user_id: str):
    H = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"https://api.mercadolibre.com/items/{item_id}", headers=H)
    if r.status_code != 200: raise HTTPException(status_code=404, detail="Item não encontrado")
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
    acoes["titulo"] = f"Bom — {chars}/60 caracteres." if chars>=55 else f"{chars}/60 — use: Produto + Marca + Modelo + Características."
    refs["titulo"] = "Regra ML: Produto + Marca + Modelo + Características. Nunca repita palavras."

    n_fotos = len(fotos)
    scores["fotos"] = 90 if n_fotos>=6 else 55 if n_fotos>=4 else 25 if n_fotos>=2 else 0
    acoes["fotos"] = f"{n_fotos} fotos." if n_fotos>=6 else f"{n_fotos}/6 fotos — adicione {6-n_fotos} fotos."
    refs["fotos"] = "ML exige mínimo 6 fotos 1200x1200px com fundo branco."

    n_attrs = len(atributos)
    tem_gtin = any(a.get("id") in ["GTIN","EAN"] for a in atributos)
    scores["ficha"] = 90 if n_attrs>=10 else 55 if n_attrs>=6 else 25 if n_attrs>=3 else 0
    acoes["ficha"] = f"{n_attrs} atributos. {'GTIN presente.' if tem_gtin else 'Adicione GTIN/EAN para +40% visibilidade.'}"
    refs["ficha"] = "Ficha técnica é o principal fator de SEO do ML. GTIN/EAN aumenta visibilidade em até 40%."

    chars_desc = len(descricao)
    scores["descricao"] = 85 if chars_desc>=500 else 55 if chars_desc>=200 else 25 if chars_desc>0 else 0
    acoes["descricao"] = "Completa." if chars_desc>=500 else "Adicione: o que vem na caixa, compatibilidade e garantia."
    refs["descricao"] = "Descrição deve cobrir pontos de objeção e palavras-chave secundárias."

    scores["preco"] = 75 if preco>0 else 0
    acoes["preco"] = f"R${preco} — monitore paridade com Amazon e Shopee."
    refs["preco"] = "ML penaliza se encontrar produto mais barato em outro marketplace. Prazo: 3 dias."

    r_rep = requests.get(f"https://api.mercadolibre.com/users/{user_id}", headers=H)
    nivel = r_rep.json().get("seller_reputation",{}).get("level_id","") if r_rep.status_code==200 else ""
    nivel_nome = {'5_green':'Verde','4_light_green':'Verde claro','3_yellow':'Amarela','2_orange':'Laranja','1_red':'Vermelha'}.get(nivel,'desconhecida')
    scores["reputacao"] = {"5_green":100,"4_light_green":80,"3_yellow":55,"2_orange":30,"1_red":10}.get(nivel,50)
    acoes["reputacao"] = f"Reputação {nivel_nome} — impacta posicionamento deste anúncio."
    refs["reputacao"] = "Reputação do seller afeta posicionamento individual de cada anúncio."

    scores["logistica"] = 100 if logistica=="fulfillment" else 75 if logistica=="xd_drop_off" else 0
    acoes["logistica"] = "Full ativo — 3x mais chances de venda." if logistica=="fulfillment" else "Flex ativo." if logistica=="xd_drop_off" else "Envio padrão — ative Full para triplicar chances."
    refs["logistica"] = "Full = 3x mais chances de venda + prioridade nas buscas."

    scores["conversao"] = 100 if vendas>=50 else 80 if vendas>=20 else 55 if vendas>=5 else 30 if vendas>=1 else 0
    acoes["conversao"] = f"{vendas} vendas." if vendas>=1 else "Sem vendas — aguarde 15-28 dias antes de ativar ads."
    refs["conversao"] = "Produto novo precisa de 15-28 dias para o algoritmo otimizar."

    pesos = {"titulo":0.15,"fotos":0.20,"ficha":0.20,"descricao":0.10,"preco":0.10,"reputacao":0.10,"logistica":0.10,"conversao":0.05}
    score_total = int(sum(scores[k]*pesos[k] for k in pesos))

    return {"item_id":item_id,"titulo":titulo,"preco":preco,"estoque":estoque,"status":status,"vendas":vendas,
        "fotos":n_fotos,"logistica":logistica,"tipo_anuncio":tipo_anuncio,"score_total":score_total,
        "scores":scores,"acoes":acoes,"refs":refs,"pode_anunciar":estoque>0 and status=="active" and vendas>=1,"n_atributos":n_attrs}

# ============ HISTÓRICO ============
@app.get("/historico/{usuario_id}")
def historico(usuario_id: str, conta_ml_id: str):
    try:
        r = supabase.table("diagnosticos").select("score_total,criado_em").eq("usuario_id",usuario_id).eq("conta_ml_id",conta_ml_id).order("criado_em",desc=True).limit(6).execute()
        return {"data": r.data}
    except: return {"data": []}

@app.get("/health")
def health(): return {"status": "ok"}
