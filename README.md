# Chaos-Driven Secure Image Encryption Using S-Box and Pixel Mixing

## Overview

This project is a secure image encryption and decryption web application developed using Python and Flask.

The main aim of the project is to protect digital images from unauthorized access by applying chaos-based encryption techniques. The system combines chaotic sequence generation, dynamic S-Box substitution, diffusion, and pixel permutation to transform an image into an encrypted form. The original image can only be recovered using the correct secret key.

The project provides a simple web interface where users can upload images, encrypt them, and decrypt them when needed.

---

## Features

* Image encryption and decryption
* Secret key based security
* Dynamic S-Box generation
* Pixel mixing and permutation
* RGB channel processing
* Web-based user interface
* User authentication and history management
* SQLite database integration

---

## Technologies Used

* Python
* Flask
* OpenCV
* NumPy
* SQLite
* HTML
* CSS

---

## How It Works

### Encryption Process

1. The user uploads an image and provides a secret key.
2. The image is split into Red, Green, and Blue channels.
3. The secret key is processed using SHA-256 hashing.
4. Chaotic sequences are generated based on the hashed values.
5. Dynamic S-Box substitution is applied to introduce non-linearity.
6. Diffusion is performed using XOR operations.
7. Pixel positions are shuffled using permutation techniques.
8. The transformed image is produced as the encrypted output.

### Decryption Process

The decryption process performs the reverse operations using the same secret key:

1. Inverse pixel permutation
2. Reverse diffusion
3. Inverse S-Box substitution
4. RGB channel reconstruction

After these steps, the original image is recovered successfully.

---

## Security Evaluation

The encryption scheme was analyzed using:

* Entropy Analysis
* Correlation Analysis
* Histogram Analysis
* NPCR
* UACI

These metrics help evaluate the randomness and effectiveness of the encryption process.

---

## Project Structure

```text
app.py
encryption.py
decryption.py
utils.py

templates/
static/

database.db
```

---

## Applications

* Secure image sharing
* Image privacy protection
* Secure storage of digital images
* Educational study of chaos-based cryptography
* Research in image security techniques

---

## Future Improvements

* Support for larger image datasets
* Real-time image encryption
* Cloud deployment
* Additional encryption techniques
* Performance optimization for large images



