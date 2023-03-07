import imagehash
from PIL import Image

takeouthash = imagehash.dhash(
    Image.open(
        "/Users/nicolas/Downloads/Perceptual Hash sample files/Google Photos Takeout/2023-02-25T102246-DSCF3482.jpg"
    ),
    hash_size=16,
)
print(takeouthash)
webhash = imagehash.dhash(
    Image.open(
        "/Users/nicolas/Downloads/Perceptual Hash sample files/Google Photos Web Download/2023-02-25T102246-DSCF3482.jpg"
    ),
    hash_size=16,
)
print(webhash)
originalhash = imagehash.dhash(
    Image.open(
        "/Users/nicolas/Downloads/Perceptual Hash sample files/Originals Photos/2023-02-25T102246-DSCF3482.jpg"
    ),
    hash_size=16,
)
print(originalhash)
print(originalhash - webhash)
print(originalhash - takeouthash)  # hamming distance
