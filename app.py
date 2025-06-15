from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
API_HOST = "v3.football.api-sports.io"

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
    odd_fav = 1.75  # aqui você pode integrar busca de odds reais numa próxima etapa

    # Simulação da análise SRP usando prompt no ChatGPT
    prompt = f"""
Você é o ANTIZEBRA PRO MAX, use análise SRP para partida entre {timeA} vs {timeB}, odd do favorito: {odd_fav}
... [seu prompt otimizado aqui] ...
"""
    # Supondo que você chame o ChatGPT aqui e obtenha `resposta`
    resposta = f"(Análise simulada com odd {odd_fav})"

    return jsonify({"analise": resposta})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
