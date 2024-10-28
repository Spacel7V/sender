from flask import Flask, request, render_template_string

app = Flask(__name__)

commande = ""
resultat_commande = ""

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
    global commande, resultat_commande
    if request.method == "POST":
        nouvelle_commande = request.form.get("commande", "").strip()
        if nouvelle_commande and nouvelle_commande != commande:
            commande = nouvelle_commande
            resultat_commande = ""  # Réinitialise le résultat pour une nouvelle commande
    return render_template_string(html_formulaire, commande=commande, resultat_commande=resultat_commande)

@app.route("/get_commande")
def get_commande():
    return commande

@app.route("/post_resultat", methods=["POST"])
def post_resultat():
    global resultat_commande
    resultat_commande = request.form.get("resultat", "").strip()
    return "Résultat reçu", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
