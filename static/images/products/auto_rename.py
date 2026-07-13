"""
auto_rename_images.py

Drop this file directly into the folder that has your fruit/vegetable
photos, then run it - no path editing needed. It classifies each image
with a Hugging Face model trained on raw produce photos, and copies it
into a new "renamed" subfolder as <predicted_class>_<original_name>.<ext>,
leaving your original photos untouched. It only ever looks at image files
(.jpg/.jpeg/.png/.webp), so it ignores itself and anything else sitting
in that folder.

When you're happy with the results, delete this .py file - it doesn't
leave anything else behind, just the renamed/ folder and a
renaming_log.csv, both saved next to wherever the script was.

Anything below the confidence threshold (or, if you set ALLOWED_CLASSES,
anything not on that shortlist) becomes unclassified_<original_name>.<ext>.
Every prediction is logged to renaming_log.csv so you can QC results and
retune CONFIDENCE_THRESHOLD if needed.

Setup (run once):
    pip install transformers torch pillow pandas

Run (from inside the folder):
    python auto_rename_images.py

First run downloads and caches the model (~95 MB) from Hugging Face, so it
needs internet access; after that it works offline.
"""

import shutil
from pathlib import Path

import pandas as pd
import torch
from PIL import Image, UnidentifiedImageError
from transformers import AutoImageProcessor, AutoModelForImageClassification

# ---------------- Configuration ----------------
# Self-locating: IMAGE_DIR defaults to wherever this script itself is
# saved. Drop it in your photos folder, run it, delete it when done -
# nothing to edit. Only touch IMAGE_DIR below if you'd rather point it
# at a different folder instead of the script's own location.
SCRIPT_DIR = Path(__file__).resolve().parent
IMAGE_DIR = SCRIPT_DIR
OUTPUT_DIR = SCRIPT_DIR / "renamed"
LOG_PATH = SCRIPT_DIR / "renaming_log.csv"

CONFIDENCE_THRESHOLD = 0.6     # minimum confidence to accept a label
TOP_K = 5                      # how many ranked predictions to keep/log per image

# Trained specifically on raw fruit/vegetable photos (36 classes, ~97% eval
# accuracy on its own test set) - deliberately NOT a "food101"-style model,
# which classifies cooked dishes like "apple_pie" or "sashimi" rather than
# individual produce, and would not work for this task.
MODEL_NAME = "jazzmacedo/fruits-and-vegetables-detector-36"

# This model's 36 classes: apple, banana, beetroot, bell pepper, cabbage,
# capsicum, carrot, cauliflower, chilli pepper, corn, cucumber, eggplant,
# garlic, ginger, grapes, jalepeno, kiwi, lemon, lettuce, mango, onion,
# orange, paprika, pear, peas, pineapple, pomegranate, potato, raddish,
# soy beans, spinach, sweetcorn, sweetpotato, tomato, turnip, watermelon.
# Notably absent: broccoli, strawberry, blueberry, avocado, and anything
# else off that list - those will either get misclassified into the
# nearest-looking class or fall through to "unclassified" depending on
# confidence. Check the "top3" column in the log if that matters for you.

# Optional: restrict ACCEPTED labels to a subset of the classes above
# (e.g. if you know your 120 images only ever cover some of these).
# Leave as None to accept any of the model's 36 classes at face value.
ALLOWED_CLASSES = None  # e.g. {"apple", "banana", "carrot", "tomato"}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def get_image_paths(dir_path: Path):
    """Collect image files by extension. (The original glob patterns only
    matched *.jpg, silently skipping *.jpeg - fixed here.)"""
    d = Path(dir_path)
    if not d.is_dir():
        raise FileNotFoundError(f"Image folder not found: {d.resolve()}")
    paths = [p for p in d.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
    return sorted(paths, key=lambda p: p.name)


def classify_image(image_path: Path, processor, model, device: str, top_k: int):
    img = Image.open(image_path).convert("RGB")
    inputs = processor(images=img, return_tensors="pt").to(device)

    with torch.no_grad():
        logits = model(**inputs).logits
        probs = logits.softmax(dim=-1)[0]

    k = min(top_k, probs.shape[-1])
    top_probs, top_indices = probs.topk(k)
    return [
        {"label": model.config.id2label[idx.item()], "confidence": prob.item()}
        for idx, prob in zip(top_indices, top_probs)
    ]


def pick_final_class(predictions, allowed_classes, threshold):
    """Walk the ranked predictions, return the first one that's both
    allowed and confident enough. Falls through to 'unclassified'."""
    for pred in predictions:
        if allowed_classes is not None and pred["label"] not in allowed_classes:
            continue
        if pred["confidence"] >= threshold:
            return pred["label"], pred["confidence"]
    return "unclassified", predictions[0]["confidence"]


def unique_destination(directory: Path, name: str) -> Path:
    """Avoid silently overwriting if two source images would map to the
    same new filename."""
    candidate = directory / name
    if not candidate.exists():
        return candidate
    stem, ext = candidate.stem, candidate.suffix
    counter = 1
    while candidate.exists():
        candidate = directory / f"{stem}_{counter}{ext}"
        counter += 1
    return candidate


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading {MODEL_NAME} ({device})...")
    processor = AutoImageProcessor.from_pretrained(MODEL_NAME)
    model = AutoModelForImageClassification.from_pretrained(MODEL_NAME).to(device)
    model.eval()

    image_paths = get_image_paths(IMAGE_DIR)
    if not image_paths:
        raise ValueError(f"No images found in {IMAGE_DIR}")

    out_dir = Path(OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    log_rows = []
    for i, img_path in enumerate(image_paths, start=1):
        print(f"[{i}/{len(image_paths)}] {img_path.name}", end=" ")
        try:
            predictions = classify_image(img_path, processor, model, device, TOP_K)
        except (UnidentifiedImageError, OSError) as e:
            print(f"-> SKIPPED (unreadable: {e})")
            log_rows.append({
                "original_name": img_path.name, "predicted_label": None,
                "confidence": None, "final_class": "error",
                "new_name": None, "top3": None,
            })
            continue

        final_class, confidence = pick_final_class(
            predictions, ALLOWED_CLASSES, CONFIDENCE_THRESHOLD
        )

        new_name = f"{final_class}_{img_path.stem}{img_path.suffix}"
        new_path = unique_destination(out_dir, new_name)
        shutil.copy2(img_path, new_path)
        print(f"-> {new_path.name} ({confidence:.0%})")

        top3 = "; ".join(f'{p["label"]}:{p["confidence"]:.2f}' for p in predictions[:3])
        log_rows.append({
            "original_name": img_path.name,
            "predicted_label": predictions[0]["label"],
            "confidence": round(confidence, 4),
            "final_class": final_class,
            "new_name": new_path.name,
            "top3": top3,
        })

    log_df = pd.DataFrame(log_rows)
    log_df.to_csv(LOG_PATH, index=False)

    print(f"\nDone. {len(log_df)} images processed.")
    print(log_df["final_class"].value_counts().to_string())
    print(f"\nRenamed copies -> {out_dir}/")
    print(f"Full log       -> {LOG_PATH}")


if __name__ == "__main__":
    main()
