# CSV Splitter

A minimal Streamlit app for splitting `.csv` files into smaller `.csv` files and downloading the result as a ZIP archive.

## Features

- Upload a `.csv` file
- Enter rows per output file, excluding the header
- Keep the header row in every output file
- Create files named `part_001.csv`, `part_002.csv`, ...
- Download all split files as one ZIP
- Basic error handling for empty files, invalid row counts, read failures, and wrong file formats
- CSV content is copied as raw bytes without parsing fields or converting formats

## Project Structure

```text
.
├── .gitignore
├── app.py
├── requirements.txt
└── README.md
```

## Local Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL shown by Streamlit, usually:

```text
http://localhost:8501
```

## Deploy To Streamlit Community Cloud

1. Push these files to a GitHub repository:

```text
.gitignore
app.py
requirements.txt
README.md
```

2. Open [Streamlit Community Cloud](https://share.streamlit.io/).

3. Click **Create app** or **New app**.

4. Select your GitHub repository, branch, and set the main file path to:

```text
app.py
```

5. Click **Deploy**. Streamlit will install `requirements.txt` and start the app automatically.

## Notes

- The app is public by default on Streamlit Community Cloud.
- No login or password is required by this app.
- The app treats one physical line as one CSV row. CSV fields containing embedded line breaks are not specially parsed.
