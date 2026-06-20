import cv2
import numpy as np

from utils import (
    generate_parameters,
    generate_sbox,
    inverse_sbox,
    chaotic_sequence
)


def inverse_substitute(channel, inv_sbox):
    return inv_sbox[channel]


def inverse_shuffle(R, G, B, x0, a, beta):

    rows, cols = R.shape
    total_pixels = rows * cols

    chaos = chaotic_sequence(total_pixels, x0 + 0.5678, a, beta)

    rand_vals = (
        np.floor(chaos * 1e14)
    ).astype(np.uint64)

    Rf = R.flatten()
    Gf = G.flatten()
    Bf = B.flatten()

    swaps = []

    for i in range(total_pixels - 1, 0, -1):
        j = rand_vals[i] % (i + 1)
        swaps.append((i, j))

    for i, j in reversed(swaps):
        Rf[i], Rf[j] = Rf[j], Rf[i]
        Gf[i], Gf[j] = Gf[j], Gf[i]
        Bf[i], Bf[j] = Bf[j], Bf[i]

    return (
        Rf.reshape(rows, cols),
        Gf.reshape(rows, cols),
        Bf.reshape(rows, cols)
    )


def inverse_diffusion(R, G, B, x0, a, beta):

    rows, cols = R.shape
    total_pixels = rows * cols

    chaos = chaotic_sequence(
        total_pixels * 3,
        x0 + 0.1234,
        a,
        beta
    )

    key_stream = (
        np.floor(chaos * 1e14) % 256
    ).astype(np.uint8)

    CR = R.flatten().astype(int)
    CG = G.flatten().astype(int)
    CB = B.flatten().astype(int)

    for i in range(0, total_pixels - 1):
        CB[i] = (CB[i] - CG[i]) % 256
        CG[i] = (CG[i] - CR[i]) % 256
        CR[i] = (CR[i] - CB[i+1]) % 256

    Rf = np.zeros_like(CR)
    Gf = np.zeros_like(CG)
    Bf = np.zeros_like(CB)

    k = 3 * (total_pixels - 1)

    for i in range(total_pixels - 1, 0, -1):

        Rf[i] = (CR[i] - key_stream[k] - CB[i-1]) % 256
        Gf[i] = (CG[i] - key_stream[k+1] - CR[i]) % 256
        Bf[i] = (CB[i] - key_stream[k+2] - CG[i]) % 256

        k -= 3

    Rf[0] = (CR[0] - key_stream[0]) % 256
    Gf[0] = (CG[0] - key_stream[1] - CR[0]) % 256
    Bf[0] = (CB[0] - key_stream[2] - CG[0]) % 256

    return (
        Rf.astype(np.uint8).reshape(rows, cols),
        Gf.astype(np.uint8).reshape(rows, cols),
        Bf.astype(np.uint8).reshape(rows, cols)
    )


def decrypt_image(image_path, secret_key):

    import os

    print("Decrypt Path:", image_path)
    print("Exists:", os.path.exists(image_path))

    if not os.path.exists(image_path):
        raise ValueError(
            f"Encrypted image not found: {image_path}"
        )

    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(
            f"OpenCV could not read: {image_path}"
        )

    image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )

    R, G, B = cv2.split(image)

    x0, a, beta = generate_parameters(secret_key)

    sbox = generate_sbox(x0, a, beta)
    inv_sbox = inverse_sbox(sbox)

    R, G, B = inverse_shuffle(
        R, G, B,
        x0, a, beta
    )

    R, G, B = inverse_diffusion(
        R, G, B,
        x0, a, beta
    )

    R = inverse_substitute(R, inv_sbox)
    G = inverse_substitute(G, inv_sbox)
    B = inverse_substitute(B, inv_sbox)

    decrypted = cv2.merge([R, G, B])

    return decrypted