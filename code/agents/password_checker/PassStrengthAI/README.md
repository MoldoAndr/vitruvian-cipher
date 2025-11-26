# Password Strength Estimation AI

Password Strength Estimation AI is an open-source project that utilizes machine learning techniques to estimate the strength of passwords. The AI model is trained on a large dataset of randomly generated passwords, labeled using the zxcvbn password estimation library. This project is implemented using TensorFlow.

## Disclaimer
**The AI model is currently in beta state and may produce inaccurate predictions of password strength. Use the results with caution and always consider additional security measures.**

## Features

- Estimates the strength of passwords using machine learning.
- Trained on a diverse dataset of randomly generated passwords.
- Includes cracked passwords from SecLists to enhance the training dataset.
- Created with TensorFlow for robust and efficient computation.

## Usage

To train the AI model or load a pre-trained model, follow the instructions below:

### Prerequisites
- Python 3.x
- TensorFlow library
- Other required Python packages (`pip install -r requirements.txt`)

### Training

1. Provide a `config.json` file in the root directory of the project. Alternatively, use the `--config <path_to_config>` parameter to specify the configuration file's path.
2. In the `config.json` file, specify the following keys:
   - `cracked_passwords_url`: URL to an online `.txt` file containing cracked passwords.
   - `csv_password_dataset`: Path to a local `.csv` file containing passwords and their strength score from 0 to 4.
3. Execute the training process using the following command: `python pass_strength_ai.py --train <model_version>`

### Kaggle training

- If you prefer running the training job on Kaggle, open `notebooks/pass_strength_ai_training.ipynb` in a Kaggle Notebook and follow the steps in `docs/kaggle_training.md` to configure the inputs, run the pipeline, and export the trained model artifacts.

### Use a pre-trained model

To estimate passwords using a trained model, follow these steps:

1. Download a pretrained model [here](https://github.com/OffRange/PassStrengthAI/releases)
2. Execute the loading process using the following command: `python pass_strength_ai.py --execute <path_to_saved_model>`

### Quick model smoke test

- After training (locally or via Kaggle), run `python test_saved_model.py --model <path_to_saved_model.keras>` to score a few sample passwords and confirm the export works. Use `--password` or `--file` to control which passwords get evaluated.


## Contributing

Contributions to this project are highly appreciated. You can contribute in the following ways:

- Report issues or suggestions for improvement.
- Submit pull requests to enhance the functionality or codebase.
- Share additional password datasets for further training and evaluation.

Please review the [CONTRIBUTING.md](CONTRIBUTING.md) file for more information on how to contribute to this project.

## License

This project is licensed under the [MIT License](LICENSE.md).
