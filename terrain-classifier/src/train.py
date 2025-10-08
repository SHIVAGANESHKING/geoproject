import os
import argparse
import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split
from model import build_fcn_resnet
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping
import matplotlib.pyplot as plt

# --- Configuration ---
PROCESSED_DATA_DIR = "data/processed"
MODELS_DIR = "models"
INPUT_SHAPE = (256, 256, 3) # Height, Width, Channels (Elevation, Slope, Aspect)
NUM_CLASSES = 7 # 6 classes + 1 background class (0)
BATCH_SIZE = 16
EPOCHS = 50

def load_data_paths(data_dir):
    """Loads and returns sorted lists of image and mask file paths."""
    image_dir = os.path.join(data_dir, "images")
    mask_dir = os.path.join(data_dir, "masks")

    image_files = sorted([os.path.join(image_dir, f) for f in os.listdir(image_dir) if f.endswith('.npy')])
    mask_files = sorted([os.path.join(mask_dir, f) for f in os.listdir(mask_dir) if f.endswith('.npy')])

    assert len(image_files) == len(mask_files), "Mismatch between number of images and masks."
    return image_files, mask_files

def parse_function(image_path, mask_path):
    """Loads and decodes a single image and mask from their file paths."""
    image_string = tf.io.read_file(image_path)
    image = tf.numpy_function(np.load, [image_string], tf.float32)
    image.set_shape(INPUT_SHAPE)

    mask_string = tf.io.read_file(mask_path)
    mask = tf.numpy_function(np.load, [mask_string], tf.uint8)
    mask = tf.one_hot(mask, NUM_CLASSES)
    mask.set_shape((INPUT_SHAPE[0], INPUT_SHAPE[1], NUM_CLASSES))

    return image, mask

def create_dataset(image_paths, mask_paths, batch_size):
    """Creates a tf.data.Dataset from file paths."""
    dataset = tf.data.Dataset.from_tensor_slices((image_paths, mask_paths))
    dataset = dataset.map(parse_function, num_parallel_calls=tf.data.AUTOTUNE)
    dataset = dataset.shuffle(buffer_size=1000).batch(batch_size).prefetch(buffer_size=tf.data.AUTOTUNE)
    return dataset

def dice_loss(y_true, y_pred, smooth=1e-6):
    """Calculates the Dice loss, a common metric for segmentation tasks."""
    y_true_f = tf.keras.backend.flatten(tf.cast(y_true, tf.float32))
    y_pred_f = tf.keras.backend.flatten(y_pred)
    intersection = tf.keras.backend.sum(y_true_f * y_pred_f)
    return 1 - (2. * intersection + smooth) / (tf.keras.backend.sum(y_true_f) + tf.keras.backend.sum(y_pred_f) + smooth)

def combined_loss(y_true, y_pred):
    """Combines Categorical Cross-Entropy and Dice Loss."""
    cce = tf.keras.losses.categorical_crossentropy(y_true, y_pred)
    dice = dice_loss(y_true, y_pred)
    return cce + dice

def main(args):
    """Main function to run the model training."""
    os.makedirs(MODELS_DIR, exist_ok=True)

    # 1. Load data paths and split into training and validation sets
    image_paths, mask_paths = load_data_paths(args.data_dir)
    train_images, val_images, train_masks, val_masks = train_test_split(
        image_paths, mask_paths, test_size=0.2, random_state=42
    )

    # 2. Create tf.data.Dataset objects
    train_dataset = create_dataset(train_images, train_masks, BATCH_SIZE)
    val_dataset = create_dataset(val_images, val_masks, BATCH_SIZE)

    # 3. Build and compile the model
    model = build_fcn_resnet(input_shape=INPUT_SHAPE, num_classes=NUM_CLASSES)
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4),
                  loss=combined_loss,
                  metrics=['accuracy', dice_loss])

    model.summary()

    # 4. Set up callbacks
    checkpoint_path = os.path.join(MODELS_DIR, "fcn_resnet_best.keras")
    model_checkpoint = ModelCheckpoint(checkpoint_path, save_best_only=True, monitor='val_loss', mode='min', verbose=1)
    early_stopping = EarlyStopping(monitor='val_loss', patience=10, verbose=1, mode='min', restore_best_weights=True)

    # 5. Start training
    print("\n--- Starting Model Training ---")
    history = model.fit(
        train_dataset,
        epochs=EPOCHS,
        validation_data=val_dataset,
        callbacks=[model_checkpoint, early_stopping]
    )

    # 6. Plot and save training history
    plt.figure(figsize=(12, 4))
    plt.subplot(1, 2, 1)
    plt.plot(history.history['loss'], label='Training Loss')
    plt.plot(history.history['val_loss'], label='Validation Loss')
    plt.title('Loss Over Epochs')
    plt.legend()

    plt.subplot(1, 2, 2)
    plt.plot(history.history['accuracy'], label='Training Accuracy')
    plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
    plt.title('Accuracy Over Epochs')
    plt.legend()

    plt.savefig(os.path.join(MODELS_DIR, "training_history.png"))
    print(f"\nTraining complete. Best model saved to {checkpoint_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train an FCN-ResNet model for terrain classification.")
    parser.add_argument("--data_dir", default=PROCESSED_DATA_DIR, help="Directory with preprocessed data.")

    args = parser.parse_args()
    main(args)