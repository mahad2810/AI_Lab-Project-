import pandas as pd
import numpy as np
import pickle
import statistics
from sklearn.preprocessing import StandardScaler, LabelEncoder
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from tensorflow.keras.models import load_model

class DiseasePredictor:
    def __init__(self):
        self.symptom_index = {}
        self.label_encoder = None
        self.final_xgb_model = None
        self.final_lgbm_model = None
        self.final_nn_model = None
        self.scaler = None
        self.classes_ = None

    @classmethod
    def load_models(cls, models_dir='./models/'):
        """
        Load all trained models and metadata
        """
        predictor = cls()
        
        # Load metadata
        with open(f"{models_dir}metadata.pkl", "rb") as f:
            metadata = pickle.load(f)
        
        predictor.symptom_index = metadata['symptom_index']
        predictor.label_encoder = metadata['label_encoder']
        predictor.scaler = metadata['scaler']
        predictor.classes_ = metadata.get('classes', predictor.label_encoder.classes_)
        
        # Load XGBoost model
        with open(f"{models_dir}xgb_model.pkl", "rb") as f:
            predictor.final_xgb_model = pickle.load(f)
        
        # Load LightGBM model
        with open(f"{models_dir}lgbm_model.pkl", "rb") as f:
            predictor.final_lgbm_model = pickle.load(f)
        
        # Load Neural Network model
        predictor.final_nn_model = load_model(f"{models_dir}nn_model.keras")
        
        print("All models and metadata loaded successfully")
        return predictor

    def predict(self, symptoms):
        """
        Predict disease based on input symptoms
        """
        if isinstance(symptoms, str):
            symptoms = symptoms.split(",")
        elif not isinstance(symptoms, list):
            raise ValueError("Symptoms should be a string (comma-separated) or a list of symptoms.")

        # Create input vector
        input_data = [0] * len(self.symptom_index)
        for symptom in symptoms:
            index = self.symptom_index.get(symptom.strip())
            if index is not None:
                input_data[index] = 1
            else:
                print(f"Warning: {symptom.strip()} not found in symptom index.")

        # Convert and scale input
        input_data = np.array(input_data).reshape(1, -1)
        input_data_scaled = self.scaler.transform(input_data)

        # Predict with each model
        xgb_pred_idx = int(self.final_xgb_model.predict(input_data_scaled)[0])
        lgbm_pred_idx = int(self.final_lgbm_model.predict(input_data_scaled)[0])
        nn_pred_idx = int(np.argmax(self.final_nn_model.predict(input_data_scaled), axis=1)[0])

        xgb_prediction = self.classes_[xgb_pred_idx]
        lgbm_prediction = self.classes_[lgbm_pred_idx]
        nn_prediction = self.classes_[nn_pred_idx]

        print("XGBoost Prediction: ", xgb_prediction)
        print("LightGBM Prediction: ", lgbm_prediction)
        print("Neural Network Prediction: ", nn_prediction)

        try:
            final_prediction = statistics.mode([xgb_prediction, lgbm_prediction, nn_prediction])
        except statistics.StatisticsError:
            final_prediction = xgb_prediction  # fallback

        return {
            "xgb_model_prediction": xgb_prediction,
            "lgbm_model_prediction": lgbm_prediction,
            "neural_network_prediction": nn_prediction,
            "final_prediction": nn_prediction,
        }
