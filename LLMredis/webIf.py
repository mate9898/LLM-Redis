from webIf import Flask, request, jsonify, render_template
from flask_cors import CORS
import pyodbc
import pandas as pd
import requests

app = Flask(__name__)
CORS(app)

SERVER = "puntocentral.dyndns.org,43034"
DATABASE = "FAM450"
USERNAME = "DATA"
PASSWORD = "6,02x1023"


def get_connection():
    return pyodbc.connect(
        f"DRIVER={{SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};"
    )

# datos de stock y ventas
def obtener_datos():
    conn = get_connection()
    df_stock = pd.read_sql("SELECT local_id, producto_id, cantidad FROM stock_locales", conn)
    df_ventas = pd.read_sql("SELECT local_id, producto_id, SUM(cantidad) AS ventas_totales FROM ventas GROUP BY local_id, producto_id", conn)
    conn.close()
    
    df = pd.merge(df_stock, df_ventas, on=["local_id", "producto_id"], how="left")
    df["ventas_totales"].fillna(0, inplace=True)
    return df

# LLM
def generar_contexto(df):
    contexto = "📦 **Situación de Stock Actual:**\n\n"
    for _, row in df.iterrows():
        contexto += f"- Local {row['local_id']} tiene {row['cantidad']} unidades del producto {row['producto_id']} (ventas: {row['ventas_totales']}).\n"
    return contexto

# consultar la LLM en LM Studio
def consultar_llm(pregunta, contexto):
    url = "http://localhost:1234/v1/chat/completions"
    data = {
        "model": "nombre-del-modelo.gguf",  
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

# interfaz web
@app.route("/")
def index():
    return render_template("index.html")

# ruta consultar stock y generar respuesta de la LLM
@app.route("/consulta", methods=["GET"])
def consulta():
    df = obtener_datos()
    contexto = generar_contexto(df)
    pregunta = request.args.get("pregunta", "¿Cómo redistribuir el stock?")
    respuesta = consultar_llm(pregunta, contexto)
    return jsonify({"contexto": contexto, "respuesta": respuesta})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
