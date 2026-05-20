# Excel Splitter

A minimal Streamlit app for splitting `.xlsx` files into smaller `.xlsx` files and downloading the result as a ZIP archive.

## Features

- Upload an `.xlsx` file
- Enter rows per output file, excluding the header
- Optionally enter a sheet name
- Leave sheet name blank to use the first sheet
- Keep the header row in every output file
- Create files named `part_001.xlsx`, `part_002.xlsx`, ...
- Download all split files as one ZIP
- Basic error handling for empty files, missing sheets, invalid row counts, read failures, and wrong file formats
- Temporary input and split files are cleaned automatically after processing

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
- Very large workbooks may take longer depending on Community Cloud memory and CPU limits.
