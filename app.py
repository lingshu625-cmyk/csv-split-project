from __future__ import annotations

import math
import tempfile
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd
import streamlit as st


class AppError(Exception):
    """Base class for user-facing errors."""


class EmptyFileError(AppError):
    """Raised when the uploaded workbook has no usable content."""


class InvalidFormatError(AppError):
    """Raised when the uploaded file is not an .xlsx file."""


class InvalidRowCountError(AppError):
    """Raised when rows per file is invalid."""


class SheetNotFoundError(AppError):
    """Raised when the requested sheet name does not exist."""


class ReadWorkbookError(AppError):
    """Raised when the workbook cannot be read or written."""


def validate_upload(uploaded_file) -> None:
    """Validate file presence, extension, and non-empty upload size."""
    if uploaded_file is None:
        raise InvalidFormatError("Please upload an .xlsx file.")

    if Path(uploaded_file.name).suffix.lower() != ".xlsx":
        raise InvalidFormatError("Invalid file format. Please upload an .xlsx file.")

    if uploaded_file.size == 0:
        raise EmptyFileError("The uploaded file is empty. Please upload another file.")


def validate_rows_per_file(rows_per_file: int) -> None:
    """Validate the user-entered data-row count."""
    if not isinstance(rows_per_file, int) or rows_per_file <= 0:
        raise InvalidRowCountError(
            "Rows per output file must be an integer greater than 0."
        )


def save_uploaded_file(uploaded_file, temp_dir: Path) -> Path:
    """Save Streamlit's uploaded file object to a temporary local file."""
    input_path = temp_dir / "input.xlsx"
    uploaded_file.seek(0)
    input_path.write_bytes(uploaded_file.read())
    return input_path


def choose_sheet(excel_file: pd.ExcelFile, requested_sheet: str) -> str:
    """Use the requested sheet name, or the first workbook sheet when blank."""
    if not excel_file.sheet_names:
        raise EmptyFileError("The workbook does not contain any sheets.")

    sheet_name = requested_sheet.strip()
    if not sheet_name:
        return excel_file.sheet_names[0]

    if sheet_name not in excel_file.sheet_names:
        available = ", ".join(excel_file.sheet_names)
        raise SheetNotFoundError(
            f"Sheet '{sheet_name}' was not found. Available sheets: {available}"
        )

    return sheet_name


def read_sheet(input_path: Path, sheet_name: str) -> pd.DataFrame:
    """Read one worksheet into a DataFrame."""
    try:
        return pd.read_excel(
            input_path,
            sheet_name=sheet_name,
            engine="openpyxl",
            dtype=object,
        )
    except Exception as exc:
        raise ReadWorkbookError(
            "Failed to read the workbook. Please check the file and upload again."
        ) from exc


def write_part(part_path: Path, sheet_name: str, data: pd.DataFrame) -> None:
    """Write one split DataFrame to an .xlsx file."""
    safe_sheet_name = sheet_name[:31] or "Sheet1"
    try:
        with pd.ExcelWriter(part_path, engine="openpyxl") as writer:
            data.to_excel(writer, index=False, sheet_name=safe_sheet_name)
    except Exception as exc:
        raise ReadWorkbookError(
            "Failed to create split workbook files. Please try again."
        ) from exc


def split_workbook_to_zip(
    uploaded_file,
    rows_per_file: int,
    requested_sheet: str,
) -> tuple[bytes, int, int, str]:
    """
    Split one .xlsx workbook and return a ZIP payload.

    Temporary input and split files are created inside TemporaryDirectory and are
    automatically deleted after the ZIP bytes are prepared.
    """
    validate_upload(uploaded_file)
    validate_rows_per_file(rows_per_file)

    with tempfile.TemporaryDirectory() as temp_name:
        temp_dir = Path(temp_name)
        input_path = save_uploaded_file(uploaded_file, temp_dir)

        try:
            excel_file = pd.ExcelFile(input_path, engine="openpyxl")
        except Exception as exc:
            raise ReadWorkbookError(
                "Failed to open the workbook. Please upload a valid .xlsx file."
            ) from exc

        sheet_name = choose_sheet(excel_file, requested_sheet)
        dataframe = read_sheet(input_path, sheet_name)

        if dataframe.empty and len(dataframe.columns) == 0:
            raise EmptyFileError(
                "The selected sheet is empty. Please upload another file."
            )

        data_row_count = len(dataframe)
        part_count = max(1, math.ceil(data_row_count / rows_per_file))
        zip_buffer = BytesIO()

        with ZipFile(zip_buffer, mode="w", compression=ZIP_DEFLATED) as zip_file:
            for part_index in range(part_count):
                start = part_index * rows_per_file
                end = start + rows_per_file
                part_data = dataframe.iloc[start:end]
                part_name = f"part_{part_index + 1:03d}.xlsx"
                part_path = temp_dir / part_name

                write_part(part_path, sheet_name, part_data)
                zip_file.write(part_path, arcname=part_name)

        return zip_buffer.getvalue(), part_count, data_row_count, sheet_name


def show_error(error: Exception) -> None:
    """Display concise user-facing errors and allow a second upload."""
    if isinstance(error, AppError):
        st.error(str(error))
    else:
        st.error("An unexpected error occurred. Please upload the file again.")


st.set_page_config(page_title="Excel Splitter", page_icon="📄", layout="centered")

st.title("Excel Splitter")
st.caption("Upload an .xlsx file, split a worksheet by row count, and download a ZIP.")

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
    "Upload an .xlsx file",
    type=["xlsx"],
    accept_multiple_files=False,
)

rows_per_file = st.number_input(
    "Rows per output file (excluding header)",
    min_value=1,
    value=999,
    step=1,
    help="For example, 999 means each output workbook has the header plus up to 999 data rows.",
)

sheet_name = st.text_input(
    "Sheet name (optional)",
    value="",
    help="Leave blank to use the first sheet in the workbook.",
)

split_button = st.button("Split Excel", type="primary", use_container_width=True)

if split_button:
    try:
        with st.spinner("Splitting your workbook. Please wait..."):
            zip_bytes, part_count, data_rows, used_sheet = split_workbook_to_zip(
                uploaded_file=uploaded_file,
                rows_per_file=int(rows_per_file),
                requested_sheet=sheet_name,
            )
    except Exception as exc:
        show_error(exc)
    else:
        st.success(
            f"Done. Sheet '{used_sheet}' has {data_rows} data row(s). "
            f"Created {part_count} file(s)."
        )
        st.download_button(
            label="Download ZIP",
            data=zip_bytes,
            file_name="excel_split_result.zip",
            mime="application/zip",
            use_container_width=True,
        )

st.divider()
st.caption(
    "The header row is kept in every output file. Temporary files are deleted automatically after processing."
)
