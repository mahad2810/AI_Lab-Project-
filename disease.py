from flask import Blueprint, request, jsonify, current_app
from disease_predict import DiseasePredictionModel
from docsuggest import get_specialization
from werkzeug.utils import secure_filename
import os
import cv2
import numpy as np
import joblib


# Initialize the blueprint
disease_blueprint = Blueprint('disease', __name__)

@disease_blueprint.route('/get_doctors', methods=['POST'])
def get_doctors():
    try:
        data = request.get_json()
        disease = data.get('disease', '').strip()
        if not disease:
            return jsonify({'error': 'Disease not specified.'}), 400

        specialization = get_specialization(disease)
        if not specialization:
            return jsonify({'doctors': [], 'message': f'No specialization found for disease: {disease}'}), 200

        doctors = current_app.mongo.db.doctors.find({"specialization": {'$regex': specialization, '$options': 'i'}})
        response_data = [{
            "name": doc.get("name", "Name not available"),
            "specialization": doc.get("specialization", "Specialization not available"),
            "description": doc.get("description", {}),
            "phone_number": doc.get("phone_number", "Not available"),
            "hospital": doc.get("hospital", "Not available"),
            "availability": doc.get("availability", {}),
            "fees": doc.get("fees", "Not specified")
        } for doc in doctors]

        return jsonify({"doctors": response_data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
