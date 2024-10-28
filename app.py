from flask import Flask, request, render_template_string

app = Flask(__name__)

# Stocke la commande soumise et le résultat de la commande
commande = ""
resultat_commande = ""

# Page web avec un formulaire
html_formulaire = """
<!DOCTYPE html>
<html>
<head><title>Command Console</title></head>
<body>
    <h2>Entrer une commande Batch</h2>
    <form action="/" method="POST">
        <input type="text" name="commande" placeholder="Commande batch">
        <button type="submit">Envoyer</button>
    </form>
    <p>Dernière commande soumise : {{ commande }}</p>
    <h3>Résultat de la commande :</h3>
    <pre>{{ resultat_commande }}</pre>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    global commande
    if request.method == "POST":
        # Récupère la commande depuis l'input
        commande = request.form.get("commande", "").strip()
    return render_template_string(html_formulaire, commande=commande, resultat_commande=resultat_commande)

@app.route("/get_commande")
def get_commande():
    # Retourne la dernière commande soumise
    return commande

@app.route("/post_resultat", methods=["POST"])
def post_resultat():
    global resultat_commande
    # Récupère le résultat de la commande depuis le corps de la requête
    resultat_commande = request.form.get("resultat", "").strip()
    return "Résultat reçu", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)  # Démarre le serveur sur le port 5000
