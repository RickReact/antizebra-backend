from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
API_HOST = "api-football-v1.p.rapidapi.com"
HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": API_HOST
}

def get_fixtures(date):
    url = f"https://{API_HOST}/v3/fixtures"
    r = requests.get(url, headers=HEADERS, params={"date": date})
    return r.json().get("response", []) if r.status_code == 200 else []

@app.route("/ligas-por-data", methods=["POST"])
def ligas_por_data():
    data = request.get_json().get("data")
    if not data:
        return jsonify({"erro": "Data não informada"}), 400

    ligas = {}
    for item in get_fixtures(data):
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

    r = requests.get(f"https://{API_HOST}/v3/fixtures", headers=HEADERS, params={
        "date": data, "league": liga, "season": datetime.strptime(data, "%Y-%m-%d").year
    })

    if r.status_code != 200:
        return jsonify({"erro": "Erro na API de partidas"}), 500

    jogos = [{
        "fixture_id": j["fixture"]["id"],
        "time_casa": j["teams"]["home"]["name"],
        "time_fora": j["teams"]["away"]["name"],
        "data": j["fixture"]["date"]
    } for j in r.json().get("response", [])]

    return jsonify({"jogos": jogos})

@app.route("/analise-jogo", methods=["POST"])
def analise_jogo():
    fid = request.get_json().get("fixture_id")
    if not fid:
        return jsonify({"erro": "ID da partida não fornecido"}), 400

    fixture_url = f"https://{API_HOST}/v3/fixtures"
    odds_url = f"https://{API_HOST}/v3/odds"
    r1 = requests.get(fixture_url, headers=HEADERS, params={"id": fid})
    r2 = requests.get(odds_url, headers=HEADERS, params={"fixture": fid})

    if r1.status_code != 200 or r2.status_code != 200:
        return jsonify({"erro": "Erro ao buscar dados da partida"}), 500

    fixture = r1.json()["response"][0]
    odds_data = r2.json()["response"]
    home = fixture["teams"]["home"]
    away = fixture["teams"]["away"]
    season = fixture["league"]["season"]

    odd_fav = None
    odd_btts = None
    odd_ht = None
    favorito = "Indefinido"

    try:
        for bet in odds_data[0]["bookmakers"][0]["bets"]:
            if bet["name"] == "Match Winner":
                for val in bet["values"]:
                    if float(val["odd"]) < 1.96:
                        odd_fav = float(val["odd"])
                        favorito = val["value"]
            if bet["name"] == "Both Teams To Score":
                for val in bet["values"]:
                    if val["value"] == "Yes":
                        odd_btts = float(val["odd"])
            if bet["name"] == "1st Half Winner":
                for val in bet["values"]:
                    if float(val["odd"]) < 1.96:
                        odd_ht = float(val["odd"])
    except Exception:
        pass

    if not odd_fav:
        return jsonify({"erro": "❌ Jogo inapto para análise. Nenhum favorito claro identificado."})

    risco = 20
    if odd_fav <= 1.25: risco += 1
    elif odd_fav <= 1.50: risco += 3
    else: risco += 5

    if odd_btts and odd_btts >= 2.00: risco += 3
    if odd_ht and odd_ht < 1.95: risco -= 2

    if risco <= 39:
        nivel = "🎯 Muito Baixo"; stake = "5%"
    elif risco <= 56:
        nivel = "🟢 Baixo"; stake = "4%"
    elif risco <= 74:
        nivel = "🟡 Moderado"; stake = "2.5%"
    elif risco <= 91:
        nivel = "🔴 Alto"; stake = "1%"
    else:
        nivel = "🚫 Muito Alto"; stake = "0%"

    resumo = f"""
🎯 Fixture ID: {fid}
⭐ Favorito identificado: {favorito}
⭐ Odd do favorito: {odd_fav}
⚙️ Odd BTTS: {odd_btts}
⏱️ Odd vitória 1º tempo: {odd_ht}

📊 Classificação de Risco: {nivel}
💰 Stake Recomendada: {stake}
"""

    return jsonify({"analise": resumo.strip()})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
