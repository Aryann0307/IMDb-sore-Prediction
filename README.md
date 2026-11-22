# 🎬 IMDb Movie Rating Predictor

Predict a movie's IMDb rating from just its **genres**, **release year** and **runtime**, using a Random Forest model trained on 1,000 popular movies. The project includes the full data-science notebook and a **Tkinter desktop app (CineRate)** that serves the trained model.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-Random%20Forest-F7931E?logo=scikitlearn&logoColor=white)
![Tkinter](https://img.shields.io/badge/Tkinter-desktop%20app-4B8BBE)

<!--
  Add a screenshot after you upload it to the repo, for example:
  ![CineRate desktop app](screenshots/desktop_app.png)
-->

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Dataset](#-dataset)
- [Methodology](#-methodology)
- [Results](#-results)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [How the App Makes a Prediction](#-how-the-app-makes-a-prediction)
- [Limitations](#-limitations)
- [Future Improvements](#-future-improvements)
- [Tech Stack](#-tech-stack)
- [Author](#-author)

---

## 🔎 Overview

The goal is to see how well a movie's rating can be estimated from basic, easy-to-know details, without using anything that only exists after release (such as votes or revenue).

| | |
|---|---|
| **Input** | One or more genres, release year, runtime (minutes) |
| **Output** | Estimated IMDb rating out of 10 |
| **Model** | Random Forest Regressor (200 trees, max depth 10) |
| **Interface** | Desktop app built with Tkinter |

## ✨ Features

- **End-to-end ML workflow**: exploration, cleaning, feature engineering, model comparison and model export, all in one documented notebook.
- **Three models compared**: Linear Regression, Decision Tree and Random Forest, evaluated with MAE, MSE, RMSE and R².
- **Multi-genre support**: movies can have several genres at once, handled with `MultiLabelBinarizer`.
- **Desktop app (CineRate)**: a minimal, scrollable Tkinter interface with genre chips, input validation and an animated rating ring.
- **Portable model file**: the model, the genre encoder and the feature order are bundled in a single `movie_rating_model.pkl`.

## 📊 Dataset

The data comes from `IMDB-Movie-Data.csv` (IMDb movie data from 2006 to 2016, originally shared on Kaggle).

| Property | Value |
|---|---|
| Movies | 1,000 |
| Columns | 12 (Rank, Title, Genre, Description, Director, Actors, Year, Runtime, Rating, Votes, Revenue, Metascore) |
| Release years | 2006 to 2016 |
| Runtime range | 66 to 191 minutes |
| Rating range | 1.9 to 9.0 (average 6.72) |
| Unique genres | 20 |

Only four columns are used for modelling:

| Role | Column |
|---|---|
| Features | `Genre`, `Year`, `Runtime (Minutes)` |
| Target | `Rating` |

## 🧪 Methodology

1. **Exploratory data analysis**: rating distribution, rating by genre, runtime vs rating, and rating trend by year.
2. **Cleaning**: keep the four relevant columns, convert them to numeric types and check for missing values.
3. **Genre encoding**: each movie's genre string (for example `"Action,Adventure,Sci-Fi"`) is split into a list and one-hot encoded into 20 genre columns with `MultiLabelBinarizer`. The encoder is fitted on the training set only, to avoid data leakage.
4. **Train / test split**: 80% training (800 movies) and 20% testing (200 movies), with `random_state=42`.
5. **Model training**: Linear Regression, Decision Tree (`max_depth=5`) and Random Forest (`n_estimators=200`, `max_depth=10`).
6. **Evaluation and export**: the best model (Random Forest) is saved together with the encoder and the feature column order.

## 📈 Results

Performance on the 200 held-out test movies:

| Model | MAE | MSE | RMSE | R² |
|---|---|---|---|---|
| Linear Regression | 0.623 | 0.713 | 0.844 | 0.256 |
| Decision Tree | 0.632 | 0.732 | 0.855 | 0.237 |
| **Random Forest** | **0.589** | **0.642** | **0.801** | **0.331** |

**Reading the results:** the Random Forest performs best on every metric. On average its prediction is off by about **0.6 rating points**. An R² of 0.33 means the model explains roughly a third of the variation in ratings, which is a sensible result given that it only sees genre, year and runtime, and not the quality of the script, cast or direction.

## 📁 Project Structure

```
.
├── IMDB-Movie-Data.csv          # Dataset (1,000 movies)
├── model_traning_code.ipynb     # EDA, preprocessing, training and evaluation
├── movie_rating_model.pkl       # Saved model + genre encoder + feature columns
├── desktop_app.py               # Tkinter desktop app (CineRate)
├── requirements.txt             # Python dependencies
└── README.md
```

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Aryann0307/imdb-movie-rating-predictor.git
cd imdb-movie-rating-predictor
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install the dependencies

```bash
pip install -r requirements.txt
```

> The bundled model was saved with **scikit-learn 1.9.1**. Using the version pinned in `requirements.txt` avoids an `InconsistentVersionWarning` when the model loads.

### 4. Run the desktop app

```bash
python desktop_app.py
```

Keep `movie_rating_model.pkl` in the same folder as `desktop_app.py`. Tkinter is included with the standard Python installers for Windows and macOS (python.org). On Debian/Ubuntu, install it with `sudo apt install python3-tk`.

### 5. (Optional) Re-train the model

Open the notebook and run all cells. The last cells re-create `movie_rating_model.pkl`.

```bash
jupyter notebook model_traning_code.ipynb
```

## ⚙️ How the App Makes a Prediction

The app loads `movie_rating_model.pkl`, a dictionary with three entries:

| Key | Contents |
|---|---|
| `model` | The trained `RandomForestRegressor` |
| `encoder` | The fitted `MultiLabelBinarizer` (20 genres) |
| `feature_columns` | The exact column order used during training |

When you press **Predict rating**:

1. The selected genres are encoded with the saved encoder.
2. A one-row table is built using the saved `feature_columns` order, so the input always matches the training format.
3. Year, runtime and the genre columns are filled in.
4. The model predicts the rating, which is shown out of 10 together with a short verdict.

Input checks: at least one genre, a year between 1900 and 2035, and a runtime between 30 and 300 minutes.

## ⚠️ Limitations

- **Estimates, not official ratings.** The output is a statistical estimate and not an actual IMDb score.
- **Limited features.** Only genre, year and runtime are used, so the model cannot capture cast, director, story or marketing.
- **Small dataset.** 1,000 movies is small for a machine-learning model.
- **Years outside 2006 to 2016.** The app accepts years from 1900 to 2035, but the model was trained only on 2006 to 2016. Tree-based models cannot extrapolate, so results outside that range behave much like the nearest training years and should not be trusted.
- **Popular-movie bias.** The dataset contains well-known movies, so predictions may be skewed for obscure titles.

## 🔮 Future Improvements

- Add more pre-release features, such as director or lead actors.
- Tune hyperparameters and use cross-validation for a more reliable evaluation.
- Try gradient boosting models such as XGBoost or LightGBM.
- Train on a larger and more recent dataset.
- Package the desktop app as a standalone executable.

## 🛠 Tech Stack

- **Language:** Python
- **Data and ML:** pandas, NumPy, scikit-learn, joblib
- **Visualization:** Matplotlib, Seaborn
- **Interface:** Tkinter

## 👤 Author

**Aryan**
GitHub: [@Aryann0307](https://github.com/Aryann0307)

If you found this project useful, consider giving it a ⭐.
