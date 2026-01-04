import csv
from pathlib import Path

def filter_valid_challenges():
    input_csv = Path('training_challenges/all_challenges.csv')
    output_csv = Path('training_challenges/all_challenges_filtered.csv')

    valid_challenges = []
    failed_count = 0

    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Check if the challenge is valid (not an error message)
            if 'LLM Story Generation Failed' not in row['input'] and row['input'].strip():
                valid_challenges.append(row)
            else:
                failed_count += 1

    # Write only valid challenges
    if valid_challenges:
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['input', 'hint', 'flag', 'archetype', 'subtype', 'difficulty'])
            writer.writeheader()
            writer.writerows(valid_challenges)

        print(f"✅ Filtered CSV created!")
        print(f"📊 Valid challenges: {len(valid_challenges)}")
        print(f"❌ Failed challenges: {failed_count}")
        print(f"📁 Saved to: {output_csv}")
        print(f"💾 File size: {output_csv.stat().st_size / 1024:.2f} KB")
    else:
        print("❌ No valid challenges found!")

if __name__ == '__main__':
    filter_valid_challenges()
