import tensorflow as tf
from tensorflow.keras import layers, models
from pathlib import Path

IMG_SIZE = (224, 224)
BATCH_SIZE = 32
SEED = 123

BASE_DIR = Path(__file__).resolve().parent
TRAIN_DIR = BASE_DIR / "dataset_binary_split" / "train"
VAL_DIR = BASE_DIR / "dataset_binary_split" / "val"

def count_images(folder: Path) -> int:
    exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    return sum(1 for p in folder.rglob("*") if p.suffix.lower() in exts)

train_ds = tf.keras.utils.image_dataset_from_directory(
    str(TRAIN_DIR),
    seed=SEED,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE
)

val_ds = tf.keras.utils.image_dataset_from_directory(
    str(VAL_DIR),
    seed=SEED,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    shuffle=False
)

print("Class names:", train_ds.class_names) 

AUTOTUNE = tf.data.AUTOTUNE
train_ds = train_ds.cache().shuffle(1000, seed=SEED).prefetch(buffer_size=AUTOTUNE)
val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)

data_augmentation = tf.keras.Sequential([
    layers.RandomFlip("horizontal"),
    layers.RandomRotation(0.15),
    layers.RandomZoom(0.10),
    layers.RandomContrast(0.10),
])

base_model = tf.keras.applications.MobileNetV2(
    input_shape=(224, 224, 3),
    include_top=False,
    weights="imagenet"
)
base_model.trainable = False

model = models.Sequential([
    layers.Input(shape=(224, 224, 3)),
    data_augmentation,
    layers.Rescaling(1./127.5, offset=-1),
    base_model,
    layers.GlobalAveragePooling2D(),
    layers.Dropout(0.2),
    layers.Dense(1, activation="sigmoid")
])

n_non = count_images(TRAIN_DIR / "non_recyclable")
n_rec = count_images(TRAIN_DIR / "recyclable")
n_total = n_non + n_rec

class_weight = {
    0: n_total / (2.0 * max(n_non, 1)),  # non_recyclable
    1: n_total / (2.0 * max(n_rec, 1)),  # recyclable
}
print("Train counts:", {"non_recyclable": n_non, "recyclable": n_rec})
print("class_weight:", class_weight)

model.compile(
    optimizer="adam",
    loss="binary_crossentropy",
    metrics=[
        "accuracy",
        tf.keras.metrics.Precision(name="precision"),
        tf.keras.metrics.Recall(name="recall"),
        tf.keras.metrics.AUC(name="auc_roc"),
        tf.keras.metrics.AUC(name="auc_pr", curve="PR"),
    ]
)

callbacks = [
    tf.keras.callbacks.EarlyStopping(
        monitor="val_auc_pr",
        mode="max",
        patience=3,
        restore_best_weights=True
    )
]

EPOCHS = 15
history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=EPOCHS,
    class_weight=class_weight,
    callbacks=callbacks
)

model.save(str(BASE_DIR / "recyclable_model.keras"))

converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()
with open(BASE_DIR / "model.tflite", "wb") as f:
    f.write(tflite_model)

print("Training complete. Model saved as model.tflite")