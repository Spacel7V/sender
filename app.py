from flask import Flask, request, render_template_string

app = Flask(__name__)

# Stocke la commande soumise
commande = ""

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
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    global commande
    if request.method == "POST":
        # Récupère la commande depuis l'input
        commande = request.form.get("commande", "").strip()
    return render_template_string(html_formulaire, commande=commande)

@app.route("/get_commande")
def get_commande():
    # Retourne la dernière commande soumise
    return commande

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)  # Démarre le serveur sur le port 5000
