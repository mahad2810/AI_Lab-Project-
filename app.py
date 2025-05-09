import os
from flask_cors import CORS
from flask import Flask, render_template, redirect, url_for, request, session, flash ,jsonify
from flask_pymongo import PyMongo
import requests
from datetime import datetime
from pymongo import MongoClient
import json
from dotenv import load_dotenv
from chatbot import chatbot_blueprint

app = Flask(__name__,static_folder='static')
CORS(app)
app.secret_key = "your_secret_key"  # Replace with a secure secret key
app.config["MONGO_URI"] = "mongodb+srv://mahadiqbalaiml27:9Gx_qVZ-tpEaHUu@healthcaresystem.ilezc.mongodb.net/healthcaresystem?retryWrites=true&w=majority&appName=Healthcaresystem"  # Replace with your MongoDB URI
app.config['HOSPITAL_UPLOAD_FOLDER'] = 'static/uploads'

mongo = PyMongo(app)
app.mongo = mongo

# Ensure 'uploads' directory exists
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route("/")
def landing_page():
    return render_template("land.html")


@app.route('/disease')
def render_disease():
    return render_template('disease.html')



from disease import disease_blueprint
# Register the blueprint
app.register_blueprint(disease_blueprint)

app.register_blueprint(chatbot_blueprint)

client = MongoClient(app.config["MONGO_URI"])
db = client["healthcaresystem"]
appointments_collection = db["appointments"]
tests_collection = db["tests"]



# Load environment variables from .env file
load_dotenv()



if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    app.run(host="localhost", port=5000)  # Correct host and port for Cloud Run
