import numpy as np
import tensorflow as tf
from sklearn.metrics import confusion_matrix, classification_report
from pathlib import Path

IMG_SIZE = (224, 224)
BATCH_SIZE = 32
SEED = 123

THRESHOLD = 0.7 

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "recyclable_model.keras"
TEST_DIR = BASE_DIR / "dataset_binary_split" / "test"

model = tf.keras.models.load_model(str(MODEL_PATH))

test_ds = tf.keras.utils.image_dataset_from_directory(
    str(TEST_DIR),
    seed=SEED,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    shuffle=False
)

class_names = test_ds.class_names
print("Class names:", class_names)
print("Threshold:", THRESHOLD)

y_true = np.concatenate([y.numpy() for _, y in test_ds], axis=0)
y_prob = model.predict(test_ds).reshape(-1)
y_pred = (y_prob >= THRESHOLD).astype(int)

print("Confusion matrix (rows=true, cols=pred):")
print(confusion_matrix(y_true, y_pred))

print("\nClassification report:")
print(classification_report(y_true, y_pred, target_names=class_names))