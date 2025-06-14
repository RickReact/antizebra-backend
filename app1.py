
from flask_cors import CORS
from flask import Flask, request, jsonify
import openai
import os
import requests

openai.api_key = os.getenv("OPENAI_API_KEY")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

app = Flask(__name__)
CORS(app)

def buscar_id_time(nome_time):
    url = f"https://v3.football.api-sports.io/teams?search={nome_time}"
    headers = {
        "x-rapidapi-host": "v3.football.api-sports.io",
        "x-rapidapi-key": RAPIDAPI_KEY
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        dados = response.json()
        if dados["response"]:
            return dados["response"][0]["team"]["id"]
    return None

def buscar_confrontos_h2h(id_time1, id_time2):
    url = f"https://v3.football.api-sports.io/fixtures/headtohead?h2h={id_time1},{id_time2}&season=2023"
    headers = {
        "x-rapidapi-host": "v3.football.api-sports.io",
        "x-rapidapi-key": RAPIDAPI_KEY
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

@app.route("/analise-jogo", methods=["POST"])
def analisar_jogo():
    data = request.get_json()
    jogo = data.get("jogo")

    if not jogo:
        return jsonify({"erro": "Jogo não informado."}), 400

    try:
        times = jogo.split("x")
        if len(times) < 2:
            raise ValueError("Formato inválido. Use: Time A x Time B – Data")

        nome_a = times[0].strip()
        nome_b = times[1].split("–")[0].strip()

        id_a = buscar_id_time(nome_a)
        id_b = buscar_id_time(nome_b)

        if not id_a or not id_b:
            return jsonify({"erro": "Não foi possível encontrar os IDs dos times."}), 404

        dados_confronto = buscar_confrontos_h2h(id_a, id_b)

        contexto_extra = f"Confrontos anteriores entre {nome_a} e {nome_b}:\n"
        if dados_confronto and dados_confronto["response"]:
            for jogo in dados_confronto["response"][:3]:
                data = jogo["fixture"]["date"].split("T")[0]
                placar = f"{jogo['teams']['home']['name']} {jogo['goals']['home']} x {jogo['goals']['away']} {jogo['teams']['away']['name']}"
                contexto_extra += f"- {data}: {placar}\n"
        else:
            contexto_extra += "Nenhum confronto direto encontrado.\n"

        prompt = f'''
Você é o ANTIZEBRA PRO MAX – analista técnico de apostas esportivas.

Analise a seguinte partida: {jogo}

DADOS REAIS DISPONÍVEIS:
{contexto_extra}

Regras:
1. Só prossiga se houver um favorito com odd entre 1.01 e 1.95. Caso contrário, diga: "❌ Jogo inapto para análise. Nenhum favorito claro identificado."
2. Confirme ou não o favoritismo técnico com base no modelo ANTIZEBRA (SRP).
3. Classifique o risco: Muito Baixo, Baixo, Moderado, Alto, Muito Alto.
4. Defina a stake recomendada:
   - Muito Baixo → 5%
   - Baixo → 4%
   - Moderado → 2.5%
   - Alto → 1%
   - Muito Alto → ❌ Não apostar

Formato de resposta:
🎯 Jogo: [Time A x Time B – data]
⭐ Favorito pelo mercado: [Time + Odd]
[✅ ou ❌] Favoritismo confirmado pelo ANTIZEBRA
📊 Classificação de Risco: [nível]
💰 Stake Recomendada: [%]
📌 Aposta recomendada: [se houver]
🧠 Comentário técnico: [explicação curta]
'''

        resposta = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )
        resultado = resposta.choices[0].message.content
        return jsonify({"analise": resultado})

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
