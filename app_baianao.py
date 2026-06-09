# -*- coding: utf-8 -*-
import itertools
import random
import time
import requests
import psycopg2

#API_KEY = "123"
#BASE_API = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}"

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "estadual",
    "user": "postgres",
    "password": "admin",
    "client_encoding": "utf8",
}

clubes = [
    ("Bahia", "bah", "Salvador"),
    ("Vitória", "vit", "Salvador"),
    ("Atlético de Alagoinhas", "atl", "Alagoinhas"),
    ("Bahia de Feira", "bfe", "Feira de Santana"),
    ("Barcelona de Ilhéus", "bar", "Ilhéus"),
    ("Galícia", "gal", "Salvador"),
    ("Jacuipense", "jac", "Riachão do Jacuípe"),
    ("Jequié", "jeq", "Jequié"),
    ("Juazeirense", "jua", "Juazeiro"),
    ("Porto", "por", "Porto Seguro"),
]

estadios = [
    ("Arena Fonte Nova", "Salvador", "Bahia", "https://upload.wikimedia.org/wikipedia/commons/7/7e/Itaipava_Arena_Fonte_Nova.jpg"),
    ("Estádio Manoel Barradas", "Salvador", "Bahia", "https://upload.wikimedia.org/wikipedia/commons/4/4b/Barrad%C3%A3o_EC_Vit%C3%B3ria.jpg"),
    ("Estádio Antônio Carneiro", "Alagoinhas", "Bahia", None),
    ("Arena Cajueiro", "Feira de Santana", "Bahia", None),
    ("Estádio Mário Pessoa", "Ilhéus", "Bahia", None),
    ("Estádio Eliel Martins", "Riachão do Jacuípe", "Bahia", None),
    ("Estádio Waldomiro Borges", "Jequié", "Bahia", None),
    ("Estádio Adauto Moraes", "Juazeiro", "Bahia", None),
    ("Estádio Agnaldo Bento", "Porto Seguro", "Bahia", None),
]

arbitros = [
    ("Marielson Alves Silva", "Bahia"),
    ("Diego Pombo Lopez", "Bahia"),
    ("Bruno Pereira Vasconcelos", "Bahia"),
    ("Reinaldo Silva de Santana", "Bahia"),
    ("Ricarle Gustavo Gonçalves Batista", "Bahia"),
    ("Moilson Ferreira Silva", "Bahia"),
    ("Ramon Diego Rodrigues Casais", "Bahia"),
    ("Gleidson Santos Oliveira", "Bahia"),
]

# Elencos fictícios/base para demonstração. Você pode trocar depois por nomes reais.
elencos_especiais = {
    "Bahia": [
        ("Marcos Felipe", 1, "Goleiro"),
        ("Gilberto", 2, "Lateral"),
        ("Kanu", 3, "Zagueiro"),
        ("David Duarte", 4, "Zagueiro"),
        ("Rezende", 5, "Meio-campo"),
        ("Luciano Juba", 6, "Lateral"),
        ("Ademir", 7, "Atacante"),
        ("Cauly", 8, "Meio-campo"),
        ("Everaldo", 9, "Atacante"),
        ("Éverton Ribeiro", 10, "Meio-campo"),
        ("Biel", 11, "Atacante"),
        ("Danilo Fernandes", 12, "Goleiro"),
        ("Santiago Arias", 13, "Lateral"),
        ("Thaciano", 16, "Meio-campo"),
        ("Rafael Ratão", 21, "Atacante"),
    ],
    "Vitória": [
        ("Lucas Arcanjo", 1, "Goleiro"),
        ("Raúl Cáceres", 2, "Lateral"),
        ("Camutanga", 3, "Zagueiro"),
        ("Wagner Leonardo", 4, "Zagueiro"),
        ("Willian Oliveira", 5, "Meio-campo"),
        ("PK", 6, "Lateral"),
        ("Osvaldo", 7, "Atacante"),
        ("Matheuzinho", 8, "Meio-campo"),
        ("Alerrandro", 9, "Atacante"),
        ("Jean Mota", 10, "Meio-campo"),
        ("Iury Castilho", 11, "Atacante"),
        ("Muriel", 12, "Goleiro"),
        ("Bruno Uvini", 13, "Zagueiro"),
        ("Dudu", 15, "Meio-campo"),
        ("Everaldo", 17, "Atacante"),
    ],
}

