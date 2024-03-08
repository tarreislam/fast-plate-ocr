"""
Model definitions for the FastLP OCR.
"""
from keras.activations import softmax
from keras.layers import (
    Activation,
    Concatenate,
    Dense,
    Dropout,
    GlobalAveragePooling2D,
    Input,
    Lambda,
    MaxPool2D,
    Reshape,
)
from keras.models import Model

from fast_lp_ocr.layer_blocks import block_bn, block_bn_sep_conv_l2, block_no_activation


def modelo_2m(h: int, w: int, dense: bool = True) -> Model:
    """
    2M parameter model that uses normal Convolutional layers (not Depthwise Convolutional layers).
    """
    input_tensor = Input((h, w, 1))
    # Backbone
    x, _ = block_bn(input_tensor)
    x, _ = block_bn(x, k=3, n_c=32, s=1, padding="same")
    x, _ = block_bn(x, k=3, n_c=32, s=1, padding="same")
    x, _ = block_bn(x, k=1, n_c=64, s=1, padding="same")
    x = MaxPool2D(pool_size=(3, 3), strides=(3, 3), padding="same")(x)
    x, _ = block_bn(x, k=3, n_c=64, s=1, padding="same")
    x, _ = block_bn(x, k=3, n_c=128, s=1, padding="same")
    x, _ = block_bn(x, k=1, n_c=128, s=1, padding="same")
    x = MaxPool2D(pool_size=(2, 2), strides=(2, 2), padding="same")(x)
    x, _ = block_bn(x, k=3, n_c=128, s=1, padding="same")
    x, _ = block_bn(x, k=3, n_c=128, s=1, padding="same")
    x, _ = block_bn(x, k=1, n_c=256, s=1, padding="same")
    x = MaxPool2D(pool_size=(2, 2), strides=(2, 2), padding="same")(x)
    x, _ = block_bn(x, k=3, n_c=256, s=1, padding="same")
    x = MaxPool2D(pool_size=(2, 2), strides=(2, 2), padding="same")(x)
    x, _ = block_bn(x, k=1, n_c=512, s=1, padding="same")
    x = MaxPool2D(pool_size=(2, 2), strides=(2, 2), padding="same")(x)
    x, _ = block_bn(x, k=1, n_c=1024, s=1, padding="same")
    x = head(x) if dense else head_no_fc(x)
    return Model(inputs=input_tensor, outputs=x)


def modelo_1m_cpu(h: int, w: int, dense: bool = True) -> Model:
    """
    1.2M parameter model that uses Depthwise Convolutional layers, more suitable for low-end devices
    """
    input_tensor = Input((h, w, 1))
    x, _ = block_bn(input_tensor, k=3, n_c=32, s=1, padding="same")
    x, _ = block_bn(x, k=3, n_c=64, s=1, padding="same")
    x = MaxPool2D(pool_size=(2, 2), strides=(2, 2), padding="same")(x)
    x, _ = block_bn(x, k=3, n_c=64, s=1, padding="same")
    x, _ = block_bn(x, k=3, n_c=128, s=1, padding="same")
    x = MaxPool2D(pool_size=(2, 2), strides=(2, 2), padding="same")(x)
    x, _ = block_bn(x, k=1, n_c=128, s=1, padding="same")
    x = MaxPool2D(pool_size=(2, 2), strides=(2, 2), padding="same")(x)
    x, _ = block_bn_sep_conv_l2(x, k=3, n_c=128, s=1, padding="same", depth_multiplier=1)
    x, _ = block_bn(x, k=1, n_c=256, s=1, padding="same")
    x = MaxPool2D(pool_size=(2, 2), strides=(2, 2), padding="same")(x)
    x, _ = block_bn_sep_conv_l2(x, k=3, n_c=256, s=1, padding="same", depth_multiplier=1)
    x, _ = block_bn_sep_conv_l2(x, k=1, n_c=512, s=1, padding="same", depth_multiplier=1)
    x = MaxPool2D(pool_size=(2, 2), strides=(2, 2), padding="same")(x)
    x, _ = block_bn(x, k=1, n_c=1024, s=1, padding="same")
    x = head(x) if dense else head_no_fc(x)
    return Model(inputs=input_tensor, outputs=x)


def head(x):
    """
    Se encarga de la parte de clasificacion
    de caracteres e incluye Fully Connected Layers
    """
    x = GlobalAveragePooling2D()(x)
    # dropout for more robust learning
    x = Dropout(0.5)(x)
    x1 = Dense(units=37)(x)
    x2 = Dense(units=37)(x)
    x3 = Dense(units=37)(x)
    x4 = Dense(units=37)(x)
    x5 = Dense(units=37)(x)
    x6 = Dense(units=37)(x)
    x7 = Dense(units=37)(x)
    # Softmax act.
    x1 = Activation(softmax)(x1)
    x2 = Activation(softmax)(x2)
    x3 = Activation(softmax)(x3)
    x4 = Activation(softmax)(x4)
    x5 = Activation(softmax)(x5)
    x6 = Activation(softmax)(x6)
    x7 = Activation(softmax)(x7)
    x = Concatenate()([x1, x2, x3, x4, x5, x6, x7])
    return x


def head_no_fc(x):
    """
    Model head without Fully Connected (FC) layers.
    """
    x = block_no_activation(x, k=1, n_c=7 * 37, s=1, padding="same")
    x = GlobalAveragePooling2D()(x)
    x = Reshape((7, 37, 1))(x)
    return Lambda(lambda x: softmax(x, axis=-2))(x)
