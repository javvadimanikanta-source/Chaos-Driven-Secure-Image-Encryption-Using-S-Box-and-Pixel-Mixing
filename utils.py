import numpy as np
import hashlib
import math


def generate_parameters(key):
    h = hashlib.sha256(key.encode()).hexdigest()
    h = int(h, 16)

    x0 = 0.1 + (h % 10**12)/10**12 * 0.8
    a = 4.7 + ((h >> 64) % 10**12)/10**12 * (17 - 4.7)
    beta = -1 + ((h >> 128) % 10**12)/10**12 * 2

    return x0, a, beta


def chaotic_sequence(size, x0, a, beta):

    x = x0

    for _ in range(5000):
        x = math.exp(-a * (x**2)) + beta
        x = x % 1

    seq = np.zeros(size)

    for i in range(size):
        x = math.exp(-a * (x**2)) + beta
        x = x % 1
        seq[i] = x

    return seq


def generate_sbox(x0, a, beta):
    chaos = chaotic_sequence(256, x0, a, beta)
    idx = np.argsort(chaos)
    return idx.astype(np.uint8)


def inverse_sbox(sbox):
    inv = np.zeros_like(sbox)

    for i in range(256):
        inv[sbox[i]] = i

    return inv