from flask import Flask, request, jsonify
from flask_cors import CORS
import requests, os
from datetime import datetime
import openai

app = Flask(__name__)
CORS(app)

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
API_HOST = "api-football-v1.p.rapidapi.com"

openai.api_key = OPENAI_KEY

@app.route("/ligas-por-data", methods=["POST"])
def ligas_por_data():
    data = request.get_json().get("data")
    if not data:
        return jsonify({"erro": "Data não informada"}), 400

    url = f"https://{API_HOST}/v3/fixtures"
    r = requests.get(url, headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": API_HOST}, params={"date": data})
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

    year = datetime.strptime(data, "%Y-%m-%d").year
    r = requests.get(f"https://{API_HOST}/v3/fixtures",
                     headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": API_HOST},
                     params={"date": data, "league": liga, "season": year})

    return jsonify({"jogos": [
        {
            "fixture_id": j["fixture"]["id"],
            "time_casa": j["teams"]["home"]["name"],
            "time_fora": j["teams"]["away"]["name"],
            "data": j["fixture"]["date"]
        } for j in r.json().get("response", [])
    ]})

@app.route("/analise-jogo", methods=["POST"])
def analise_jogo():
    req = request.get_json()
    fid = req.get("fixture_id")
    if not fid:
        return jsonify({"erro": "ID da partida não fornecido"}), 400

    # Buscar dados do jogo
    f = requests.get(f"https://{API_HOST}/v3/fixtures", 
                     headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": API_HOST}, 
                     params={"id": fid}).json()["response"][0]
    o = requests.get(f"https://{API_HOST}/v3/odds", 
                     headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": API_HOST}, 
                     params={"fixture": fid}).json().get("response", [])

    # Preparar dados-chave
    home = f["teams"]["home"]["name"]
    away = f["teams"]["away"]["name"]
    date = f["fixture"]["date"]
    bookmakers = o[0]["bookmakers"] if o else []

    # Extrair odds
    odd_fav = odd_btts = odd_ht = None
    for bm in bookmakers:
        for bet in bm.get("bets", []):
            if bet["name"] == "Match Winner":
                for v in bet["values"]:
                    if float(v["odd"]) < 1.96:
                        odd_fav = float(v["odd"])
            elif bet["name"] == "Both Teams To Score" and odd_btts is None:
                for v in bet["values"]:
                    if v["value"] == "Yes":
                        odd_btts = float(v["odd"])
            elif bet["name"] == "1st Half Winner" and odd_ht is None:
                for v in bet["values"]:
                    if float(v["odd"]) < 1.96:
                        odd_ht = float(v["odd"])

    # Buscar forma recente e H2H
    def busca_fixtures(params):
        resp = requests.get(f"https://{API_HOST}/v3/fixtures",
                            headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": API_HOST},
                            params=params).json().get("response", [])
        return [{
            "res": fx["teams"]["home"]["winner"] or fx["fixture"]["status"]["elapsed"] < 90,
            "time": fx["teams"]["home" if params.get("team") == f["teams"]["home"]["id"] else "away"]["name"]
        } for fx in resp]

    form_home = busca_fixtures({"team": f["teams"]["home"]["id"], "last": 5})
    form_away = busca_fixtures({"team": f["teams"]["away"]["id"], "last": 5})
    h2h = busca_fixtures({"h2h": f"{f['teams']['home']['id']}-{f['teams']['away']['id']}", "last": 5})

    # Montar prompt para o modelo
    prompt = f"""
Você é o MÉTODO ANTIZEBRA – Sistema de Risco Ponderado.
Analise a partida:
{home} vs {away} (ID: {fid}) em {date}

Odds:
- Favorito (odd <1.96): {odd_fav}
- BTTS (Yes): {odd_btts}
- 1º tempo (favoritismo): {odd_ht}

Forma (últimos 5 jogos):
- {home}: {form_home}
- {away}: {form_away}

Confronto direto (H2H 5 jogos): {h2h}

Siga o método:
…[continue com os 12 critérios SRP]…
Retorne:
1. Indicação de favorito.
2. Classificação de risco + stake (%).
3. Justificativa técnica resumida.
"""

    gpt_resp = openai.ChatCompletion.create(
        model="gpt-4", messages=[{"role": "user", "content": prompt}],
        temperature=0.7, max_tokens=500
    ).choices[0].message.content

    return jsonify({"analise": gpt_resp})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
