from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
API_HOST = "api-football-v1.p.rapidapi.com"

@app.route("/ligas-por-data", methods=["POST"])
def ligas_por_data():
    data = request.get_json().get("data")
    if not data:
        return jsonify({"erro": "Data não informada"}), 400

    url = f"https://{API_HOST}/v3/fixtures"
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

    try:
        ano = datetime.strptime(data, "%Y-%m-%d").year
    except ValueError:
        return jsonify({"erro": "Data em formato inválido"}), 400

    url = f"https://{API_HOST}/v3/fixtures"
    params = {"date": data, "league": liga, "season": str(ano)}
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

    url = f"https://{API_HOST}/v3/odds"
    headers = {"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": API_HOST}
    params = {"fixture": fid}

    odds_resp = requests.get(url, headers=headers, params=params)
    if odds_resp.status_code != 200 or not odds_resp.json().get("response"):
        return jsonify({"erro": "Odds não disponíveis para este jogo"}), 404

    bookmakers = odds_resp.json()["response"][0].get("bookmakers", [])
    odd_fav = None
    odd_btts = None
    odd_ht = None

    for bookmaker in bookmakers:
        for bet in bookmaker.get("bets", []):
            if bet.get("name") == "Match Winner":
                for val in bet.get("values", []):
                    odd = val.get("odd")
                    if odd and float(odd) < 1.96:
                        odd_fav = float(odd)
            elif bet.get("name") == "Both Teams To Score" and odd_btts is None:
                for val in bet.get("values", []):
                    if val.get("value") == "Yes":
                        odd_btts = float(val.get("odd", 0))
            elif bet.get("name") == "1st Half Winner" and odd_ht is None:
                for val in bet.get("values", []):
                    odd = val.get("odd")
                    if odd and float(odd) < 1.96:
                        odd_ht = float(odd)

    if not odd_fav:
        return jsonify({"erro": "❌ Jogo inapto para análise. Nenhum favorito claro identificado."})

    risco = 20
    if odd_fav <= 1.25: risco += 1
    elif odd_fav <= 1.50: risco += 3
    else: risco += 5

    if odd_btts and odd_btts >= 2.00: risco += 3
    if odd_ht and odd_ht < 1.95: risco -= 2

    if risco <= 39:
        nivel = "🎯 Muito Baixo"
        stake = "5%"
    elif risco <= 56:
        nivel = "🟢 Baixo"
        stake = "4%"
    elif risco <= 74:
        nivel = "🟡 Moderado"
        stake = "2.5%"
    elif risco <= 91:
        nivel = "🔴 Alto"
        stake = "1%"
    else:
        nivel = "🚫 Muito Alto"
        stake = "0%"

    resumo = f"""
🎯 Fixture ID: {fid}
⭐ Odd do favorito: {odd_fav}
⚙️ Odd BTTS: {odd_btts}
⏱️ Odd vitória 1º tempo: {odd_ht}

📊 Classificação de Risco: {nivel}
💰 Stake Recomendada: {stake}
"""

    return jsonify({"analise": resumo.strip()})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
