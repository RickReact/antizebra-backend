from flask import Flask, request, jsonify
from flask_cors import CORS
import requests, os
from datetime import datetime, timezone
import openai

app = Flask(__name__)
CORS(app)

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
API_HOST = "api-football-v1.p.rapidapi.com"
openai.api_key = OPENAI_KEY

def api_get(path, params):
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": API_HOST
    }
    resp = requests.get(f"https://{API_HOST}/v3/{path}", headers=headers, params=params)
    return resp.json().get("response", []) if resp.status_code == 200 else []

@app.route("/analise-jogo", methods=["POST"])
def analise_jogo():
    data = request.get_json()
    fid = data.get("fixture_id")
    if not fid:
        return jsonify({"erro": "ID da partida não fornecido"}), 400

    # ⚽ Fetch fixture details
    fix = api_get("fixtures", {"id": fid})
    if not fix:
        return jsonify({"erro": "Partida não encontrada"}), 404
    j = fix[0]
    timeA, timeB = j["teams"]["home"]["name"], j["teams"]["away"]["name"]
    idA, idB = j["teams"]["home"]["id"], j["teams"]["away"]["id"]
    game_time = datetime.fromisoformat(j["fixture"]["date"].replace("Z","+00:00"))
    if game_time <= datetime.now(timezone.utc):
        return jsonify({"erro": "⏸️ Jogo não disponível para análise (já começou ou terminou)" }), 400

    # 🧮 Fetch odds
    odds_resp = api_get("odds", {"fixture": fid})
    odd_fav = odd_btts = odd_ht = None
    if odds_resp:
        for bm in odds_resp[0].get("bookmakers", []):
            for bet in bm.get("bets", []):
                if bet["name"] == "Match Winner":
                    for val in bet["values"]:
                        if val.get("odd") and float(val["odd"]) < 1.96:
                            odd_fav = float(val["odd"])
                elif bet["name"] == "Both Teams To Score":
                    for val in bet["values"]:
                        if val.get("value") == "Yes":
                            odd_btts = float(val.get("odd"))
                elif bet["name"] == "1st Half Winner":
                    for val in bet["values"]:
                        if val.get("odd") and float(val["odd"]) < 1.96:
                            odd_ht = float(val["odd"])

    if not odd_fav:
        return jsonify({"erro": "❌ Jogo inapto — sem favorito claro (odd abaixo de 1.96)" }), 400

    # 📊 Fetch form and H2H
    formA = api_get("fixtures", {"team": idA, "last": 5})
    formB = api_get("fixtures", {"team": idB, "last": 5})
    h2h = api_get("fixtures/headtohead", {"h2h": f"{idA}-{idB}"})

    def summarize(fixtures):
        return " | ".join([f"{f['teams']['home']['name']} {f['goals']['home']} x {f['goals']['away']} {f['teams']['away']['name']}" for f in fixtures])

    formaA = summarize(formA)
    formaB = summarize(formB)
    h2h_sum = summarize(h2h)

    # 🧠 Build prompt
    prompt = f"""
Você é o ANTIZEBRA PRO MAX – analista técnico. Utilize o Método SRP para essa partida:

📅 {timeA} x {timeB}
⭐ Odd favorito: {odd_fav}
⚙️ Odd BTTS (Yes): {odd_btts}
⏱️ Odd vitória 1º tempo: {odd_ht}

📊 Últimos 5 jogos de {timeA}: {formaA or 'N/A'}
📊 Últimos 5 jogos de {timeB}: {formaB or 'N/A'}
🔁 Confronto direto H2H: {h2h_sum or 'N/A'}

Classifique o risco (🎯Muito Baixo / 🟢Baixo / 🟡Moderado / 🔴Alto / 🚫Muito Alto),
informe a stake sugerida (5%,4%,2.5%,1% ou 0%), ou indique “Não apostar”.
"""

    res = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role":"user","content":prompt}],
        temperature=0.7,
        max_tokens=400
    )
    return jsonify({"analise": res.choices[0].message["content"].strip()})

# (Mantenha demais rotas intactas: ligas-por-data e jogos-por-liga)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
