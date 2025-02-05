import pyodbc
import pandas as pd
from config import SERVER, DATABASE, USERNAME, PASSWORD

def get_connection():
    return pyodbc.connect(
        f"DRIVER={{SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};"
    )

def obtener_datos():
    conn = get_connection()
    df_stock = pd.read_sql("SELECT local_id, producto_id, cantidad FROM stock_locales", conn)
    df_ventas = pd.read_sql("SELECT local_id, producto_id, SUM(cantidad) AS ventas_totales FROM ventas GROUP BY local_id, producto_id", conn)
    conn.close()
    
    df = pd.merge(df_stock, df_ventas, on=["local_id", "producto_id"], how="left")
    df["ventas_totales"].fillna(0, inplace=True)
    return df