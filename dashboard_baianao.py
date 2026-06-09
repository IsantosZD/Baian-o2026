# -*- coding: utf-8 -*-
import os
import random
import hashlib
import hmac
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

st.set_page_config(layout="wide", page_title="Baianão")

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "estadual")

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{quote_plus(DB_PASSWORD)}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


for key, value in {
    "partida_escolhida": None,
    "mostrar_escalacao": False,
    "fundo_clube": None,
    "formacao_casa": None,
    "formacao_fora": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = value

FUNDO_PADRAO = "https://d1x4bjge7r9nas.cloudfront.net/wp-content/uploads/2026/03/07154419/Fonte-Nova-Final-Baianao-Leandro-Aragao.jpeg"
FUNDO_CLUBES = {
    "Bahia": "https://images.unsplash.com/photo-1547347298-4074fc3086f0?q=80&w=1600&auto=format&fit=crop",
    "Vitória": "https://images.unsplash.com/photo-1517466787929-bc90951d0974?q=80&w=1600&auto=format&fit=crop",
    "Jacuipense": "https://images.unsplash.com/photo-1574629810360-7efbbe195018?q=80&w=1600&auto=format&fit=crop",
    "Juazeirense": "https://images.unsplash.com/photo-1508098682722-e99c643e7f94?q=80&w=1600&auto=format&fit=crop",
}

fundo_atual = FUNDO_CLUBES.get(st.session_state["fundo_clube"], FUNDO_PADRAO)

st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url("{fundo_atual}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    .stApp::before {{
        content: "";
        position: fixed;
        inset: 0;
        background: rgba(4, 8, 14, 0.84);
        z-index: -1;
    }}
    .block-container {{ padding-top: 1.2rem; padding-bottom: 2rem; }}
    h1, h2, h3, h4, h5, h6, p, label, div, span {{ color: white; }}
    .stTabs [data-baseweb="tab-list"] {{
        gap: 10px;
        background: rgba(8, 12, 20, 0.78);
        padding: 10px;
        border-radius: 16px;
        border: 1px solid rgba(255,255,255,0.08);
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 42px;
        background: linear-gradient(180deg, rgba(22,27,34,0.95), rgba(11,15,20,0.95));
        border-radius: 12px;
        padding: 8px 16px;
        color: #d1d5db;
        font-weight: 700;
        border: 1px solid rgba(255,255,255,0.08);
    }}
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg,#0f172a,#14532d) !important;
        color: white !important;
        border: 1px solid rgba(34,197,94,0.7) !important;
    }}
    .stButton > button {{
        width: 100%;
        background: linear-gradient(180deg, #111827, #0b1220);
        color: #f9fafb;
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 12px;
        font-weight: 700;
        padding: 0.55rem 0.9rem;
        transition: all 0.20s ease;
    }}
    .stButton > button:hover {{
        color: #22c55e;
        border-color: rgba(34,197,94,0.65);
        transform: translateY(-2px);
    }}
    div[data-baseweb="select"] > div {{
        background: rgba(10, 15, 24, 0.85) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
    }}
    .custom-card {{
        background: linear-gradient(180deg, rgba(11,15,20,0.90), rgba(17,24,39,0.90));
        border-radius: 16px;
        border: 1px solid rgba(255,255,255,0.08);
        padding: 16px;
        text-align: center;
        margin-bottom: 12px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.20);
    }}
    .custom-card:hover {{
        transform: translateY(-3px);
        border-color: rgba(34,197,94,0.55);
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

USUARIOS = {
    "admin": {
        "senha": os.getenv("ADMIN_PASSWORD", "admin123"),
        "perfil": "Administrador",
    },
    "visitante": {
        "senha": os.getenv("VISITANTE_PASSWORD", "123456"),
        "perfil": "Visitante",
    },
}

def verificar_login(usuario: str, senha: str):
    usuario = (usuario or "").strip().lower()
    senha = senha or ""
    dados = USUARIOS.get(usuario)
    if not dados:
        return False
    return hmac.compare_digest(senha, dados["senha"])

def tela_login():
    st.markdown("# 🔐 Acesso ao Sistema")
    st.caption("Entre para acessar o painel do Baianão.")

    with st.form("form_login"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar")

    if entrar:
        usuario_normalizado = usuario.strip().lower()
        if verificar_login(usuario_normalizado, senha):
            st.session_state["autenticado"] = True
            st.session_state["usuario"] = usuario_normalizado
            st.session_state["perfil"] = USUARIOS[usuario_normalizado]["perfil"]
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")

    st.info("Usuários iniciais: admin / admin123 ou visitante / 123456.")

if not st.session_state.get("autenticado"):
    tela_login()
    st.stop()

with st.sidebar:
    st.markdown("### 👤 Sessão")
    st.write(f"Usuário: **{st.session_state.get('usuario')}**")
    st.write(f"Perfil: **{st.session_state.get('perfil')}**")
    if st.button("Sair"):
        st.session_state["autenticado"] = False
        st.session_state["usuario"] = None
        st.session_state["perfil"] = None
        st.rerun()

IS_ADMIN = st.session_state.get("perfil") == "Administrador"


def get_engine():
    return create_engine(DATABASE_URL, pool_pre_ping=True)

def garantir_schema():
    """Garante campos extras usados pelo dashboard sem precisar recriar o banco."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE partidas ADD COLUMN IF NOT EXISTS jogada BOOLEAN NOT NULL DEFAULT FALSE"))

@st.cache_data(show_spinner=False)
def carregar_dados():
    engine = get_engine()

    df_clubes = pd.read_sql_query("SELECT * FROM clubes ORDER BY nome", engine)

    df_partidas = pd.read_sql_query("""
        SELECT
            p.*,
            e.nome AS estadio_nome,
            e.cidade AS estadio_cidade,
            e.estado AS estadio_estado,
            e.foto_url AS estadio_foto,
            a.nome AS arbitro_nome,
            a.federacao AS arbitro_federacao
        FROM partidas p
        LEFT JOIN estadios e ON e.id = p.estadio_id
        LEFT JOIN arbitros a ON a.id = p.arbitro_id
        ORDER BY p.rodada, p.id
    """, engine)

    df_jogadores = pd.read_sql_query("""
        SELECT id, nome, numero, posicao, clube, rating, titular, foto_url
        FROM jogadores
        ORDER BY clube, titular DESC, numero
    """, engine)

    df_estadios = pd.read_sql_query("SELECT * FROM estadios ORDER BY cidade, nome", engine)
    df_arbitros = pd.read_sql_query("SELECT * FROM arbitros ORDER BY nome", engine)

    return df_clubes, df_partidas, df_jogadores, df_estadios, df_arbitros

def carregar_ids_favoritos():
    engine = get_engine()
    df_fav = pd.read_sql_query("SELECT partida_id FROM favoritos", engine)
    return set(df_fav["partida_id"].tolist()) if not df_fav.empty else set()

def favoritar_partida(partida_id: int):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO favoritos (partida_id) VALUES (:partida_id) ON CONFLICT (partida_id) DO NOTHING"),
            {"partida_id": partida_id},
        )

def desfavoritar_partida(partida_id: int):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM favoritos WHERE partida_id = :partida_id"), {"partida_id": partida_id})

try:
    garantir_schema()
    df_clubes, df_partidas, df_jogadores, df_estadios, df_arbitros = carregar_dados()
    favoritos_ids = carregar_ids_favoritos()
except Exception as e:
    st.error("Não foi possível conectar ao banco ou carregar os dados.")
    st.code(str(e))
    st.info("Confira DB_NAME, DB_USER e DB_PASSWORD no topo do arquivo dashboard_baianao.py.")
    st.stop()

map_escudos = dict(zip(df_clubes["nome"], df_clubes["escudo_url"]))
map_codigos = dict(zip(df_clubes["nome"], df_clubes["codigo"]))


def escudo_url(clube: str) -> str:
    url = map_escudos.get(clube)
    if isinstance(url, str) and url.strip():
        return url
    nome = str(clube).replace(" ", "+")
    return f"https://ui-avatars.com/api/?name={nome}&background=14532d&color=ffffff&size=128&bold=true"

def get_elenco(clube: str):
    elenco = df_jogadores[df_jogadores["clube"] == clube].copy()
    if elenco.empty:
        return [], []
    titulares = elenco[elenco["titular"] == 1].copy()
    reservas = elenco[elenco["titular"] == 0].copy()
    if len(titulares) < 11:
        faltam = 11 - len(titulares)
        titulares = pd.concat([titulares, reservas.head(faltam)])
        reservas = reservas.iloc[faltam:]
    return titulares.head(11).to_dict("records"), reservas.to_dict("records")

def media_rating(clube: str):
    elenco = df_jogadores[df_jogadores["clube"] == clube]
    if elenco.empty:
        return 6.5
    titulares = elenco[elenco["titular"] == 1]
    base = titulares if not titulares.empty else elenco
    return float(base["rating"].mean())

def calcular_classificacao():
    clubes = sorted(df_clubes["nome"].unique())
    tabela = {
        c: {"Clube": c, "J": 0, "V": 0, "E": 0, "D": 0, "GP": 0, "GC": 0, "SG": 0, "Pts": 0}
        for c in clubes
    }

    
    if "jogada" in df_partidas.columns:
        jogos_validos = df_partidas[df_partidas["jogada"].astype(bool)].copy()
    else:
        jogos_validos = df_partidas.copy()

    for _, row in jogos_validos.iterrows():
        casa, fora = row["clube_casa"], row["clube_fora"]
        gc, gf = int(row["gols_casa"]), int(row["gols_fora"])

        tabela[casa]["J"] += 1
        tabela[fora]["J"] += 1
        tabela[casa]["GP"] += gc
        tabela[casa]["GC"] += gf
        tabela[fora]["GP"] += gf
        tabela[fora]["GC"] += gc

        if gc > gf:
            tabela[casa]["V"] += 1
            tabela[fora]["D"] += 1
            tabela[casa]["Pts"] += 3
        elif gc < gf:
            tabela[fora]["V"] += 1
            tabela[casa]["D"] += 1
            tabela[fora]["Pts"] += 3
        else:
            tabela[casa]["E"] += 1
            tabela[fora]["E"] += 1
            tabela[casa]["Pts"] += 1
            tabela[fora]["Pts"] += 1

    df = pd.DataFrame(tabela.values())
    df["SG"] = df["GP"] - df["GC"]
    return df.sort_values(["Pts", "V", "SG", "GP"], ascending=False).reset_index(drop=True)

def ultimos_resultados(clube: str, n: int = 5):
    jogos = df_partidas[(df_partidas["clube_casa"] == clube) | (df_partidas["clube_fora"] == clube)].copy()
    if "jogada" in jogos.columns:
        jogos = jogos[jogos["jogada"].astype(bool)]
    jogos = jogos.tail(n)
    seq = []
    for _, row in jogos.iterrows():
        if row["clube_casa"] == clube:
            gm, gs = row["gols_casa"], row["gols_fora"]
        else:
            gm, gs = row["gols_fora"], row["gols_casa"]
        if gm > gs:
            seq.append("V")
        elif gm == gs:
            seq.append("E")
        else:
            seq.append("D")
    return seq

def prever_partida(casa: str, fora: str):
    rating_casa = media_rating(casa)
    rating_fora = media_rating(fora)
    tabela = calcular_classificacao()
    pts_map = dict(zip(tabela["Clube"], tabela["Pts"]))
    sg_map = dict(zip(tabela["Clube"], tabela["SG"]))

    forca_casa = rating_casa * 10 + pts_map.get(casa, 0) * 0.8 + sg_map.get(casa, 0) * 0.4 + 3.0
    forca_fora = rating_fora * 10 + pts_map.get(fora, 0) * 0.8 + sg_map.get(fora, 0) * 0.4
    diff = forca_casa - forca_fora

    prob_casa = 0.42 + diff / 100
    prob_fora = 0.34 - diff / 120
    prob_empate = 0.24 - abs(diff) / 250

    prob_casa = max(0.12, min(0.75, prob_casa))
    prob_fora = max(0.10, min(0.70, prob_fora))
    prob_empate = max(0.12, min(0.38, prob_empate))

    total = prob_casa + prob_empate + prob_fora
    prob_casa, prob_empate, prob_fora = prob_casa / total, prob_empate / total, prob_fora / total

    if prob_empate > 0.34 and abs(prob_casa - prob_fora) < 0.10:
        pred = "empate"
    else:
        pred = "casa" if prob_casa >= prob_fora else "fora"

    return {"casa": prob_casa, "empate": prob_empate, "fora": prob_fora, "predicao_final": pred}


def render_card_partida(row):
    casa = row["clube_casa"]
    fora = row["clube_fora"]
    estadio = f"{row['estadio_nome']} - {row['estadio_cidade']}" if pd.notna(row.get("estadio_nome")) else "Estádio a definir"
    arbitro = row["arbitro_nome"] if pd.notna(row.get("arbitro_nome")) else "Árbitro a definir"
    rodada = int(row["rodada"])
    jogada = bool(row.get("jogada", False))
    placar = f"{int(row['gols_casa'])} x {int(row['gols_fora'])}" if jogada else "A jogar"
    cor_placar = "#facc15" if jogada else "#93c5fd"

    html = f"""
    <div style="background:linear-gradient(135deg,#111827,#0b1220);padding:16px;border-radius:14px;border:1px solid rgba(255,255,255,0.08);color:white;font-family:Arial,sans-serif;min-height:154px;box-sizing:border-box;">
        <div style="font-size:12px;color:#a7f3d0;font-weight:800;margin-bottom:10px;">Rodada {rodada} • {row['fase']}</div>
        <div style="display:flex;align-items:center;justify-content:space-between;font-size:15px;font-weight:700;gap:10px;">
            <div style="display:flex;align-items:center;gap:8px;max-width:38%;">
                <img src="{escudo_url(casa)}" width="34" height="34" style="border-radius:50%;"><span>{casa}</span>
            </div>
            <div style="color:{cor_placar};font-weight:900;font-size:18px;">{placar}</div>
            <div style="display:flex;align-items:center;gap:8px;max-width:38%;justify-content:flex-end;">
                <span>{fora}</span><img src="{escudo_url(fora)}" width="34" height="34" style="border-radius:50%;">
            </div>
        </div>
        <div style="font-size:12px;color:#cbd5e1;margin-top:12px;">🏟️ {estadio}</div>
        <div style="font-size:12px;color:#cbd5e1;margin-top:4px;">⚖️ {arbitro}</div>
    </div>
    """
    components.html(html, height=180)

def selecionar_partida(casa: str, fora: str):
    atual = st.session_state.get("partida_escolhida")
    aberta = atual and atual.get("casa") == casa and atual.get("fora") == fora and st.session_state.get("mostrar_escalacao")
    if aberta:
        st.session_state["mostrar_escalacao"] = False
        st.session_state["formacao_casa"] = None
        st.session_state["formacao_fora"] = None
    else:
        st.session_state["partida_escolhida"] = {"casa": casa, "fora": fora}
        st.session_state["mostrar_escalacao"] = True
        st.session_state["formacao_casa"] = random.choice([[4,3,3], [4,4,2], [4,2,3,1], [3,5,2]])
        st.session_state["formacao_fora"] = random.choice([[4,3,3], [4,4,2], [4,2,3,1], [3,4,3]])

def render_lista_partidas(df_filtrado: pd.DataFrame, origem: str):
    global favoritos_ids
    if df_filtrado.empty:
        st.info("Nenhuma partida encontrada.")
        return

    rodadas = sorted(df_filtrado["rodada"].dropna().unique())
    for rodada in rodadas:
        st.markdown(f"### Rodada {int(rodada)}")
        jogos = df_filtrado[df_filtrado["rodada"] == rodada].reset_index(drop=True)
        for _, row in jogos.iterrows():
            partida_id = int(row["id"])
            casa = row["clube_casa"]
            fora = row["clube_fora"]
            c1, c2, c3 = st.columns([4.5, 1.2, 1.2])
            with c1:
                render_card_partida(row)
            with c2:
                atual = st.session_state.get("partida_escolhida")
                aberta = atual and atual.get("casa") == casa and atual.get("fora") == fora and st.session_state.get("mostrar_escalacao")
                texto = "❌ Fechar" if aberta else "📋 Escalação"
                if st.button(texto, key=f"{origem}_esc_{partida_id}"):
                    selecionar_partida(casa, fora)
                    st.rerun()
            with c3:
                eh_fav = partida_id in favoritos_ids
                texto = "★ Favorito" if eh_fav else "☆ Favoritar"
                if st.button(texto, key=f"{origem}_fav_{partida_id}"):
                    if eh_fav:
                        desfavoritar_partida(partida_id)
                    else:
                        favoritar_partida(partida_id)
                    st.cache_data.clear()
                    st.rerun()

def posicoes_time_por_formacao(formacao, lado="esquerda"):
    if lado == "esquerda":
        x_gk, x_inicio, x_fim = 10, 24, 52
    else:
        x_gk, x_inicio, x_fim = 90, 76, 48
    coords = [(x_gk, 50, "centro")]
    passo = (x_fim - x_inicio) / max(1, len(formacao) - 1)
    xs = [x_inicio + i * passo for i in range(len(formacao))]
    for linha_idx, qtd in enumerate(formacao):
        x = xs[linha_idx]
        ys = [50] if qtd == 1 else [18 + i * (64 / (qtd - 1)) for i in range(qtd)]
        for jogador_idx, y in enumerate(ys):
            setor = "centro" if qtd == 1 else ("direita" if jogador_idx == 0 else "esquerda" if jogador_idx == qtd - 1 else "centro")
            coords.append((x, y, setor))
    return coords

def posicao_curta(posicao: str, idx: int, setor: str = ""):
    pos = (posicao or "").lower()
    if "goleiro" in pos: return "GK"
    if "zagueiro" in pos: return "CB"
    if "lateral" in pos: return "RB" if setor == "direita" else "LB"
    if "meio" in pos: return "CM" if setor == "centro" else ("RM" if setor == "direita" else "LM")
    if "atac" in pos: return "ST" if setor == "centro" else ("RW" if setor == "direita" else "LW")
    return "PL"

def render_campo_duplo(casa: str, fora: str):
    titulares_casa, reservas_casa = get_elenco(casa)
    titulares_fora, reservas_fora = get_elenco(fora)
    if len(titulares_casa) < 11 or len(titulares_fora) < 11:
        st.warning("Não foi possível montar as escalações completas.")
        return

    formacao_casa = st.session_state.get("formacao_casa") or [4,3,3]
    formacao_fora = st.session_state.get("formacao_fora") or [4,3,3]

    st.markdown("---")
    c_title, c_btn = st.columns([7, 1])
    with c_title:
        st.subheader(f"📋 Escalações: {casa} x {fora}")
        st.caption(f"{casa}: {' - '.join(map(str, formacao_casa))} | {fora}: {' - '.join(map(str, formacao_fora))}")
    with c_btn:
        if st.button("❌ Fechar", key="fechar_escalacao_topo"):
            st.session_state["mostrar_escalacao"] = False
            st.rerun()

    pos_esq = posicoes_time_por_formacao(formacao_casa, "esquerda")
    pos_dir = posicoes_time_por_formacao(formacao_fora, "direita")

    def player_html(j, left, top, bg, idx, setor):
        foto = str(j.get("foto_url") or "").strip()
        numero = j.get("numero", "")
        nome = j.get("nome", "Jogador")
        rating = j.get("rating", "")
        pos = posicao_curta(j.get("posicao", ""), idx, setor)
        foto_html = f'<img src="{foto}" style="width:42px;height:42px;border-radius:50%;object-fit:cover;border:2px solid white;background:#0f172a;">' if foto else '<div style="width:42px;height:42px;border-radius:50%;border:2px solid white;background:#0f172a;"></div>'
        return f"""
        <div style="position:absolute;left:{left}%;top:{top}%;transform:translate(-50%,-50%);text-align:center;width:94px;font-family:Arial;color:white;z-index:6;">
            {foto_html}
            <div style="margin-top:5px;display:inline-flex;gap:5px;background:{bg};border-radius:999px;padding:4px 9px;font-size:11px;font-weight:900;"><span>#{numero}</span><span>{pos}</span></div>
            <div style="margin-top:5px;font-size:11px;background:rgba(3,7,18,.78);border-radius:9px;padding:4px 5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{nome}</div>
            <div style="margin-top:3px;display:inline-block;background:#0f172a;color:#facc15;border-radius:8px;padding:2px 6px;font-weight:900;font-size:11px;">★ {rating}</div>
        </div>
        """

    jogadores_html = ""
    for idx, (j, (left, top, setor)) in enumerate(zip(titulares_casa, pos_esq)):
        jogadores_html += player_html(j, left, top, "linear-gradient(135deg,#22c55e,#16a34a)", idx, setor)
    for idx, (j, (left, top, setor)) in enumerate(zip(titulares_fora, pos_dir)):
        jogadores_html += player_html(j, left, top, "linear-gradient(135deg,#f59e0b,#ef4444)", idx, setor)

    def reservas_html(reservas, lado):
        side = "left:12px;" if lado == "left" else "right:12px;"
        itens = ""
        for j in reservas[:5]:
            itens += f"<div style='display:flex;justify-content:space-between;background:rgba(255,255,255,.07);border-radius:9px;padding:6px 8px;margin-bottom:5px;font-size:11px;'><span><b>{j.get('numero')}</b> {j.get('nome')}</span><b style='color:#facc15;'>{j.get('rating')}</b></div>"
        return f"<div style='position:absolute;{side}bottom:12px;width:230px;background:rgba(0,0,0,.32);border:1px solid rgba(255,255,255,.12);border-radius:14px;padding:10px;color:white;font-family:Arial;z-index:7;'><b>Reservas</b><div style='height:8px;'></div>{itens}</div>"

    campo_html = f"""
    <div style="position:relative;width:100%;height:740px;border-radius:20px;overflow:hidden;background:repeating-linear-gradient(90deg,#14532d 0%,#14532d 7%,#166534 7%,#166534 14%);border:1px solid rgba(255,255,255,.12);box-shadow:0 12px 28px rgba(0,0,0,.25);">
        <div style="position:absolute;left:50%;top:0;width:2px;height:100%;background:rgba(255,255,255,.75);"></div>
        <div style="position:absolute;left:50%;top:50%;width:110px;height:110px;border:2px solid rgba(255,255,255,.75);border-radius:50%;transform:translate(-50%,-50%);"></div>
        <div style="position:absolute;left:0;top:22%;width:15%;height:56%;border:2px solid rgba(255,255,255,.75);border-left:none;"></div>
        <div style="position:absolute;right:0;top:22%;width:15%;height:56%;border:2px solid rgba(255,255,255,.75);border-right:none;"></div>
        <div style="position:absolute;left:1%;top:2%;background:rgba(6,18,28,.75);padding:7px 12px;border-radius:10px;font-weight:900;color:white;z-index:8;">{casa}</div>
        <div style="position:absolute;right:1%;top:2%;background:rgba(6,18,28,.75);padding:7px 12px;border-radius:10px;font-weight:900;color:white;z-index:8;">{fora}</div>
        {jogadores_html}
        {reservas_html(reservas_casa, 'left')}
        {reservas_html(reservas_fora, 'right')}
    </div>
    """
    components.html(campo_html, height=760, scrolling=False)


if st.session_state["partida_escolhida"] and st.session_state["mostrar_escalacao"]:
    render_campo_duplo(st.session_state["partida_escolhida"]["casa"], st.session_state["partida_escolhida"]["fora"])

st.title("🏆 Baianão")
st.caption("Dashboard interativo do Campeonato Baiano: jogos, classificação, clubes, elenco e previsão.")

abas = st.tabs(["Jogos", "Favoritos", "Tabela", "Clubes", "Estatísticas", "Previsão", "Estádios", "Jogadores","Admin"])

with abas[0]:
    st.subheader("⚽ Jogos do Baianão")
    rodadas = sorted(df_partidas["rodada"].unique())
    rodada_sel = st.selectbox("Filtrar por rodada", ["Todas"] + [int(r) for r in rodadas], key="filtro_rodada_jogos")
    df_jogos = df_partidas if rodada_sel == "Todas" else df_partidas[df_partidas["rodada"] == rodada_sel]
    render_lista_partidas(df_jogos, "jogos")

with abas[1]:
    st.subheader("⭐ Favoritos")
    favoritos_ids = carregar_ids_favoritos()
    if not favoritos_ids:
        st.info("Você ainda não favoritou nenhuma partida.")
    else:
        render_lista_partidas(df_partidas[df_partidas["id"].isin(list(favoritos_ids))], "favoritos")

with abas[2]:
    st.subheader("📊 Classificação")
    tabela = calcular_classificacao()
    tabela_show = tabela.copy()
    tabela_show.insert(0, "Pos", range(1, len(tabela_show) + 1))
    st.dataframe(tabela_show[["Pos", "Clube", "Pts", "J", "V", "E", "D", "GP", "GC", "SG"]], use_container_width=True, hide_index=True)
    st.caption("Critérios usados no painel: pontos, vitórias, saldo e gols pró.")
    st.markdown("### Zona de decisão")
    c1, c2 = st.columns(2)
    with c1:
        st.success("Semifinalistas provisórios")
        st.dataframe(tabela_show.head(4)[["Pos", "Clube", "Pts"]], use_container_width=True, hide_index=True)
    with c2:
        st.warning("Zona de rebaixamento provisória")
        st.dataframe(tabela_show.tail(2)[["Pos", "Clube", "Pts"]], use_container_width=True, hide_index=True)

with abas[3]:
    st.subheader("🛡️ Clubes")
    cols = st.columns(5)
    for idx, (_, row) in enumerate(df_clubes.iterrows()):
        with cols[idx % 5]:
            st.markdown(f"""
            <div class="custom-card">
                <img src="{escudo_url(row['nome'])}" width="72" height="72" style="border-radius:50%;">
                <div style="margin-top:8px;font-weight:800;">{row['nome']}</div>
                <div style="font-size:12px;color:#cbd5e1;">{row['cidade']}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Fundo: {row['nome']}", key=f"fundo_{row['nome']}"):
                st.session_state["fundo_clube"] = row["nome"]
                st.rerun()
    if st.button("Restaurar fundo padrão"):
        st.session_state["fundo_clube"] = None
        st.rerun()

with abas[4]:
    st.subheader("📈 Estatísticas comparativas")
    clubes_validos = sorted(df_clubes["nome"].unique())
    c1, c2 = st.columns(2)
    with c1:
        clube_a = st.selectbox("Clube A", clubes_validos, key="stats_a")
    with c2:
        clube_b = st.selectbox("Clube B", clubes_validos, index=1 if len(clubes_validos) > 1 else 0, key="stats_b")

    if clube_a == clube_b:
        st.info("Escolha dois clubes diferentes.")
    else:
        tab = calcular_classificacao().set_index("Clube")
        a = tab.loc[clube_a]
        b = tab.loc[clube_b]
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.metric(f"Pontos {clube_a}", int(a["Pts"]))
        with m2: st.metric(f"Pontos {clube_b}", int(b["Pts"]))
        with m3: st.metric(f"Rating {clube_a}", f"{media_rating(clube_a):.1f}")
        with m4: st.metric(f"Rating {clube_b}", f"{media_rating(clube_b):.1f}")

        st.markdown("### Comparativo")
        df_comp = pd.DataFrame({
            "Indicador": ["Vitórias", "Empates", "Derrotas", "Gols Pró", "Gols Contra", "Saldo"],
            clube_a: [a["V"], a["E"], a["D"], a["GP"], a["GC"], a["SG"]],
            clube_b: [b["V"], b["E"], b["D"], b["GP"], b["GC"], b["SG"]],
        })
        st.dataframe(df_comp, use_container_width=True, hide_index=True)

        st.markdown("### Confrontos diretos na tabela atual")
        h2h = df_partidas[((df_partidas["clube_casa"] == clube_a) & (df_partidas["clube_fora"] == clube_b)) | ((df_partidas["clube_casa"] == clube_b) & (df_partidas["clube_fora"] == clube_a))].copy()
        if "jogada" in h2h.columns:
            h2h["Status"] = h2h["jogada"].map({True: "Jogada", False: "A jogar"})
        if h2h.empty:
            st.info("Não há confronto direto registrado entre os dois na tabela atual.")
        else:
            cols_h2h = ["rodada", "clube_casa", "gols_casa", "gols_fora", "clube_fora", "fase"]
            if "Status" in h2h.columns:
                cols_h2h.append("Status")
            st.dataframe(h2h[cols_h2h], use_container_width=True, hide_index=True)
            
with abas[5]:
    st.subheader("🔮 Previsão")
    clubes_validos = sorted(df_clubes["nome"].unique())
    c1, c2 = st.columns(2)
    with c1:
        casa = st.selectbox("Mandante", clubes_validos, key="pred_casa")
    with c2:
        fora = st.selectbox("Visitante", clubes_validos, index=1 if len(clubes_validos) > 1 else 0, key="pred_fora")

    if casa == fora:
        st.info("Escolha clubes diferentes.")
    elif st.button("Gerar previsão"):
        probs = prever_partida(casa, fora)
        st.markdown(f"### {casa} x {fora}")
        p1, p2, p3 = st.columns(3)
        with p1: st.metric("Vitória mandante", f"{probs['casa'] * 100:.1f}%")
        with p2: st.metric("Empate", f"{probs['empate'] * 100:.1f}%")
        with p3: st.metric("Vitória visitante", f"{probs['fora'] * 100:.1f}%")
        mapa = {"casa": f"✅ Tendência: {casa}", "empate": "🤝 Tendência: empate", "fora": f"✅ Tendência: {fora}"}
        st.success(mapa[probs["predicao_final"]])
        df_probs = pd.DataFrame({"Resultado": ["Mandante", "Empate", "Visitante"], "Probabilidade": [probs["casa"], probs["empate"], probs["fora"]]})
        st.bar_chart(df_probs.set_index("Resultado"))

with abas[6]:
    st.subheader("🏟️ Estádios")
    cols = st.columns(2)
    for i, (_, row) in enumerate(df_estadios.iterrows()):
        with cols[i % 2]:
            if isinstance(row.get("foto_url"), str) and row["foto_url"]:
                st.image(row["foto_url"], use_container_width=True)
            st.markdown(f"**{row['nome']}**")
            st.write(f"{row['cidade']} - {row['estado']}")
            st.markdown("---")


with abas[7]:
    st.subheader("👥 Jogadores")
    clube_sel = st.selectbox("Clube", sorted(df_jogadores["clube"].unique()))
    elenco = df_jogadores[df_jogadores["clube"] == clube_sel].copy()
    elenco = elenco.rename(columns={"nome": "Jogador", "numero": "Número", "posicao": "Posição", "rating": "Nota", "titular": "Titular"})
    elenco["Titular"] = elenco["Titular"].map({1: "Sim", 0: "Reserva"})
    st.dataframe(elenco[["Número", "Jogador", "Posição", "Nota", "Titular"]], use_container_width=True, hide_index=True)


with abas[8]:
    st.subheader("⚙️ Administração")

    if not IS_ADMIN:
        st.warning("Apenas usuários administradores podem acessar esta área.")
    else:
        st.caption("Área simples para atualizar placares das partidas.")

        partida_opcoes = []
        partida_map = {}
        for _, row in df_partidas.iterrows():
            label = f"ID {int(row['id'])} | Rodada {int(row['rodada'])} | {row['clube_casa']} x {row['clube_fora']}"
            partida_opcoes.append(label)
            partida_map[label] = row

        partida_label = st.selectbox("Partida", partida_opcoes)
        partida = partida_map[partida_label]

        c1, c2 = st.columns(2)
        with c1:
            gols_casa = st.number_input(f"Gols {partida['clube_casa']}", min_value=0, max_value=20, value=int(partida["gols_casa"]), step=1)
        with c2:
            gols_fora = st.number_input(f"Gols {partida['clube_fora']}", min_value=0, max_value=20, value=int(partida["gols_fora"]), step=1)

        if st.button("Salvar placar"):
            engine = get_engine()
            with engine.begin() as conn:
                conn.execute(
                    text("UPDATE partidas SET gols_casa = :gc, gols_fora = :gf WHERE id = :id"),
                    {"gc": int(gols_casa), "gf": int(gols_fora), "id": int(partida["id"])},
                )
            st.cache_data.clear()
            st.success("Placar atualizado com sucesso.")
            st.rerun()
            