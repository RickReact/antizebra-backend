
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import openai

app = Flask(__name__)
CORS(app)

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
API_HOST = "api-football-v1.p.rapidapi.com"

openai.api_key = OPENAI_API_KEY

@app.route("/ligas-por-data", methods=["POST"])
def ligas_por_data():
    data = request.get_json().get("data")
    if not data:
        return jsonify({"erro": "Data não informada"}), 400

    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures"
    params = {"date": data}
    headers = {"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": API_HOST}

    r = requests.get(url, headers=headers, params=params)
    if r.status_code != 200:
        return jsonify({"erro": "Erro ao buscar partidas"}), 500

    ligas = {}
    for item in r.json().get("response", []):
        league = item["league"]
        ligas[league["id"]] = {"id": league["id"], "nome": league["name"], "pais": league["country"]}

    return jsonify({"ligas": list(ligas.values())})

@app.route("/jogos-por-liga", methods=["POST"])
def jogos_por_liga():
    req = request.get_json()
    data = req.get("data")
    liga = req.get("liga_id")
    if not data or not liga:
        return jsonify({"erro": "Data ou ID da liga não fornecidos"}), 400

    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures"
    params = {"date": data, "league": liga, "season": "2025"}
    headers = {"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": API_HOST}

    r = requests.get(url, headers=headers, params=params)
    if r.status_code != 200:
        return jsonify({"erro": "Erro na API de partidas"}), 500

    resp = r.json().get("response", [])
    if not resp:
        return jsonify({"jogos": []})

    jogos = [{
        "fixture_id": j["fixture"]["id"],
        "time_casa": j["teams"]["home"]["name"],
        "time_fora": j["teams"]["away"]["name"],
        "data": j["fixture"]["date"]
    } for j in resp]

    return jsonify({"jogos": jogos})

@app.route("/analise-jogo", methods=["POST"])
def analise_jogo():
    req = request.get_json()
    fid = req.get("fixture_id")
    if not fid:
        return jsonify({"erro": "ID da partida não fornecido"}), 400

    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures"
    params = {"id": fid}
    headers = {"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": API_HOST}

    r = requests.get(url, headers=headers, params=params)
    if r.status_code != 200 or not r.json().get("response"):
        return jsonify({"erro": "Erro ao buscar partida por ID"}), 500

    jogo = r.json()["response"][0]
    timeA = jogo["teams"]["home"]["name"]
    timeB = jogo["teams"]["away"]["name"]
    data_jogo = jogo["fixture"]["date"]
    odd_favorito = 1.80  # Simulado

    prompt = f'''
Você é o ANTIZEBRA PRO MAX – analista técnico de apostas.

🎯 Jogo: {timeA} x {timeB} – {data_jogo}
⭐ Favorito simulado: {timeA if odd_favorito <= 1.95 else timeB} (odd {odd_favorito})

Avalie com base no método SRP se há risco de zebra, classifique o risco, e defina a stake ideal.

Stake máxima: 5%. Não recomende aposta se o risco for Muito Alto.
'''

    try:
        resposta = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=800
        )
        analise = resposta.choices[0].message.content
    except Exception as e:
        return jsonify({"erro": f"Erro ao gerar análise: {str(e)}"}), 500

    return jsonify({"analise": analise})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
