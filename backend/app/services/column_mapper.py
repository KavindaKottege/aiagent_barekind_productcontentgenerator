"""Fuzzy column mapping using RapidFuzz."""
from rapidfuzz import process, fuzz
from typing import Any


class FuzzyColumnMapper:
    """Map Excel column names to product fields using fuzzy matching."""

    # Expected fields with common variations
    FIELD_PATTERNS = {
        'product_name': ['Product Name', 'Name', 'Title', 'Product Title'],
        'product_token': ['Product Token', 'Token', 'Product ID', 'ID'],
        'sku': ['SKU', 'Product SKU', 'Variant SKU', 'Item Number', 'Item SKU'],
        'status': ['Status', 'Product Status', 'State'],
        'description': ['Description', 'Product Description', 'Details', 'Long Description'],
        'option_name': ['Option Name', 'Option', 'Variant Name', 'Variant', 'Size/Color'],
        'product_type': ['Product Type', 'Type', 'Category'],
        'country_of_origin': ['Country of Origin', 'Country', 'Origin', 'Made In'],
        'made_to_order': ['Made to Order', 'MTO', 'Custom Order'],
        'images': ['Images', 'Image URLs', 'Image', 'Product Images', 'Photo URLs'],
    }

    # Required fields that must be mapped for upload to succeed
    REQUIRED_FIELDS = {'product_name', 'product_token', 'sku'}

    def map_columns(self, excel_headers: list[str]) -> dict:
        """
        Map Excel columns to product fields.
        Returns: {
            'mapped': {'field_name': 'Excel Column Name', ...},
            'unmapped': ['Unmapped Col 1', ...],
            'confidence': 'HIGH' | 'MEDIUM',
            'missing_required': ['field1', ...]  # Required fields not mapped
        }
        """
        mappings = {}
        used_columns = set()

        for field, patterns in self.FIELD_PATTERNS.items():
            best_match = None
            best_score = 0

            # Try each pattern against all headers
            for pattern in patterns:
                match = process.extractOne(
                    query=pattern,
                    choices=[h for h in excel_headers if h not in used_columns],
                    scorer=fuzz.token_sort_ratio,
                    score_cutoff=75.0  # 75% similarity threshold
                )
                if match and match[1] > best_score:
                    best_match = match[0]
                    best_score = match[1]

            if best_match:
                mappings[field] = best_match
                used_columns.add(best_match)

        # Unmapped columns (preserved for export)
        unmapped = [col for col in excel_headers if col not in used_columns]

        # Check required fields
        missing_required = [f for f in self.REQUIRED_FIELDS if f not in mappings]

        # Confidence based on required fields and total mappings
        if missing_required:
            confidence = 'LOW'
        elif len(mappings) >= 5:
            confidence = 'HIGH'
        else:
            confidence = 'MEDIUM'

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
                    if field_name == 'made_to_order':
                        mapped[field_name] = self._parse_bool(value)
                    elif field_name == 'images':
                        mapped[field_name] = self._parse_images(value)
                    else:
                        mapped[field_name] = self._sanitize(value)
                else:
                    unmapped[col_name] = self._sanitize(value)

            mapped['unmapped_data'] = unmapped
            result.append(mapped)

        return result

    def _sanitize(self, value: Any) -> Any:
        """Sanitize cell value to prevent formula injection."""
        if isinstance(value, str) and value and value[0] in ('=', '+', '-', '@'):
            return "'" + value
        return value

    def _parse_bool(self, value: Any) -> bool | None:
        """Parse boolean-like values."""
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('yes', 'true', '1', 'y')
        return bool(value)

    def _parse_images(self, value: Any) -> list[str] | None:
        """Parse image URLs (comma or newline separated)."""
        if not value:
            return None
        if isinstance(value, str):
            # Split by comma or newline
            urls = [u.strip() for u in value.replace('\n', ',').split(',') if u.strip()]
            return urls if urls else None
        return None
