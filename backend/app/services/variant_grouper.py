"""Variant grouping using pandas groupby."""
import pandas as pd
from typing import Any


class VariantGrouper:
    """Group products with identical Name/Token/SKU as variants."""

    def group_variants(self, products: list[dict]) -> tuple[list[dict], list[dict]]:
        """
        Group products by product_name + product_token + sku.

        Returns:
            (groups, products_with_group_assignment)
            - groups: list of group dicts with variant_count
            - products: original products with group assignment info
        """
        if not products:
            return [], []

        df = pd.DataFrame(products)

        # Group by the three identifying fields
        grouped = df.groupby(['product_name', 'product_token', 'sku'], dropna=False)

        groups = []
        products_with_groups = []

        for group_idx, ((name, token, sku), group_df) in enumerate(grouped):
            # Create group entry
            group_info = {
                'group_idx': group_idx,
                'product_name': name if pd.notna(name) else '',
                'product_token': token if pd.notna(token) else '',
                'sku': sku if pd.notna(sku) else '',
                'variant_count': len(group_df),
            }
            groups.append(group_info)

            # Assign group index to each product in this group
            for _, row in group_df.iterrows():
                product = row.to_dict()
                product['_group_idx'] = group_idx
                products_with_groups.append(product)

        return groups, products_with_groups
