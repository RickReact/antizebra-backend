
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

# Endpoint 1 – Ligas com jogos na data
@app.route("/ligas-por-data", methods=["POST"])
def ligas_por_data():
    data = request.get_json()
    data_escolhida = data.get("data")
    if not data_escolhida:
        return jsonify({"erro": "Data não fornecida."}), 400

    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    headers = {
        "x-rapidapi-host": "api-football-v1.p.rapidapi.com",
        "x-rapidapi-key": RAPIDAPI_KEY
    }
    response = requests.get(url, headers=headers, params={"date": data_escolhida, "season": "2024"})

    if response.status_code != 200:
        return jsonify({"erro": "Erro ao buscar jogos."}), 500

    jogos = response.json().get("response", [])
    ligas_unicas = {}
    for jogo in jogos:
        liga_id = jogo["league"]["id"]
        liga_nome = jogo["league"]["name"]
        ligas_unicas[liga_id] = liga_nome

    lista_ligas = [{"id": k, "nome": v} for k, v in ligas_unicas.items()]
    return jsonify({"ligas": lista_ligas})


# Endpoint 2 – Jogos por liga na data
@app.route("/jogos-por-liga", methods=["POST"])
def jogos_por_liga():
    data = request.get_json()
    data_selecionada = data.get("data")
    liga_id = data.get("liga_id")

    if not data_selecionada or not liga_id:
        return jsonify({"erro": "Data ou liga não fornecida."}), 400

    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    headers = {
        "x-rapidapi-host": "api-football-v1.p.rapidapi.com",
        "x-rapidapi-key": RAPIDAPI_KEY
    }
    response = requests.get(url, headers=headers, params={"date": data_selecionada, "league": liga_id, "season": "2024"})

    if response.status_code != 200:
        return jsonify({"erro": "Erro ao buscar jogos."}), 500

    data = response.json().get("response", [])
    jogos = [
        {
            "time_casa": j["teams"]["home"]["name"],
            "time_fora": j["teams"]["away"]["name"],
            "data": j["fixture"]["date"]
        }
        for j in data
    ]

    return jsonify({"jogos": jogos})


# Endpoint 3 – Análise do jogo
@app.route("/analise-jogo", methods=["POST"])
def analise_jogo():
    data = request.get_json()
    time_a = data.get("time_a")
    time_b = data.get("time_b")
    data_jogo = data.get("data")

    if not time_a or not time_b:
        return jsonify({"erro": "Dados do jogo incompletos."}), 400

    prompt = f"""
Você é o ANTIZEBRA PRO MAX – analista técnico de apostas esportivas.

Analise a seguinte partida: {time_a} x {time_b} – {data_jogo}

REGRAS:
1. Só analise se houver favorito técnico (odd entre 1.01 e 1.95).
2. Aplique os critérios do método ANTIZEBRA (SRP).
3. Classifique o risco: Muito Baixo, Baixo, Moderado, Alto, Muito Alto.
4. Sugira uma aposta segura (caso exista).
5. Informe a stake recomendada:

Muito Baixo → 5%
Baixo → 4%
Moderado → 2.5%
Alto → 1%
Muito Alto → ❌ Não apostar

Resultado:
- Favorito: [nome e odd]
- Risco: [classificação]
- Stake: [%]
- Comentário técnico: [breve análise]
"""

    try:
        import openai
        openai.api_key = os.getenv("OPENAI_API_KEY")
        resposta = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800
        )
        resultado = resposta.choices[0].message["content"]
        return jsonify({"analise": resultado})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
