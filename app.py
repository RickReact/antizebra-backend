
from flask_cors import CORS
from flask import Flask, request, jsonify
import openai
import os
import requests

# Configurar clientes e variáveis de ambiente
openai.api_key = os.getenv("OPENAI_API_KEY")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

app = Flask(__name__)
CORS(app)

# Função para buscar dados reais do jogo
def buscar_dados_jogo(time_a, time_b):
    url = f"https://api-football-v1.p.rapidapi.com/v2/fixtures/headtohead/{time_a}/{time_b}"
    headers = {
        "x-rapidapi-host": "api-football-v1.p.rapidapi.com",
        "x-rapidapi-key": RAPIDAPI_KEY
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

# Função para extrair últimos jogos
def extrair_ultimos_jogos(dados_json):
    try:
        partidas = dados_json.get("api", {}).get("fixtures", [])
        ultimos = partidas[:5]

        resultados = []
        for partida in ultimos:
            home = partida['homeTeam']['team_name']
            away = partida['awayTeam']['team_name']
            goals = partida['goalsHomeTeam'], partida['goalsAwayTeam']
            status = partida['statusShort']

            if status == "FT":
                resultado = f"{home} {goals[0]} x {goals[1]} {away}"
                resultados.append(resultado)

        return resultados

    except Exception as e:
        return [f"Erro ao extrair dados: {str(e)}"]

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

        time_a = times[0].strip().replace(" ", "%20")
        time_b = times[1].split()[0].strip().replace(" ", "%20")

        dados_reais = buscar_dados_jogo(time_a, time_b)

        contexto_extra = ""
        if dados_reais:
            ultimos = extrair_ultimos_jogos(dados_reais)
            contexto_extra = "\n📊 Últimos confrontos (dados REAIS):\n" + "\n".join(ultimos)

        prompt = f"""
Você é o ANTIZEBRA PRO MAX – analista técnico de apostas esportivas, especializado no modelo SRP.

🔒 Você recebeu os seguintes dados REAIS dos últimos confrontos entre os times (API oficial):

{contexto_extra}

📌 Esses dados são reais e foram fornecidos diretamente via API. Use-os na análise abaixo.

Analise a seguinte partida: {jogo}

1. Só prossiga se houver um favorito com odd entre 1.01 e 1.95. Caso contrário, diga: "❌ Jogo inapto para análise. Nenhum favorito claro identificado."

Se houver favorito:
1. Confirme ou não o favoritismo técnico com base no modelo ANTIZEBRA (SRP).
2. Classifique o risco: Muito Baixo, Baixo, Moderado, Alto, Muito Alto.
3. Defina a stake recomendada:
   - Muito Baixo → 5%
   - Baixo → 4%
   - Moderado → 2.5%
   - Alto → 1%
   - Muito Alto → ❌ Não apostar

Apresente a resposta assim:

🎯 Jogo: [Time A x Time B – data]  
⭐ Favorito pelo mercado: [Time + Odd]  
[✅ ou ❌] Favoritismo confirmado pelo ANTIZEBRA  
📊 Classificação de Risco: [nível]  
💰 Stake Recomendada: [%]

📌 Aposta recomendada: [ex: Vitória do favorito]

🧠 Comentário técnico: [Explicação baseada nos dados reais fornecidos acima]
"""

        resposta = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800
        )
        resultado = resposta.choices[0].message.content
        return jsonify({"analise": resultado})

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
