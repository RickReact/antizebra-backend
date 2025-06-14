from flask_cors import CORS
from flask import Flask, request, jsonify
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
CORS(app)

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
1. Só faça a análise se houver favorito técnico claro (odd entre 1.01 e 1.95). Caso contrário, diga: "Jogo inapto para análise técnica. Não há favorito claro."
2. Aplique os 12 critérios técnicos do modelo SRP e classifique o risco: Muito Baixo, Baixo, Moderado, Alto, Muito Alto.
3. Com base no risco e nas odds, sugira:
   - Aposta mais segura (menor risco, menor lucro)
   - Aposta de valor (maior risco, maior lucro)
   - Aposta equilibrada (risco moderado, bom retorno)
4. Inclua odd do favorito (simulada se não informada), classificação do risco, stake recomendada (%), e mercados alternativos como BTTS, Over/Under, DNB, etc.

Responda de forma estruturada, profissional e clara para o apostador.
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
    app.run(host='0.0.0.0', port=10000)
