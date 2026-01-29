"""Excel export service for reconstructing original Excel structure with updated content."""

from io import BytesIO

from openpyxl import Workbook

from app.services.column_mapper import ExactColumnMapper


class ExcelExporter:
    """Export products back to Excel format preserving original structure.

    Reconstructs the original uploaded Excel with only Product Name and
    Description columns updated for approved/edited products. All other
    columns and all original values are preserved as-is.
    """

    # Reverse map: Excel header name -> field name
    REVERSE_MAP: dict[str, str] = {v: k for k, v in ExactColumnMapper.COLUMN_MAP.items()}

    def export(
        self,
        products: list[dict],
        column_order: list[str],
        include_pending: bool = False,
    ) -> BytesIO:
        """Export products to an Excel workbook.

        Args:
            products: List of product dicts with group info, ordered by row_index.
                Each dict should contain:
                - All mapped field values (product_name, description, etc.)
                - unmapped_data: dict of unmapped column values
                - review_status: from ProductGroup
                - status: from ProductGroup (generation status)
                - generated_title, generated_description: from ProductGroup
                - edited_title, edited_description: from ProductGroup
            column_order: Original Excel column headers in order.
            include_pending: If True, also update content for generated products
                that are not yet reviewed (and not rejected).

        Returns:
            BytesIO buffer containing the .xlsx file.
        """
        wb = Workbook()
        ws = wb.active
        ws.title = "Products"

        # Write header row
        ws.append(column_order)

        # Write data rows
        for product in products:
            use_generated = self._should_use_generated(product, include_pending)
            row = self._build_row(product, column_order, use_generated)
            ws.append(row)

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer

    def _should_use_generated(self, product: dict, include_pending: bool) -> bool:
        """Determine if a product should use generated content in the export.

        Rules:
        - Approved or edited products always use generated/edited content.
        - If include_pending is True, generated products that are not rejected
          also use generated content.
        - Rejected and non-generated products keep original values.
        """
        review_status = product.get("review_status")
        group_status = product.get("group_status")

        # Approved or edited: always use generated content
        if review_status in ("approved", "edited"):
            return True

        # Include pending: use generated content if generated and not rejected
        if include_pending and group_status == "generated" and review_status != "rejected":
            return True

        return False

    def _build_row(self, product: dict, column_order: list[str], use_generated: bool) -> list:
        """Build a single row of data for the export.

        For each column header in the original order:
        - If it's a mapped column: use the product's field value
          (with generated content substitution for product_name/description if use_generated)
        - If it's an unmapped column: pull from unmapped_data dict
        """
        row = []
        for col_header in column_order:
            field_name = self.REVERSE_MAP.get(col_header)

            if field_name:
                value = self._get_mapped_value(product, field_name, use_generated)
            else:
                # Unmapped column: pull from unmapped_data
                value = product.get("unmapped_data", {}).get(col_header, "")

            row.append(value if value is not None else "")

        return row

    def _get_mapped_value(self, product: dict, field_name: str, use_generated: bool):
        """Get the value for a mapped field, with generated content substitution."""
        if field_name == "product_name" and use_generated:
            # Prefer edited_title > generated_title > original product_name
            return (
                product.get("edited_title")
                or product.get("generated_title")
                or product.get("product_name", "")
            )

        if field_name == "description" and use_generated:
            # Prefer edited_description > generated_description > original description
            return (
                product.get("edited_description")
                or product.get("generated_description")
                or product.get("description", "")
            )

        if field_name == "images":
            # Join image URLs with space separator (Faire format)
            images = product.get("images")
            if isinstance(images, list):
                return " ".join(str(url) for url in images if url)
            return images or ""

        if field_name == "made_to_order":
            # Export boolean as-is; openpyxl handles True/False in Excel
            return product.get("made_to_order")

        return product.get(field_name, "")
