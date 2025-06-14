
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

@app.route("/analise-dia", methods=["POST"])
def analise_dia():
    data = request.get_json()
    data_selecionada = data.get("data")
    liga_id = data.get("liga_id")

    if not data_selecionada or not liga_id:
        return jsonify({"erro": "Data ou ID da liga não fornecidos."}), 400

    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures"
    querystring = {
        "date": data_selecionada,
        "league": liga_id,
        "season": "2024"
    }
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "api-football-v1.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    if response.status_code != 200:
        return jsonify({"erro": "Erro ao buscar dados da API."}), 500

    data = response.json()
    jogos = data.get("response", [])

    if not jogos:
        return jsonify({"erro": "Nenhum jogo encontrado para esta data/competição."}), 404

    jogos_filtrados = [
        {
            "time_casa": jogo["teams"]["home"]["name"],
            "time_fora": jogo["teams"]["away"]["name"],
            "data": jogo["fixture"]["date"],
            "liga": jogo["league"]["name"]
        } for jogo in jogos
    ]

    return jsonify({"jogos": jogos_filtrados})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
