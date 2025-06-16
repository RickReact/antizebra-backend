from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from datetime import datetime, timezone
import openai

app = Flask(__name__)
CORS(app)

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
API_HOST = "api-football-v1.p.rapidapi.com"
openai.api_key = OPENAI_KEY

def busca_fixtures(filtros):
    url = f"https://{API_HOST}/v3/fixtures"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": API_HOST
    }
    response = requests.get(url, headers=headers, params=filtros)
    if response.status_code != 200:
        return []
    return response.json().get("response", [])

@app.route("/ligas-por-data", methods=["POST"])
def ligas_por_data():
    data = request.get_json().get("data")
    if not data:
        return jsonify({"erro": "Data não informada"}), 400

    fixtures = busca_fixtures({"date": data})
    ligas = {}
    for item in fixtures:
        league = item["league"]
        ligas[league["id"]] = {
            "id": league["id"],
            "nome": league["name"],
            "pais": league["country"]
        }

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

    fixtures = busca_fixtures({"date": data, "league": liga, "season": str(ano)})
    jogos = []
    for j in fixtures:
        jogos.append({
            "fixture_id": j["fixture"]["id"],
            "time_casa": j["teams"]["home"]["name"],
            "time_fora": j["teams"]["away"]["name"],
            "data": j["fixture"]["date"]
        })

    return jsonify({"jogos": jogos})

@app.route("/analise-jogo", methods=["POST"])
def analise_jogo():
    req = request.get_json()
    fid = req.get("fixture_id")
    if not fid:
        return jsonify({"erro": "ID da partida não fornecido"}), 400

    url_fixture = f"https://{API_HOST}/v3/fixtures"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": API_HOST
    }

    detalhes = requests.get(url_fixture, headers=headers, params={"id": fid})
    if detalhes.status_code != 200:
        return jsonify({"erro": "Erro ao buscar detalhes da partida"}), 500

    dados = detalhes.json().get("response", [])
    if not dados:
        return jsonify({"erro": "Partida não encontrada"}), 404

    fixture = dados[0]
    timeA = fixture["teams"]["home"]["name"]
    timeB = fixture["teams"]["away"]["name"]
    game_time_str = fixture["fixture"]["date"]
    game_time = datetime.fromisoformat(game_time_str.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)

    if game_time <= now:
        return jsonify({"erro": "⏸️ Esta partida já começou ou foi encerrada. Análises são feitas apenas no pré-jogo."}), 400

    prompt = f"""
Você é o ANTIZEBRA PRO MAX - um analista técnico de apostas esportivas.
Analise a partida {timeA} x {timeB}. A partida ainda não começou e está apta para análise.
Aplique o Método SRP (Sistema de Risco Ponderado) e apresente uma avaliação de risco, incluindo uma sugestão de stake ou se deve evitar aposta.
"""

    resposta = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    return jsonify({"analise": resposta.choices[0].message["content"].strip()})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
