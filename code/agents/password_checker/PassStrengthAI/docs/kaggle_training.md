# Kaggle Training Guide

This guide documents how to train the Password Strength AI model end-to-end inside a Kaggle Notebook using the provided workflow at `notebooks/pass_strength_ai_training.ipynb`.

## 1. Prepare the data

- Export or create a Kaggle Dataset that contains the `pass_with_strength.csv` file from this repository.
- Confirm the cracked password list URL in `config.json` is accessible from Kaggle. The notebook defaults to the SecLists wordlist used in the project.

## 2. Configure the notebook

1. Open Kaggle, create a new Notebook, and attach the dataset that contains `pass_with_strength.csv`.
2. Upload `notebooks/pass_strength_ai_training.ipynb` from this repository and set it as the notebook body.
3. Edit the configuration cell near the top of the notebook:
   - Update `CSV_PATH` to match the mounted Kaggle dataset path (e.g. `/kaggle/input/<dataset-name>/pass_with_strength.csv`).
   - Adjust `PASSWORD_MAX_LENGTH`, `TEST_RATIO`, and `MAX_SAMPLES_PER_CLASS` to control the dataset size and balance.
   - Tune `BATCH_SIZE`, `EPOCHS`, `PATIENCE`, and `LEARNING_RATE` if you need faster runs or higher accuracy.

## 3. Training workflow

The notebook mirrors the Python training script and performs the following steps:

1. **Imports and seeding** – ensures reproducibility across runs.
2. **Data ingestion** – downloads the cracked password list, parses the CSV, filters passwords that exceed the configured maximum length, and shuffles each strength bucket.
3. **Balanced split** – creates even class distributions (up to the chosen cap) and partitions train/test datasets with the requested ratio.
4. **Vectorisation** – converts each password into a one-hot encoded tensor of shape `(max_length, |charset|)`.
5. **Model build** – instantiates the CNN + BiLSTM architecture from `ai/model_v1.py` and compiles it with `Adam` + categorical cross-entropy.
6. **Training** – runs `model.fit` with early stopping on validation loss and records the history.
7. **Evaluation** – prints final test metrics and plots loss/accuracy curves.
8. **Export** – saves a Keras SavedModel bundle and the corresponding `.tflite` file inside `/kaggle/working/pass_strength_model`.
9. **Interactive checks** – provides a helper cell to score sample passwords with the trained model.

## 4. Collecting the artifacts

- After the notebook finishes, open the Kaggle **Output** tab and download the `pass_strength_model` directory.
- Copy the exported `.tflite` file (and optionally the SavedModel) into your repository’s `models/` folder.
- Record any training metrics (accuracy, loss, dataset size) for reproducibility.

## 5. Maintenance tips

- Re-run the notebook when you update the dataset or tweak hyperparameters so the saved model stays in sync.
- Keep an eye on the label balance table; if a class has zero samples, lower `PASSWORD_MAX_LENGTH` or augment the dataset.
- If you need GPU acceleration on Kaggle, enable GPU in the notebook settings before running the pipeline.
