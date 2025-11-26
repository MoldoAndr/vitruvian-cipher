import random
from typing import Dict, List
from urllib.request import urlopen

from config import CONFIG

lines = urlopen(CONFIG['cracked_passwords_url'])
lines = [line.decode('utf-8').replace('\n', '') for line in lines.readlines()]


def __get_cracked_passwords(max_length: int):
    return [line for line in lines if len(line) <= max_length]


def __load_csv_passwords(csv_path: str):
    passwords_by_strength: Dict[int, List[str]] = {i: [] for i in range(5)}

    with open(csv_path, 'r', encoding='utf-8', errors='ignore') as csv_file:
        for line_number, raw_line in enumerate(csv_file, start=1):
            line = raw_line.strip()
            if not line:
                continue

            try:
                password, strength_raw = line.rsplit(',', 1)
            except ValueError:
                # Skip malformed lines that cannot be split into password/strength
                continue

            strength_raw = strength_raw.strip()
            if not strength_raw.isdigit():
                continue

            strength = int(strength_raw)
            if strength not in passwords_by_strength:
                continue

            passwords_by_strength[strength].append(password)

    for strength_list in passwords_by_strength.values():
        random.shuffle(strength_list)

    return (
        passwords_by_strength[0],
        passwords_by_strength[1],
        passwords_by_strength[2],
        passwords_by_strength[3],
        passwords_by_strength[4],
    )


poor, weak, moderate, ok, strong = __load_csv_passwords(CONFIG['csv_password_dataset'])

LABEL_LOOKUP = {
    0: "Cracked",
    1: "Ridiculous",
    2: "Weak",
    3: "Moderate",
    4: "Strong",
    5: "Very strong"
}


def get_dataset(max_length, test_ratio=.3):
    print(f'Dataset with {max_length}-character passwords and {test_ratio} test ratio is loaded')
    class_passwords = {
        0: __get_cracked_passwords(max_length),
        1: [password for password in poor if len(password) <= max_length],
        2: [password for password in weak if len(password) <= max_length],
        3: [password for password in moderate if len(password) <= max_length],
        4: [password for password in ok if len(password) <= max_length],
        5: [password for password in strong if len(password) <= max_length],
    }

    available_lengths = [len(passwords) for label, passwords in class_passwords.items() if label != 0 and len(passwords) > 0]
    if not available_lengths:
        raise ValueError('No CSV passwords available to build the dataset.')

    min_dataset_length = min(available_lengths)
    if min_dataset_length == 0:
        raise ValueError('Dataset does not contain enough samples for any strength category.')

    train_passwords: List[str] = []
    train_labels: List[int] = []
    test_passwords: List[str] = []
    test_labels: List[int] = []

    def add_samples(passwords: List[str], label: int, limit: int):
        if not passwords or limit == 0:
            return
        selected = passwords[:limit]
        random.shuffle(selected)
        test_count = max(1, int(len(selected) * test_ratio))
        if test_count >= len(selected):
            test_count = len(selected) // 2 or 1

        test_passwords.extend(selected[:test_count])
        test_labels.extend([label] * test_count)

        train_passwords.extend(selected[test_count:])
        train_labels.extend([label] * (len(selected) - test_count))

    add_samples(class_passwords[0], 0, min_dataset_length)
    add_samples(class_passwords[1], 1, min(len(class_passwords[1]), min_dataset_length))
    add_samples(class_passwords[2], 2, min(len(class_passwords[2]), min_dataset_length))
    add_samples(class_passwords[3], 3, min(len(class_passwords[3]), min_dataset_length))
    add_samples(class_passwords[4], 4, min(len(class_passwords[4]), min_dataset_length))
    add_samples(class_passwords[5], 5, min(len(class_passwords[5]), min_dataset_length))

    if not train_passwords or not test_passwords:
        raise ValueError('Failed to generate train/test splits; check dataset size and configuration.')

    train_combined = list(zip(train_passwords, train_labels))
    random.shuffle(train_combined)
    train_passwords, train_labels = zip(*train_combined)

    test_combined = list(zip(test_passwords, test_labels))
    random.shuffle(test_combined)
    test_passwords, test_labels = zip(*test_combined)

    return Dataset((list(train_passwords), list(train_labels)), (list(test_passwords), list(test_labels)))


class Dataset:
    def __init__(self, train_dataset, test_dataset):
        self.train_dataset = train_dataset
        self.test_dataset = test_dataset
        self.total = len(self.train_dataset[0])

    def print_stats(self):
        length = len(max(LABEL_LOOKUP.values(), key=len))
        for index in LABEL_LOOKUP:
            print(f'{LABEL_LOOKUP[index]} {" " * (length - len(LABEL_LOOKUP[index]))}: {self.train_dataset[1].count(index):,}')

        print(f'Total {" " * (length - 5)}: {self.total:,}')
