import numpy as np
import tensorflow as tf
from tensorflow import keras
import cv2
import pefile

def get_gradcam_heatmap(model, img_array, last_conv_layer_name):
    # 1. Create a model that maps the input image to the activations of the last conv layer
    grad_model = tf.keras.models.Model(
        [model.inputs], [model.get_layer(last_conv_layer_name).output, model.output]
    )

    # 2. Compute the gradient of the top predicted class for the input image
    with tf.GradientTape() as tape:
        last_conv_layer_output, preds = grad_model(img_array)
        class_channel = preds[:, 0]

    # 3. Gradient of the output neuron wrt the output feature map of the last conv layer
    grads = tape.gradient(class_channel, last_conv_layer_output)

    # 4. Mean intensity of the gradient over a specific feature map channel
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

    # 5. Multiply each channel in the feature map by "how important this channel is"
    last_conv_layer_output = last_conv_layer_output[0]
    heatmap = last_conv_layer_output @ pooled_grads[..., tf.newaxis]
    heatmap = tf.squeeze(heatmap)

    # 6. Normalize the heatmap between 0 & 1
    heatmap = tf.maximum(heatmap, 0) / tf.math.reduce_max(heatmap)
    return heatmap.numpy()

def get_suspicious_sections(file_path, heatmap, original_width):
    """Maps heatmap 'hot zones' back to PE sections."""
    pe = pefile.PE(file_path)
    # Find coordinates of highest activation (e.g., top 10% of heatmap)
    threshold = 0.8
    hot_indices = np.where(heatmap > threshold)
    
    # Map 128x128 back to original byte offsets
    # This is a simplified approximation
    suspicious_sections = set()
    for y, x in zip(hot_indices[0], hot_indices[1]):
        # Reverse the 128x128 resize logic roughly
        # Note: This is an estimation; exact mapping requires scaling y by (original_height/128)
        byte_offset = (y * (original_width // 128)) * original_width + (x * (original_width // 128))
        
        for section in pe.sections:
            if section.PointerToRawData <= byte_offset < (section.PointerToRawData + section.SizeOfRawData):
                suspicious_sections.add(section.Name.decode().strip('\x00'))
    
    return list(suspicious_sections)