MAPA_CLUBES_API = {
    "Bahia": "Bahia",
    "Vitória": "Vitoria",
    "Atlético de Alagoinhas": "Atletico Alagoinhas",
    "Bahia de Feira": "Bahia de Feira",
    "Barcelona de Ilhéus": "Barcelona de Ilheus",
    "Galícia": "Galicia",
    "Jacuipense": "Jacuipense",
    "Jequié": "Jequie",
    "Juazeirense": "Juazeirense",
    "Porto": "Porto BA",
}


def nome_clube_api(nome: str) -> str:
    return MAPA_CLUBES_API.get(nome, nome)


def avatar_url(nome: str) -> str:
    nome = str(nome).replace(" ", "+")
    return f"https://ui-avatars.com/api/?name={nome}&background=1f2937&color=ffffff&size=128"


def escudo_avatar_url(nome: str) -> str:
    nome = str(nome).replace(" ", "+")
    return f"https://ui-avatars.com/api/?name={nome}&background=14532d&color=ffffff&size=128&bold=true"


def buscar_foto_jogador_api(nome_jogador: str, clube: str):
    try:
        response = requests.get(
            f"{BASE_API}/searchplayers.php",
            params={"p": nome_jogador},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        players = data.get("player") if data else None

        if not players:
            return None

        clube_api = nome_clube_api(clube).lower()

        for p in players:
            equipe = (p.get("strTeam") or "").lower()
            thumb = p.get("strThumb") or p.get("strCutout") or p.get("strRender")
            if thumb and clube_api in equipe:
                return thumb

        for p in players:
            thumb = p.get("strThumb") or p.get("strCutout") or p.get("strRender")
            if thumb:
                return thumb

        return None
    except Exception:
        return None


def gerar_tabela_turno_unico(lista_clubes):
    """
    Gera todos contra todos em turno único.
    Com 10 clubes: 45 partidas. A rodada é distribuída por blocos de 5 jogos.
    """
    nomes = [c[0] for c in lista_clubes]
    confrontos = list(itertools.combinations(nomes, 2))
    random.seed(42)
    random.shuffle(confrontos)

    partidas = []
    for idx, (casa, fora) in enumerate(confrontos):
        rodada = (idx // 5) + 1
        # Alterna mando para não deixar sempre o primeiro clube como casa.
        if idx % 2 == 0:
            partidas.append((rodada, casa, fora))
        else:
            partidas.append((rodada, fora, casa))
    return partidas


def gerar_elenco_generico(clube: str):
    return [
        (f"{clube} Goleiro", 1, "Goleiro"),
        (f"{clube} Lateral D", 2, "Lateral"),
        (f"{clube} Zagueiro 1", 3, "Zagueiro"),
        (f"{clube} Zagueiro 2", 4, "Zagueiro"),
        (f"{clube} Volante", 5, "Meio-campo"),
        (f"{clube} Lateral E", 6, "Lateral"),
        (f"{clube} Ponta D", 7, "Atacante"),
        (f"{clube} Meia", 8, "Meio-campo"),
        (f"{clube} Centroavante", 9, "Atacante"),
        (f"{clube} Camisa 10", 10, "Meio-campo"),
        (f"{clube} Ponta E", 11, "Atacante"),
        (f"{clube} Reserva GOL", 12, "Goleiro"),
        (f"{clube} Reserva ZAG", 13, "Zagueiro"),
        (f"{clube} Reserva MEI", 14, "Meio-campo"),
        (f"{clube} Reserva ATA", 15, "Atacante"),
    ]


conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS favoritos CASCADE")
cursor.execute("DROP TABLE IF EXISTS jogadores CASCADE")
cursor.execute("DROP TABLE IF EXISTS partidas CASCADE")
cursor.execute("DROP TABLE IF EXISTS arbitros CASCADE")
cursor.execute("DROP TABLE IF EXISTS estadios CASCADE")
cursor.execute("DROP TABLE IF EXISTS clubes CASCADE")

cursor.execute("""
CREATE TABLE clubes (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome TEXT NOT NULL,
    codigo TEXT NOT NULL,
    cidade TEXT NOT NULL,
    escudo_url TEXT
)
""")

cursor.execute("""
CREATE TABLE estadios (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome TEXT NOT NULL,
    cidade TEXT NOT NULL,
    estado TEXT NOT NULL,
    foto_url TEXT
)
""")

cursor.execute("""
CREATE TABLE arbitros (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome TEXT NOT NULL,
    federacao TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE partidas (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    clube_casa TEXT NOT NULL,
    clube_fora TEXT NOT NULL,
    gols_casa INTEGER DEFAULT 0,
    gols_fora INTEGER DEFAULT 0,
    rodada INTEGER NOT NULL,
    fase TEXT NOT NULL DEFAULT 'Primeira fase',
    estadio_id INTEGER,
    arbitro_id INTEGER,
    CONSTRAINT fk_estadio FOREIGN KEY (estadio_id) REFERENCES estadios(id),
    CONSTRAINT fk_arbitro FOREIGN KEY (arbitro_id) REFERENCES arbitros(id)
)
""")

cursor.execute("""
CREATE TABLE jogadores (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome TEXT NOT NULL,
    numero INTEGER NOT NULL,
    posicao TEXT NOT NULL,
    clube TEXT NOT NULL,
    rating REAL NOT NULL,
    titular INTEGER NOT NULL,
    foto_url TEXT
)
""")

cursor.execute("""
CREATE TABLE favoritos (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    partida_id INTEGER NOT NULL UNIQUE,
    CONSTRAINT fk_partida_favorita FOREIGN KEY (partida_id) REFERENCES partidas(id) ON DELETE CASCADE
)
""")

for nome, codigo, cidade in clubes:
    cursor.execute(
        "INSERT INTO clubes (nome, codigo, cidade, escudo_url) VALUES (%s, %s, %s, %s)",
        (nome, codigo, cidade, escudo_avatar_url(nome)),
    )

for estadio in estadios:
    cursor.execute("""
        INSERT INTO estadios (nome, cidade, estado, foto_url)
        VALUES (%s, %s, %s, %s)
    """, estadio)

for arbitro in arbitros:
    cursor.execute("""
        INSERT INTO arbitros (nome, federacao)
        VALUES (%s, %s)
    """, arbitro)

cursor.execute("SELECT id FROM estadios ORDER BY id")
estadios_ids = [row[0] for row in cursor.fetchall()]

cursor.execute("SELECT id FROM arbitros ORDER BY id")
arbitros_ids = [row[0] for row in cursor.fetchall()]

partidas_geradas = gerar_tabela_turno_unico(clubes)

for idx, (rodada, casa, fora) in enumerate(partidas_geradas):
    estadio_id = estadios_ids[idx % len(estadios_ids)]
    arbitro_id = arbitros_ids[idx % len(arbitros_ids)]

    cursor.execute("""
        INSERT INTO partidas (
            clube_casa, clube_fora, gols_casa, gols_fora, rodada, fase, estadio_id, arbitro_id
        )
        VALUES (%s, %s, 0, 0, %s, 'Primeira fase', %s, %s)
    """, (casa, fora, rodada, estadio_id, arbitro_id))

cursor.execute("SELECT nome FROM clubes ORDER BY nome")
clubes_db = [row[0] for row in cursor.fetchall()]

for clube in clubes_db:
    jogadores = elencos_especiais.get(clube, gerar_elenco_generico(clube))

    for idx, (nome, numero, posicao) in enumerate(jogadores):
        titular = 1 if idx < 11 else 0

        if clube in ["Bahia", "Vitória"]:
            rating = round(random.uniform(7.0, 8.7), 1)
        elif clube in ["Jacuipense", "Juazeirense", "Atlético de Alagoinhas"]:
            rating = round(random.uniform(6.4, 7.8), 1)
        else:
            rating = round(random.uniform(6.0, 7.4), 1)

        cursor.execute("""
            INSERT INTO jogadores (nome, numero, posicao, clube, rating, titular, foto_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (nome, numero, posicao, clube, rating, titular, None))

conn.commit()

print("Buscando fotos dos jogadores na API...")
cursor.execute("SELECT id, nome, clube, foto_url FROM jogadores")
todos_jogadores = cursor.fetchall()

for jogador_id, nome_jogador, clube, foto_atual in todos_jogadores:
    if foto_atual:
        continue

    foto = buscar_foto_jogador_api(nome_jogador, clube)
    if not foto:
        foto = avatar_url(nome_jogador)

    cursor.execute(
        "UPDATE jogadores SET foto_url = %s WHERE id = %s",
        (foto, jogador_id),
    )
    print(f"✔ {clube} - {nome_jogador}")
    time.sleep(0.10)

conn.commit()
cursor.close()
conn.close()

print("Banco PostgreSQL do Baianão criado com sucesso.")
