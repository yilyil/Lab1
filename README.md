# Projet de Simulation Command & Control (C2)

Ce projet est une simulation pédagogique d'une infrastructure de type **Command & Control**. Il permet de démontrer les mécanismes d'exfiltration de données, de chiffrement symétrique et de pilotage à distance d'un agent furtif au sein d'un réseau isolé.

## Architecture du Système

Le système est divisé en trois composants principaux fonctionnant sur deux machines virtuelles Linux :

1. **Agent Victime (Cible) :** Un script Python multi-threadé qui capture les frappes clavier, l'écran et le micro.
2. **Serveur Attaquant (Récepteur) :** Une API Flask qui réceptionne, déchiffre et stocke les données de manière structurée.
3. **Dashboard de Contrôle (C2) :** Une interface Web interactive permettant de piloter l'agent en temps réel.

---

## Fonctionnalités Clés

* **Capture Multimédia :** Keylogger avec normalisation des touches, captures d'écran (Screenshots) et enregistrements audio (Microphone).
* **Sécurité des Flux :** Chiffrement des données en **AES-256** via la bibliothèque Cryptography (Fernet).
* **Résilience Réseau :** Système de tampon mémoire (Buffer) empêchant la perte de données en cas de coupure du lien LAN.
* **Pilotage à Distance :** Activation/Désactivation des captures et gestion des modes depuis une interface centralisée.
* **Gestion Multi-Victimes :** Identification unique de chaque machine via un **UUID** généré dynamiquement.

---

## Installation et Prérequis

### Configuration Réseau

* **VirtualBox :** Les deux VMs doivent être configurées en **"Réseau Interne"** (Internal Network) pour garantir l'isolation.
* **IP Statiques suggérées :**
* Attaquant : `192.168.10.100`
* Victime : `192.168.10.1`



### Dépendances Python

Exécutez la commande suivante sur les deux machines :

```bash
pip install pynput requests flask cryptography Pillow sounddevice scipy

```

*Note : Sur la victime, assurez-vous que les bibliothèques système pour l'audio (PortAudio) sont présentes.*

---

## Utilisation

### 1. Lancement du Serveur (VM Attaquant)

```bash
python3 server.py

```

Le serveur écoute sur le port **5000** pour la réception et propose l'interface web.

### 2. Lancement de l'Agent (VM Victime)

```bash
python3 agent.py

```

L'agent commence la capture en arrière-plan et ouvre un port de commande sur le **8080**.

### 3. Pilotage

Ouvrez un navigateur sur la machine attaquante à l'adresse suivante :
`http://localhost:5000`

---

## Analyse Cybersécurité (Concepts abordés)

* **Exfiltration :** Utilisation du protocole HTTP pour masquer les données volées dans du trafic apparemment légitime.
* **Persistance & Discrétion :** L'agent utilise le multi-threading pour ne pas bloquer les processus utilisateur.
* **Chiffrement :** Protection contre l'analyse de paquets (Wireshark) via AES.

---

## ⚠️ Avertissement

Ce projet est réalisé dans un cadre strictement pédagogique. L'utilisation de ces outils sur des systèmes sans autorisation explicite est illégale. L'ensemble des tests a été effectué dans un environnement virtualisé et isolé.

---
