import argparse
import string
from pathlib import Path

import numpy as np
from tensorflow import keras

CHARS = string.ascii_letters + string.digits + string.punctuation
LABEL_LOOKUP = {
    0: "Cracked",
    1: "Ridiculous",
    2: "Weak",
    3: "Moderate",
    4: "Strong",
    5: "Very strong",
}


def one_hot_encode(password: str, max_length: int) -> np.ndarray:
    encoding = np.zeros((max_length, len(CHARS)), dtype=np.float32)
    for position, char in enumerate(password[:max_length]):
        try:
            index = CHARS.index(char)
        except ValueError:
            continue
        encoding[position, index] = 1.0
    return encoding


def prepare_batch(passwords: list[str], max_length: int) -> np.ndarray:
    if not passwords:
        return np.zeros((0, max_length, len(CHARS)), dtype=np.float32)
    return np.stack([one_hot_encode(password, max_length) for password in passwords])


def load_passwords(args: argparse.Namespace) -> list[str]:
    passwords = []
    if args.password:
        passwords.extend(args.password)
    if args.file:
        for line in Path(args.file).read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line:
                passwords.append(line)
    if not passwords:
        passwords = ["password123", "LetMeIn!", "5uP3r$3cur3"]
    return passwords


def main() -> None:
    parser = argparse.ArgumentParser(description="Quickly verify a trained password strength model.")
    parser.add_argument("--model", required=True, help="Path to the saved_model.keras or SavedModel directory.")
    parser.add_argument(
        "--password",
        action="append",
        help="Password to score (supply multiple times for more than one password).",
    )
    parser.add_argument("--file", help="Optional path to a file with one password per line.")
    parser.add_argument(
        "--top-k",
        type=int,
        default=1,
        help="Show the top-k predicted labels and confidence values for each password.",
    )
    args = parser.parse_args()

    model = keras.models.load_model(args.model)
    _, max_length, charset_size = model.input_shape

    if charset_size != len(CHARS):
        print(
            f"Warning: model expects {charset_size} characters but loader defines {len(CHARS)}. "
            "Predictions may be unreliable."
        )

    passwords = load_passwords(args)
    batch = prepare_batch(passwords, max_length)
    if batch.size == 0:
        print("No passwords to evaluate.")
        return

    probabilities = model.predict(batch, verbose=0)
    top_k = max(1, min(args.top_k, probabilities.shape[1]))

    for password, prediction in zip(passwords, probabilities):
        ranked_indices = np.argsort(prediction)[::-1][:top_k]
        ranked_labels = [
            (LABEL_LOOKUP.get(index, f"Class {index}"), float(prediction[index]) * 100.0)
            for index in ranked_indices
        ]
        print(f"{password!r}")
        for label, confidence in ranked_labels:
            print(f"  → {label:<12} {confidence:6.2f}%")


if __name__ == "__main__":
    main()
