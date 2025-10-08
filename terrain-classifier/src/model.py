import tensorflow as tf
from tensorflow.keras.layers import Input, Conv2D, UpSampling2D, concatenate
from tensorflow.keras.models import Model
from tensorflow.keras.applications import ResNet50

def build_fcn_resnet(input_shape, num_classes):
    """
    Builds a Fully Convolutional Network (FCN) with a ResNet50 backbone.

    :param input_shape: Tuple (height, width, channels) for the input images.
    :param num_classes: The number of classes for the output segmentation map.
    :return: A Keras Model instance.
    """
    inputs = Input(input_shape)

    # 1. Encoder (ResNet50 Backbone)
    # Load ResNet50 with pre-trained ImageNet weights, excluding the top classification layers.
    # The input tensor is specified to connect our input to the ResNet model.
    resnet_base = ResNet50(include_top=False, weights='imagenet', input_tensor=inputs)

    # Get outputs from intermediate layers for skip connections
    # Layer names are specific to the ResNet50 architecture in Keras.
    skip_1 = resnet_base.get_layer('conv1_relu').output          # 128x128
    skip_2 = resnet_base.get_layer('conv2_block3_out').output     # 64x64
    skip_3 = resnet_base.get_layer('conv3_block4_out').output     # 32x32
    skip_4 = resnet_base.get_layer('conv4_block6_out').output     # 16x16

    # Bridge from encoder to decoder
    bridge = resnet_base.get_layer('conv5_block3_out').output     # 8x8

    # 2. Decoder (FCN with Skip Connections)
    # Upsample from the bridge and concatenate with the last skip connection (skip_4)
    x = UpSampling2D(size=(2, 2))(bridge)
    x = concatenate([x, skip_4])
    x = Conv2D(512, (3, 3), activation='relu', padding='same')(x)
    x = Conv2D(512, (3, 3), activation='relu', padding='same')(x)

    # Upsample and concatenate with skip_3
    x = UpSampling2D(size=(2, 2))(x)
    x = concatenate([x, skip_3])
    x = Conv2D(256, (3, 3), activation='relu', padding='same')(x)
    x = Conv2D(256, (3, 3), activation='relu', padding='same')(x)

    # Upsample and concatenate with skip_2
    x = UpSampling2D(size=(2, 2))(x)
    x = concatenate([x, skip_2])
    x = Conv2D(128, (3, 3), activation='relu', padding='same')(x)
    x = Conv2D(128, (3, 3), activation='relu', padding='same')(x)

    # Upsample and concatenate with skip_1
    x = UpSampling2D(size=(2, 2))(x)
    x = concatenate([x, skip_1])
    x = Conv2D(64, (3, 3), activation='relu', padding='same')(x)
    x = Conv2D(64, (3, 3), activation='relu', padding='same')(x)

    # Final upsampling to the original input size
    x = UpSampling2D(size=(2, 2))(x)

    # 3. Output Layer
    # Use a 1x1 convolution to map the features to the number of classes
    outputs = Conv2D(num_classes, (1, 1), activation='softmax')(x)

    # Create the final model
    model = Model(inputs=inputs, outputs=outputs)

    return model

if __name__ == '__main__':
    # Example of how to build and summarize the model
    # (This part is for testing and won't be run during the main pipeline)
    input_shape = (256, 256, 3)
    num_classes = 6 # Example: Flat, Hill, Low Mtn, High Mtn, Valley, Ridge
    model = build_fcn_resnet(input_shape, num_classes)
    model.summary()