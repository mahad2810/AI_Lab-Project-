import pickle
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC
from sklearn.naive_bayes import GaussianNB
from sklearn.ensemble import RandomForestClassifier, VotingClassifier

class DiseasePredictionModel:
    def __init__(self):
        # Initialize empty attributes
        self.encoder = None
        self.all_symptoms = None
        self.symptom_index = None
        self.predictions_classes = None
        self.final_svm_model = None
        self.final_nb_model = None
        self.final_rf_model = None
        self.voting_classifier = None
        self.important_features = None  # This will store the 28 important features
        
    @classmethod
    def load_model(cls, filename):
        """
        Load a saved model from a file.
        
        Args:
            filename (str): Path to the saved model file.
            
        Returns:
            DiseasePredictionModel: Loaded model instance.
        """
        with open(filename, 'rb') as f:
            state = pickle.load(f)
        
        model = cls()
        model.encoder = state['encoder']
        model.all_symptoms = state['all_symptoms']
        model.symptom_index = state['symptom_index']
        model.predictions_classes = state['predictions_classes']
        model.final_svm_model = state['final_svm_model']
        model.final_nb_model = state['final_nb_model']
        model.final_rf_model = state['final_rf_model']
        model.voting_classifier = state['voting_classifier']
        model.important_features = state['important_features']  # Load the important features
        
        return model

    def predict(self, symptoms):
        """
        Predict disease based on symptoms.
        
        Args:
            symptoms: List of symptoms or comma-separated string of symptoms
            
        Returns:
            Dictionary with model predictions and confidence scores
        """
        # Input validation and processing
        if isinstance(symptoms, str):
            symptoms = [s.strip() for s in symptoms.split(",")]
        elif not isinstance(symptoms, list):
            raise ValueError("Symptoms should be a string or list of symptoms.")
        
        # Track valid/invalid symptoms
        valid_symptoms = []
        invalid_symptoms = []
        
        # Create input vector based on ALL symptoms (132 in original data)
        input_data = [0] * len(self.all_symptoms)
        
        for symptom in symptoms:
            # Standardize symptom name (handle common variations)
            symptom = symptom.strip().lower()
            symptom = symptom.replace(" ", "_")  # Convert spaces to underscores
            
            # Handle specific known variations
            if symptom == "dischromic_patches" or symptom == "dischromic _patches":
                symptom = "dischromic _patches"
            
            # Check if symptom exists in the full symptom list
            if symptom in self.symptom_index:
                input_data[self.symptom_index[symptom]] = 1
                valid_symptoms.append(symptom)
            else:
                invalid_symptoms.append(symptom)
        
        # Convert to numpy array and reshape
        input_data = np.array(input_data).reshape(1, -1)
        
        # If feature selection was used during training, select only important features
        if hasattr(self, 'important_features') and self.important_features is not None:
            # Create mask for important features
            feature_mask = [symptom in self.important_features for symptom in self.all_symptoms]
            input_data = input_data[:, feature_mask]
        
        # Get predictions from all models
        return {
            "rf_model_prediction": self.predictions_classes[self.final_rf_model.predict(input_data)[0]],
            "naive_bayes_prediction": self.predictions_classes[self.final_nb_model.predict(input_data)[0]],
            "svm_model_prediction": self.predictions_classes[self.final_svm_model.predict(input_data)[0]],
            "final_prediction": self.predictions_classes[self.voting_classifier.predict(input_data)[0]],
        }
        