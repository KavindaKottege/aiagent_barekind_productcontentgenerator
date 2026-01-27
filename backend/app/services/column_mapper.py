"""Exact 1:1 column mapping for Faire Excel templates."""
from typing import Any
from datetime import datetime, date


class ExactColumnMapper:
    """Map Excel column names to product fields using exact 1:1 matching."""

    # Exact 1:1 mapping: field_name -> exact Excel column name
    COLUMN_MAP = {
        'product_name': 'Product Name (English)',
        'product_token': 'Product Token',
        'sku': 'SKU',
        'status': 'Product Status',
        'description': 'Description (English)',
        'option_type': 'Option 1 Name',
        'option_name': 'Option 1 Value',
        'option_2_name': 'Option 2 Name',
        'option_2_value': 'Option 2 Value',
        'option_3_name': 'Option 3 Name',
        'option_3_value': 'Option 3 Value',
        'product_type': 'Product Type',
        'country_of_origin': 'Made In Country',
        'images': 'Product Images',
        'wholesale_price_usd': 'USD Unit Wholesale Price',
        'retail_price_usd': 'USD Unit Retail Price',
    }

    # Required fields that must be mapped for upload to succeed
    REQUIRED_FIELDS = {'product_name', 'product_token', 'sku'}

    def map_columns(self, excel_headers: list[str]) -> dict:
        """
        Map Excel columns to product fields using exact matching.
        Returns: {
            'mapped': {'field_name': 'Excel Column Name', ...},
            'unmapped': ['Unmapped Col 1', ...],
            'confidence': 'HIGH' | 'LOW',
            'missing_required': ['field1', ...]  # Required fields not mapped
        }
        """
        mappings = {}
        used_columns = set()

        # Build reverse lookup: Excel column -> field name
        reverse_map = {v: k for k, v in self.COLUMN_MAP.items()}

        # Check each Excel header for exact match
        for header in excel_headers:
            if header in reverse_map:
                field = reverse_map[header]
                mappings[field] = header
                used_columns.add(header)

        # Unmapped columns (preserved for export)
        unmapped = [col for col in excel_headers if col not in used_columns]

        # Check required fields
        missing_required = [f for f in self.REQUIRED_FIELDS if f not in mappings]

        # Confidence: HIGH if all required fields present, LOW otherwise
        confidence = 'LOW' if missing_required else 'HIGH'

        return {
            'mapped': mappings,
            'unmapped': unmapped,
            'confidence': confidence,
            'missing_required': missing_required
        }

    def apply_mapping(self, rows: list[dict], mapping: dict[str, str]) -> list[dict]:
        """
        Apply column mapping to rows.
        Returns rows with both mapped fields and unmapped_data dict.
        """
        result = []
        reverse_mapping = {v: k for k, v in mapping.items()}

        for row in rows:
            mapped = {}
            unmapped = {}

            for col_name, value in row.items():
                if col_name in reverse_mapping:
                    field_name = reverse_mapping[col_name]
                    # Handle special types
                    if field_name == 'images':
                        mapped[field_name] = self._parse_images(value)
                    elif field_name in ('wholesale_price_usd', 'retail_price_usd'):
                        mapped[field_name] = self._parse_float(value)
                    else:
                        mapped[field_name] = self._sanitize(value)
                else:
                    unmapped[col_name] = self._sanitize(value)

            mapped['unmapped_data'] = unmapped
            result.append(mapped)

        return result

    def _sanitize(self, value: Any) -> Any:
        """Sanitize cell value to prevent formula injection and ensure JSON serializability."""
        # Convert datetime objects to ISO strings
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        # Prevent formula injection in strings
        if isinstance(value, str) and value and value[0] in ('=', '+', '-', '@'):
            return "'" + value
        return value

    def _parse_float(self, value: Any) -> float | None:
        """Parse float values."""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                # Remove currency symbols and commas
                cleaned = value.replace('$', '').replace(',', '').strip()
                return float(cleaned) if cleaned else None
            except ValueError:
                return None
        return None

    def _parse_images(self, value: Any) -> list[str] | None:
        """Parse image URLs (space, comma, or newline separated)."""
        if not value:
            return None
        if isinstance(value, str):
            # Normalize separators: replace newlines and commas with spaces, then split
            normalized = value.replace('\n', ' ').replace(',', ' ')
            urls = [u.strip() for u in normalized.split() if u.strip() and u.strip().startswith('http')]
            return urls if urls else None
        return None
