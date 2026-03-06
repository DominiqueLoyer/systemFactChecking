import os
from flask import Flask, request, jsonify
from syscred.backend_app import app as syscred_app
import sys
sys.path.append('/home/user/systemFactChecking_Sandbox')

app = Flask(__name__)

# Monter l'application SysCRED existante
app.wsgi_app = syscred_app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860)
