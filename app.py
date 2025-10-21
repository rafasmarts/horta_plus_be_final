from flask import Flask, request, jsonify
from tensorflow.keras.models import load_model
from tensorflow.keras.utils import load_img, img_to_array
import numpy as np
import json
import os
from io import BytesIO
import logging
from datetime import datetime

# Logs
logging.basicConfig(
    filename="backend_access.log",  # ficheiro onde os logs ficam
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

MODEL_PATH = "modelo_morangos.keras"
CONFIG_PATH = "modelo_morangos_config.json"

# Carregar Modelo e config
def load_model_with_config():
    if not os.path.exists(MODEL_PATH):
        logging.error("Modelo não encontrado.")
        raise FileNotFoundError(f"Modelo não encontrado em {MODEL_PATH}")
    if not os.path.exists(CONFIG_PATH):
        logging.error("Configuração não encontrada.")
        raise FileNotFoundError(f"Configuração não encontrada em {CONFIG_PATH}")

    # 🧠 Corrige a desserialização para modelos Functional (como o MobileNetV2)
    model = load_model(MODEL_PATH, compile=False, safe_mode=False)

    with open(CONFIG_PATH, "r") as f:
        cfg = json.load(f)

    return model, cfg["class_names"]

# predict -
def predict_with_fallback(img_file, model, class_names, threshold=0.7):
    try:
        # Volta o ponteiro para o início (importante se o ficheiro foi lido antes)
        img_file.seek(0)
        # Lê o conteúdo do ficheiro como bytes e passa para BytesIO
        img_bytes = BytesIO(img_file.read())
        img = load_img(img_bytes, target_size=(224, 224))
        img_arr = img_to_array(img) / 255.0
        img_arr = np.expand_dims(img_arr, axis=0)

        probs = model.predict(img_arr)[0]
        max_prob = np.max(probs)
        pred_class = class_names[np.argmax(probs)]

        if max_prob < threshold:
            pred_class = "em maturação"

        return pred_class, float(max_prob), {cls: float(p) for cls, p in zip(class_names, probs)}

    except Exception as e:
        logging.exception("Erro ao processar imagem")
        raise e


model, class_names = load_model_with_config()
# --- Flask app ---
app = Flask(__name__)

@app.before_request
def log_request_info():
    logging.info(f"Acesso de {request.remote_addr} ao endpoint {request.path}")

@app.route("/predict-morango", methods=["POST"])
def predict_morango():
    if "file" not in request.files:
        logging.warning(f"Tentativa sem ficheiro de {request.remote_addr}")
        return jsonify({"erro": "Nenhum ficheiro enviado"}), 400

    img_file = request.files["file"]
    classe, confianca, dist = predict_with_fallback(img_file, model, class_names)

    logging.info(f"Predição: {classe} (confiança: {confianca:.2f}) para {request.remote_addr}")

    return jsonify({
        "classe": classe,
        "confianca": f"{confianca*100:.1f}%",
        "distribuicao": dist
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
