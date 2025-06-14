from flask_cors import CORS
from flask import Flask, request, jsonify
import openai
import os

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
CORS(app)

@app.route("/analise-jogo", methods=["POST"])
def analisar_jogo():
    data = request.get_json()
    jogo = data.get("jogo")

    if not jogo:
        return jsonify({"erro": "Jogo não informado."}), 400

    prompt = f"""
Você é o ANTIZEBRA PRO MAX – um analista técnico de apostas esportivas.

Analise a partida informada a seguir: {jogo}

Regra obrigatória:
1. Só prossiga se houver um favorito com odd entre 1.01 e 1.95. Caso contrário, diga: "❌ Jogo inapto para análise. Nenhum favorito claro identificado."

Se houver favorito dentro do critério, aplique o método ANTIZEBRA (SRP) para:
- Confirmar ou não o favoritismo técnico
- Classificar o risco da aposta em: Muito Baixo, Baixo, Moderado, Alto, Muito Alto
- Calcular stake ideal com base na tabela:
  Muito Baixo → 5%
  Baixo → 4%
  Moderado → 2.5%
  Alto → 1%
  Muito Alto → ❌ Não apostar

Formate sua resposta da seguinte forma:

🎯 Jogo: [Time A x Time B – data]  
⭐ Favorito pelo mercado: [Time + Odd]  
[✅ ou ❌] Favoritismo confirmado pelo ANTIZEBRA  
📊 Classificação de Risco: [nível]  
💰 Stake Recomendada: [%]

📌 Aposta recomendada: [se houver – vitória do favorito]

🧠 Comentário técnico: [breve explicação técnica do cenário, sem mercados alternativos]
"""

    try:
        resposta = client.chat.completions.create(
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
