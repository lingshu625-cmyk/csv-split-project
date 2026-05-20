from __future__ import annotations

from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import streamlit as st


class AppError(Exception):
    """Base class for user-facing errors."""


class EmptyFileError(AppError):
    """Raised when the uploaded CSV has no content."""


class InvalidFormatError(AppError):
    """Raised when the uploaded file is not a .csv file."""


class InvalidRowCountError(AppError):
    """Raised when rows per file is invalid."""


class ReadFileError(AppError):
    """Raised when the uploaded file cannot be read or split."""


def validate_upload(uploaded_file) -> None:
    """Validate file presence, extension, and non-empty upload size."""
    if uploaded_file is None:
        raise InvalidFormatError("Please upload a .csv file.")

    if Path(uploaded_file.name).suffix.lower() != ".csv":
        raise InvalidFormatError("Invalid file format. Please upload a .csv file.")

    if uploaded_file.size == 0:
        raise EmptyFileError("The uploaded CSV is empty. Please upload another file.")


def validate_rows_per_file(rows_per_file: int) -> None:
    """Validate the user-entered data-row count."""
    if not isinstance(rows_per_file, int) or rows_per_file <= 0:
        raise InvalidRowCountError(
            "Rows per output file must be an integer greater than 0."
        )


def read_data_block(source_file, rows_per_file: int) -> list[bytes]:
    """
    Read up to rows_per_file physical CSV lines.

    The app intentionally does not parse CSV fields or convert encodings. It
    copies raw bytes so values, dates, quotes, delimiters, and line endings are
    preserved exactly as uploaded.
    """
    lines: list[bytes] = []

    while len(lines) < rows_per_file:
        line = source_file.readline()
        if not line:
            break
        lines.append(line)

    return lines


def split_csv_to_zip(uploaded_file, rows_per_file: int) -> tuple[bytes, int, int]:
    """
    Split one uploaded CSV and return a ZIP payload.

    Output files are named part_001.csv, part_002.csv, etc. The first physical
    line is treated as the header and is copied into every output file.
    """
    validate_upload(uploaded_file)
    validate_rows_per_file(rows_per_file)

    try:
        uploaded_file.seek(0)
        header = uploaded_file.readline()
    except Exception as exc:
        raise ReadFileError("Failed to read the CSV. Please upload it again.") from exc

    if not header:
        raise EmptyFileError("The uploaded CSV is empty. Please upload another file.")

    zip_buffer = BytesIO()
    part_count = 0
    total_rows = 1

    try:
        with ZipFile(zip_buffer, mode="w", compression=ZIP_DEFLATED) as zip_file:
            while True:
                data_lines = read_data_block(uploaded_file, rows_per_file)
                total_rows += len(data_lines)

                # A header-only CSV still creates one output file with just the header.
                if not data_lines and part_count > 0:
                    break

                part_count += 1
                part_name = f"part_{part_count:03d}.csv"
                part_content = BytesIO()
                part_content.write(header)
                part_content.writelines(data_lines)
                zip_file.writestr(part_name, part_content.getvalue())

                if len(data_lines) < rows_per_file:
                    break
    except Exception as exc:
        raise ReadFileError(
            "Failed to split the CSV. Please check the file and upload it again."
        ) from exc

    return zip_buffer.getvalue(), part_count, total_rows


def show_error(error: Exception) -> None:
    """Display concise user-facing errors and allow a second upload."""
    if isinstance(error, AppError):
        st.error(str(error))
    else:
        st.error("An unexpected error occurred. Please upload the file again.")


st.set_page_config(page_title="CSV Splitter", page_icon="📄", layout="centered")

st.title("CSV Splitter")
st.caption("Upload a CSV file, split it by row count, and download a ZIP.")

st.markdown(
    """
    <style>
    div.stButton > button[kind="primary"] {
        background-color: #2563eb;
        border-color: #2563eb;
        color: #ffffff;
    }

    div.stButton > button[kind="primary"]:hover {
        background-color: #1d4ed8;
        border-color: #1d4ed8;
        color: #ffffff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

uploaded_file = st.file_uploader(
    "Upload a .csv file",
    type=["csv"],
    accept_multiple_files=False,
)

rows_per_file = st.number_input(
    "Rows per output file (excluding header)",
    min_value=1,
    value=999,
    step=1,
    help="For example, 999 means each output CSV has the header plus up to 999 data rows.",
)

split_button = st.button("Split CSV", type="primary", use_container_width=True)

if split_button:
    try:
        with st.spinner("Splitting your CSV. Please wait..."):
            zip_bytes, part_count, total_rows = split_csv_to_zip(
                uploaded_file=uploaded_file,
                rows_per_file=int(rows_per_file),
            )
    except Exception as exc:
        show_error(exc)
    else:
        st.success(f"Done. Read {total_rows} rows and created {part_count} file(s).")
        st.download_button(
            label="Download ZIP",
            data=zip_bytes,
            file_name="csv_split_result.zip",
            mime="application/zip",
            use_container_width=True,
        )

st.divider()
st.caption(
    "The header row is kept in every output file. CSV content is copied as raw bytes without format conversion."
)
