from webIf import Flask, request, jsonify, render_template
from flask_cors import CORS
from dataB import obtener_datos
from llm import consultar_llm, generar_contexto

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/consulta", methods=["GET"])
def consulta():
    df = obtener_datos()
    contexto = generar_contexto(df)
    pregunta = request.args.get("pregunta", "¿Cómo redistribuir el stock?")
    respuesta = consultar_llm(pregunta, contexto)
    return jsonify({"contexto": contexto, "respuesta": respuesta})

if __name__ == "__main__":
    app.run(debug=True, port=5000)