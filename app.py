from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import openai

app = Flask(__name__)
CORS(app)

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

@app.route("/jogos-dia", methods=["POST"])
def jogos_dia():
    data = request.get_json().get("data")
    if not data:
        return jsonify({"erro": "Data não fornecida."}), 400

    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    querystring = {
        "date": data,
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
        return jsonify({"erro": "Nenhum jogo encontrado para esta data."}), 404

    jogos_filtrados = [
        {
            "time_casa": jogo["teams"]["home"]["name"],
            "time_fora": jogo["teams"]["away"]["name"],
            "data": jogo["fixture"]["date"],
            "liga": jogo["league"]["name"]
        } for jogo in jogos
    ]
    return jsonify({"jogos": jogos_filtrados})


@app.route("/analise-jogo", methods=["POST"])
def analisar_jogo():
    data = request.get_json()
    jogo = data.get("jogo")

    if not jogo:
        return jsonify({"erro": "Jogo não informado."}), 400

    prompt = f"""
Você é o ANTIZEBRA PRO MAX – analista técnico de apostas esportivas.

Analise a seguinte partida: {jogo}

REGRAS:
1. Só prossiga se houver favorito com odd entre 1.01 e 1.95.
2. Caso não haja favorito claro, diga: "❌ Jogo inapto para análise. Nenhum favorito claro identificado."
3. Confirme ou não o favoritismo técnico com base no modelo ANTIZEBRA.
4. Classifique o risco: Muito Baixo, Baixo, Moderado, Alto, Muito Alto.
5. Defina a stake com base no risco:
   - Muito Baixo: 5%
   - Baixo: 4%
   - Moderado: 2.5%
   - Alto: 1%
   - Muito Alto: ❌ Não apostar

Formato da resposta:

🎯 Jogo: [Time A x Time B – data]  
⭐ Favorito pelo mercado: [Time + Odd]  
[✅ ou ❌] Favoritismo confirmado pelo ANTIZEBRA  
📊 Classificação de Risco: [nível]  
💰 Stake Recomendada: [%]

📌 Aposta recomendada: [se houver – vitória do favorito]

🧠 Comentário técnico: [resumo técnico profissional]
"""

    try:
        resposta = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800
        )
        resultado = resposta.choices[0].message["content"]
        return jsonify({"analise": resultado})

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
