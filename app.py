from flask import Flask, request, render_template, jsonify
from threading import Lock

app = Flask(__name__)

commande = ""
resultat_commande = ""
commande_lock = Lock()

@app.route("/", methods=["GET", "POST"])
def index():
    global commande, resultat_commande
    if request.method == "POST":
        with commande_lock:
            commande = request.form.get("commande", "").strip()
            resultat_commande = ""  # Réinitialiser le résultat à chaque nouvelle commande
    return render_template("console.html", commande=commande, resultat_commande=resultat_commande)

@app.route("/get_commande")
def get_commande():
    with commande_lock:
        return commande

@app.route("/post_resultat", methods=["POST"])
def post_resultat():
    global resultat_commande
    with commande_lock:
        resultat_commande = request.form.get("resultat", "").strip()
    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
