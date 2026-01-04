import os
import csv
import re
from pathlib import Path


def parse_challenge_file(filepath):
    """Parse a challenge file and extract metadata."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract the question (everything before "---")
    parts = content.split('---')
    question = parts[0].strip()

    # Extract technical details
    metadata = {}
    for line in parts[1].split('\n') if len(parts) > 1 else []:
        match = re.match(r'([^:]+):\s*(.*)', line)
        if match:
            key, value = match.groups()
            metadata[key.strip()] = value.strip()

    return {
        'input': question,
        'hint': metadata.get('hint', ''),
        'flag': metadata.get('flag', ''),
        'archetype': metadata.get('archetype', ''),
        'subtype': metadata.get('subtype', ''),
        'difficulty': metadata.get('difficulty', 'unknown')
    }


def main():
    challenges_dir = Path('training_challenges/challenges')
    output_csv = Path('training_challenges/all_challenges.csv')

    if not challenges_dir.exists():
        print(f"Error: Directory {challenges_dir} not found!")
        return

    # Get all challenge files
    challenge_files = sorted(challenges_dir.glob('challenge_*.txt'))
    print(f"Found {len(challenge_files)} challenge files")

    if len(challenge_files) == 0:
        print("No challenge files found!")
        return

    # Parse all challenges
    challenges = []
    for filepath in challenge_files:
        try:
            challenge_data = parse_challenge_file(filepath)
            challenges.append(challenge_data)
            print(f"Parsed: {filepath.name}")
        except Exception as e:
            print(f"Error parsing {filepath.name}: {e}")

    # Write to CSV
    if challenges:
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['input', 'hint', 'flag', 'archetype', 'subtype', 'difficulty'])
            writer.writeheader()
            writer.writerows(challenges)

        print(f"\n✅ Successfully created CSV with {len(challenges)} challenges!")
        print(f"📁 Saved to: {output_csv}")
        print(f"📊 File size: {output_csv.stat().st_size / 1024:.2f} KB")
    else:
        print("No valid challenges found to write!")


if __name__ == '__main__':
    main()
