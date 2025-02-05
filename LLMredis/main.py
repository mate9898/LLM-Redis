import pyodbc
import pandas as pd

SERVER = "puntocentral.dyndns.org,43034"
DATABASE = "FAM450"
USERNAME = "DATA"
PASSWORD = "6,02x1023"

conn = pyodbc.connect(
    f"DRIVER={{SQL Server}};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    f"UID={USERNAME};"
    f"PWD={PASSWORD};"
)

print("✅ Conexión exitosa a SQL Server")

# obtener el stock de cada local
query_stock = """
SELECT SUCURSALES, CODITM, cantidad
FROM stock_locales;
"""

# obtener las ventas de cada producto en cada local
query_ventas = """
SELECT local_id, producto_id, SUM(cantidad) AS ventas_totales
FROM ventas
GROUP BY local_id, producto_id;
"""

# resultados a DataFrames de Pandas
df_stock = pd.read_sql(query_stock, conn)
df_ventas = pd.read_sql(query_ventas, conn)

print("📊 Datos de Stock")
print(df_stock.head())

print("📈 Datos de Ventas")
print(df_ventas.head())

# datos de stock y ventas en un solo DataFrame
df = pd.merge(df_stock, df_ventas, on=["local_id", "producto_id"], how="left")
df["ventas_totales"].fillna(0, inplace=True)  # reemplazar valores nulos en ventas

# calcular el stock promedio 
stock_promedio = df.groupby("producto_id")["cantidad"].mean().rename("stock_promedio")

# calcular la demanda
demanda_promedio = df.groupby("producto_id")["ventas_totales"].mean().rename("demanda_promedio")

df = df.merge(stock_promedio, on="producto_id").merge(demanda_promedio, on="producto_id")

# locales con sobrestock y faltantes
df["excedente"] = df["cantidad"] > df["stock_promedio"] * 1.2  # 20% más que el promedio
df["faltante"] = df["cantidad"] < df["stock_promedio"] * 0.8  # 20% menos que el promedio

# baja y alta rotación
df["baja_rotacion"] = (df["ventas_totales"] < df["demanda_promedio"] * 0.5) & df["excedente"]
df["alta_demanda"] = (df["ventas_totales"] > df["demanda_promedio"] * 1.5) & df["faltante"]

print("📊 Análisis de stock y ventas con etiquetas de redistribución")
print(df.head())

# codigo  para aplicar reglas de redis
transferencias = []

for _, row in df.iterrows():
    if row["baja_rotacion"]:  # vende poco y tiene mucho stock
        destino = df[(df["alta_demanda"]) & (df["producto_id"] == row["producto_id"])]
        for _, dest_row in destino.iterrows():
            transferencias.append({
                "producto_id": row["producto_id"],
                "de": row["local_id"],
                "hacia": dest_row["local_id"],
                "cantidad": min(row["cantidad"] - row["stock_promedio"], dest_row["stock_promedio"] - dest_row["cantidad"])
            })

# transferencias a DataFrame
df_transferencias = pd.DataFrame(transferencias)

print("📦 Sugerencias de redistribución de stock:")
print(df_transferencias)

def generar_contexto(df_stock, df_transferencias):
    contexto = "📦 **Situación de Stock Actual:**\n\n"

    for _, row in df_stock.iterrows():
        contexto += (f"- Local {row['local_id']} tiene {row['cantidad']} unidades "
                     f"del producto {row['producto_id']} (ventas: {row['ventas_totales']}).\n")

    contexto += "\n🚚 **Sugerencias de Redistribución:**\n"

    for _, row in df_transferencias.iterrows():
        contexto += (f"- Transferir {row['cantidad']} unidades del producto {row['producto_id']} "
                     f"de Local {row['de']} a Local {row['hacia']}.\n")

    return contexto

import requests

def consultar_llm(pregunta, contexto):
    url = "http://localhost:1234/v1/chat/completions"
    data = {
        "model": "nombre-del-modelo.gguf",  # reemplazar con modelo LM Studio
        "messages": [
            {"role": "system", "content": "Eres un asistente experto en logística y distribución de stock."},
            {"role": "user", "content": f"{contexto}\n\n{pregunta}"}
        ]
    }

    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"⚠️ Error en la consulta: {response.text}"

# contexto basado en los datos
contexto_stock = generar_contexto(df, df_transferencias)

# ejemplo de consulta a la LLM
pregunta = "¿Cómo optimizar la redistribución de stock?"
respuesta_llm = consultar_llm(pregunta, contexto_stock)

print("🤖 Respuesta de la LLM:")
print(respuesta_llm)