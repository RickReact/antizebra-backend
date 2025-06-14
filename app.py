
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import openai

app = Flask(__name__)
CORS(app)

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_KEY

HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": "api-football-v1.p.rapidapi.com"
}

@app.route("/ligas-por-data", methods=["POST"])
def ligas_por_data():
    data = request.get_json().get("data")
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    query = {"date": data}

    response = requests.get(url, headers=HEADERS, params=query)
    if response.status_code != 200:
        return jsonify({"erro": "Erro ao buscar ligas."}), 500

    fixtures = response.json().get("response", [])
    ligas_unicas = {}
    for jogo in fixtures:
        liga = jogo["league"]
        ligas_unicas[liga["id"]] = {"id": liga["id"], "nome": liga["name"], "pais": liga["country"]}

    return jsonify({"ligas": list(ligas_unicas.values())})

@app.route("/jogos-por-liga", methods=["POST"])
def jogos_por_liga():
    data_json = request.get_json()
    data = data_json.get("data")
    liga_id = data_json.get("liga_id")

    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    query = {"date": data, "league": liga_id, "season": "2024"}

    response = requests.get(url, headers=HEADERS, params=query)
    if response.status_code != 200:
        return jsonify({"erro": "Erro ao buscar jogos."}), 500

    jogos = response.json().get("response", [])
    lista = []
    for jogo in jogos:
        lista.append({
            "time_casa": jogo["teams"]["home"]["name"],
            "time_fora": jogo["teams"]["away"]["name"],
            "data": jogo["fixture"]["date"]
        })

    return jsonify({"jogos": lista})

@app.route("/analise-jogo", methods=["POST"])
def analise_jogo():
    data = request.get_json()
    time_a = data.get("time_a")
    time_b = data.get("time_b")
    data_jogo = data.get("data")

    if not time_a or not time_b:
        return jsonify({"erro": "Times não informados."}), 400

    contexto = f"Jogo entre {time_a} e {time_b} agendado para {data_jogo}. Dados reais não estão completos, mas simule com base no modelo ANTIZEBRA e odds fictícias próximas da realidade."

    prompt = f"""
Você é o ANTIZEBRA PRO MAX – um analista técnico de apostas esportivas.

Analise o jogo: {time_a} x {time_b} em {data_jogo}

Use este contexto para SIMULAR a análise com base no método ANTIZEBRA:

{contexto}

1. Só prossiga se houver um favorito com odd entre 1.01 e 1.95. Caso contrário, diga: "❌ Jogo inapto para análise. Nenhum favorito claro identificado."

Se houver favorito, siga os passos:

1. Confirme ou não o favoritismo técnico com base no modelo ANTIZEBRA (SRP).
2. Classifique o risco: Muito Baixo, Baixo, Moderado, Alto, Muito Alto.
3. Defina a stake recomendada com base na tabela:
   - Muito Baixo → 5%
   - Baixo → 4%
   - Moderado → 2.5%
   - Alto → 1%
   - Muito Alto → ❌ Não apostar

Formato da resposta:

🎯 Jogo: {time_a} x {time_b} – {data_jogo}
⭐ Favorito pelo mercado: [Time + Odd]
[✅ ou ❌] Favoritismo confirmado pelo ANTIZEBRA
📊 Classificação de Risco: [nível]
💰 Stake Recomendada: [%]

📌 Aposta recomendada: [se houver – vitória do favorito]

🧠 Comentário técnico: [breve explicação técnica do cenário]
"""

    try:
        resposta = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800
        )
        return jsonify({"analise": resposta.choices[0].message.content})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
