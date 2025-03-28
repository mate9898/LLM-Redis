import requests

def generar_contexto(df):
    contexto = "📦 **Situación de Stock Actual:**\n\n"
    for _, row in df.iterrows():
        contexto += f"- Local {row['local_id']} tiene {row['cantidad']} unidades del producto {row['producto_id']} (ventas: {row['ventas_totales']}).\n"
    return contexto

def consultar_llm(pregunta, contexto):
    url = "http://localhost:1234/v1/chat/completions"
    data = {
        "model": "nombre-del-modelo.gguf",  # aca se pone nombre real del modelo en LM Studio
        "messages": [
            {"role": "system", "content": "Eres un experto en logística y distribución de stock."},
            {"role": "user", "content": f"{contexto}\n\n{pregunta}"}
        ]
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"⚠️ Error: {response.text}"