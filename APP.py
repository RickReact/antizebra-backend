
from flask_cors import CORS
from flask import Flask, request, jsonify
import openai
import os
import requests

openai.api_key = os.getenv("OPENAI_API_KEY")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

app = Flask(__name__)
CORS(app)

# Busca todos os jogos da liga na data selecionada
def buscar_jogos_por_data(data, liga_id):
    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures"
    headers = {
        "x-rapidapi-host": "api-football-v1.p.rapidapi.com",
        "x-rapidapi-key": RAPIDAPI_KEY
    }
    params = {"date": data, "league": liga_id, "season": "2024"}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get("response", [])
    return []

@app.route("/analise-dia", methods=["POST"])
def analise_dia():
    data = request.get_json()
    data_partida = data.get("data")
    liga_id = data.get("liga")

    if not data_partida or not liga_id:
        return jsonify({"erro": "Data ou Liga não informadas"}), 400

    try:
        jogos = buscar_jogos_por_data(data_partida, liga_id)
        if not jogos:
            return jsonify({"erro": "Nenhum jogo encontrado para esta data/competição."}), 404

        jogos_seguros = []
        for jogo in jogos:
            home = jogo["teams"]["home"]["name"]
            away = jogo["teams"]["away"]["name"]
            odd = jogo.get("bookmakers", [{}])[0].get("bets", [{}])[0].get("values", [{}])[0].get("odd", "2.00")

            try:
                odd_valor = float(odd)
            except:
                continue

            if 1.01 <= odd_valor <= 1.95:
                prompt = f"""
Você é o ANTIZEBRA PRO MAX. Analise o jogo {home} x {away} na data {data_partida}.
Odd do favorito: {odd_valor}

Confirme o favoritismo técnico, classifique o risco (Muito Baixo a Muito Alto), defina a stake (1% a 5%) e diga se a aposta no favorito é recomendada.
"""
                resposta = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=600
                )
                analise = resposta.choices[0].message.content
                jogos_seguros.append({
                    "partida": f"{home} x {away}",
                    "odd_favorito": odd_valor,
                    "analise": analise
                })

        if not jogos_seguros:
            return jsonify({"erro": "Nenhum jogo com odd segura (1.01 a 1.95) encontrado."}), 200

        return jsonify(jogos_seguros)

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
