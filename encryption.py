import cv2
import numpy as np

from utils import (
    generate_parameters,
    chaotic_sequence,
    generate_sbox
)


def substitute(channel, sbox):
    return sbox[channel]


def diffusion(R, G, B, x0, a, beta):

    rows, cols = R.shape
    total_pixels = rows * cols

    chaos = chaotic_sequence(total_pixels * 3, x0 + 0.1234, a, beta)
    key_stream = (np.floor(chaos * 1e14) % 256).astype(np.uint8)

    Rf = R.flatten().astype(np.int32)
    Gf = G.flatten().astype(np.int32)
    Bf = B.flatten().astype(np.int32)

    CR = np.zeros_like(Rf)
    CG = np.zeros_like(Gf)
    CB = np.zeros_like(Bf)

    CR[0] = (Rf[0] + int(key_stream[0])) % 256
    CG[0] = (Gf[0] + int(key_stream[1]) + CR[0]) % 256
    CB[0] = (Bf[0] + int(key_stream[2]) + CG[0]) % 256

    k = 3

    for i in range(1, total_pixels):
        CR[i] = (Rf[i] + int(key_stream[k]) + CB[i-1]) % 256
        CG[i] = (Gf[i] + int(key_stream[k+1]) + CR[i]) % 256
        CB[i] = (Bf[i] + int(key_stream[k+2]) + CG[i]) % 256
        k += 3

    for i in range(total_pixels-2, -1, -1):
        CR[i] = (CR[i] + CB[i+1]) % 256
        CG[i] = (CG[i] + CR[i]) % 256
        CB[i] = (CB[i] + CG[i]) % 256

    return (
        CR.astype(np.uint8).reshape(rows, cols),
        CG.astype(np.uint8).reshape(rows, cols),
        CB.astype(np.uint8).reshape(rows, cols)
    )


def shuffle(R, G, B, x0, a, beta):

    rows, cols = R.shape
    total_pixels = rows * cols

    chaos = chaotic_sequence(total_pixels, x0 + 0.5678, a, beta)

    rand_vals = (
        np.floor(chaos * 1e14)
    ).astype(np.uint64)

    Rf = R.flatten()
    Gf = G.flatten()
    Bf = B.flatten()

    for i in range(total_pixels - 1, 0, -1):

        j = rand_vals[i] % (i + 1)

        Rf[i], Rf[j] = Rf[j], Rf[i]
        Gf[i], Gf[j] = Gf[j], Gf[i]
        Bf[i], Bf[j] = Bf[j], Bf[i]

    return (
        Rf.reshape(rows, cols),
        Gf.reshape(rows, cols),
        Bf.reshape(rows, cols)
    )


def encrypt_image(image_path, secret_key):

    import os

    if not os.path.exists(image_path):
        raise ValueError(
            f"File does not exist: {image_path}"
        )

    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(
            f"OpenCV cannot read image: {image_path}"
        )

    image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )

    R, G, B = cv2.split(image)

    x0, a, beta = generate_parameters(secret_key)

    sbox = generate_sbox(x0, a, beta)

    R = substitute(R, sbox)
    G = substitute(G, sbox)
    B = substitute(B, sbox)

    R, G, B = diffusion(
        R, G, B,
        x0, a, beta
    )

    R, G, B = shuffle(
        R, G, B,
        x0, a, beta
    )

    encrypted = cv2.merge([R, G, B])

    return encrypted