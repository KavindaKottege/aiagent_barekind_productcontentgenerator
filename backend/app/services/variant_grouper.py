"""Variant grouping using pandas groupby."""
import pandas as pd
from typing import Any


class VariantGrouper:
    """Group products with identical product_name as variants."""

    def group_variants(self, products: list[dict]) -> tuple[list[dict], list[dict]]:
        """
        Group products by product_name only.
        Products with the same name are variants of each other.
        Groups and products are ordered by original row index.

        Returns:
            (groups, products_with_group_assignment)
            - groups: list of group dicts with variant_count, ordered by first appearance
            - products: original products with group assignment info, ordered by row_index
        """
        if not products:
            return [], []

        df = pd.DataFrame(products)

        # Track group assignments while preserving order
        groups = []
        products_with_groups = []
        seen_names = {}  # product_name -> group_idx

        # Process products in original row order
        for idx, row in df.iterrows():
            product = row.to_dict()
            name = product.get('product_name', '')
            row_index = product.get('row_index', idx)

            if name not in seen_names:
                # First time seeing this product name - create a new group
                group_idx = len(groups)
                seen_names[name] = group_idx

                # Get the first product's token and sku for the group
                group_info = {
                    'group_idx': group_idx,
                    'product_name': name if pd.notna(name) else '',
                    'product_token': product.get('product_token', '') or '',
                    'sku': product.get('sku', '') or '',
                    'variant_count': 0,  # Will be updated below
                    'first_row_index': row_index,  # Track first appearance for sorting
                }
                groups.append(group_info)

            # Assign product to its group
            product['_group_idx'] = seen_names[name]
            products_with_groups.append(product)

        # Count variants per group
        for product in products_with_groups:
            groups[product['_group_idx']]['variant_count'] += 1

        return groups, products_with_groups
