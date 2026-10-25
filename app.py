from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

usuarios = {} # sid -> {nome, hora, ip}
posicoes = {} # nome -> {nome, lat, lng}


@app.route("/")
def index():
    return render_template("familia.html")


def lista_online():
    unicos = {}
    for u in usuarios.values():
        unicos.setdefault(u["nome"], u) # mesmo nome = 1 pessoa
    return list(unicos.values())


@socketio.on("entrar")
def entrar(data):
    nome = (data.get("nome") or "").strip()[:30]
    if not nome:
        return
    usuarios[request.sid] = {
        "nome": nome,
        "hora": datetime.now().strftime("%H:%M:%S"),
        "ip": request.remote_addr,
    }
    socketio.emit("lista", lista_online())
    emit("posicoes", list(posicoes.values())) # só para quem entrou


@socketio.on("localizacao")
def localizacao(data):
    u = usuarios.get(request.sid)
    if not u:
        return
    try:
        lat, lng = float(data["lat"]), float(data["lng"])
    except (KeyError, TypeError, ValueError):
        return
    d = {"nome": u["nome"], "lat": lat, "lng": lng}
    posicoes[u["nome"]] = d
    socketio.emit("localizacao", d)


@socketio.on("disconnect")
def sair():
    u = usuarios.pop(request.sid, None)
    if u and not any(x["nome"] == u["nome"] for x in usuarios.values()):
        posicoes.pop(u["nome"], None)
        socketio.emit("saiu", {"nome": u["nome"]})
    socketio.emit("lista", lista_online())


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)
