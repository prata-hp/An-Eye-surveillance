import cv2
import numpy as np
from tensorflow.keras.models import load_model


class ViolenceDetector:
    """
    CNN-based violence detector.
    Loads a Keras model and predicts a violence probability
    for a single BGR frame.
    """

    INPUT_SIZE = (128, 128)

    def __init__(self, model_path: str):
        self.model = load_model(model_path)

    def predict(self, frame: np.ndarray) -> float:
        """
        Returns a float in [0, 1] — probability of violence.
        """
        img = cv2.resize(frame, self.INPUT_SIZE)
        img = img.astype(np.float32) / 255.0
        img = np.expand_dims(img, axis=0)          # (1, 128, 128, 3)
        prediction = self.model.predict(img, verbose=0)
        return float(np.clip(prediction[0][0], 0.0, 1.0))
