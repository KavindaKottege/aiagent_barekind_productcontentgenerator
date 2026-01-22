"""Streaming Excel parser using openpyxl read_only mode."""
from pathlib import Path
from openpyxl import load_workbook
from typing import Generator


class ExcelParser:
    """Parse Excel files in streaming mode for memory efficiency."""

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        self.wb = None

    def parse(self) -> Generator[list[dict], None, None]:
        """
        Stream Excel rows in batches.
        Yields batches of 500 rows as list[dict].
        IMPORTANT: Caller must call close() when done.
        """
        self.wb = load_workbook(filename=str(self.file_path), read_only=True)
        ws = self.wb.active

        # Get headers from first row
        rows_iter = ws.iter_rows(values_only=True)
        headers = [str(cell) if cell else f"column_{i}" for i, cell in enumerate(next(rows_iter))]

        batch = []
        for row in rows_iter:
            # Skip completely empty rows
            if not any(row):
                continue
            row_dict = dict(zip(headers, row))
            batch.append(row_dict)

            if len(batch) >= 500:
                yield batch
                batch = []

        if batch:
            yield batch

    def close(self):
        """Close workbook. MUST be called after parsing."""
        if self.wb:
            self.wb.close()
            self.wb = None
