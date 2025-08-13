# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)

class SkuTestLog(models.Model):
    _name = "sku_test.log"
    _description = "SKU Test – Component SKU Log"

    date = fields.Datetime(default=lambda self: fields.Datetime.now(), required=True)
    order_id = fields.Many2one("sale.order", string="Sale Order", index=True, ondelete="cascade")
    order_line_id = fields.Many2one("sale.order.line", string="Order Line", index=True, ondelete="cascade")
    pack_product_id = fields.Many2one("product.product", string="Pack/Kit Product", index=True)
    component_product_id = fields.Many2one("product.product", string="Component Product", index=True)
    sku = fields.Char(string="Component SKU", help="Component default_code captured at confirmation time")

class ProductProduct(models.Model):
    _inherit = "product.product"

    # Optional custom field so you can define components directly
    component_ids = fields.Many2many(
        "product.product",
        "sku_test_product_component_rel",
        "product_id",
        "component_id",
        string="Pack Components (SKU Test)",
        help="Optional: define components here if you don't use BOM Kits or a product_pack module.",
    )

class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        """On confirmation, log SKUs of component products for any pack/kit lines."""
        res = super().action_confirm()

        for order in self:
            for line in order.order_line:
                product = line.product_id
                if not product:
                    continue

                components = order._sku_test_get_components(product)

                if not components:
                    continue  # Not a pack/kit product (based on our heuristics)

                for comp in components:
                    sku = comp.default_code or ""
                    # Log to server logs
                    _logger.info(
                        "[SKU_TEST] Order %s | Line %s | Pack %s -> Component %s (SKU: %s)",
                        order.name,
                        line.id,
                        product.display_name,
                        comp.display_name,
                        sku,
                    )
                    # Persist in a lightweight log model
                    self.env["sku_test.log"].create({
                        "order_id": order.id,
                        "order_line_id": line.id,
                        "pack_product_id": product.id,
                        "component_product_id": comp.id,
                        "sku": sku,
                    })
        return res

    def _sku_test_get_components(self, product):
        """Return a set of component products for a given product, using several strategies."""
        components = set()

        # 1) Phantom/kit BOMs (if mrp installed)
        try:
            Bom = self.env["mrp.bom"]
            # Try exact variant BOM first
            boms = Bom.search([
                ("product_id", "=", product.id),
                ("type", "=", "phantom"),
            ])
            # Fallback: template-level phantom BOM
            if not boms:
                boms = Bom.search([
                    ("product_tmpl_id", "=", product.product_tmpl_id.id),
                    ("type", "=", "phantom"),
                ])
            for bom in boms:
                for bl in bom.bom_line_ids:
                    if bl.product_id:
                        components.add(bl.product_id)
        except Exception:
            # mrp not installed or no access; ignore silently
            pass

        # 2) product_pack community module (pack_line_ids on product.product or product.template)
        #    Handles both possible placements defensively.
        if hasattr(product, "pack_line_ids"):
            for pl in product.pack_line_ids:
                if getattr(pl, "product_id", False):
                    components.add(pl.product_id)
        elif hasattr(product.product_tmpl_id, "pack_line_ids"):
            for pl in product.product_tmpl_id.pack_line_ids:
                if getattr(pl, "product_id", False):
                    components.add(pl.product_id)

        # 3) Our optional custom M2M field
        if hasattr(product, "component_ids") and product.component_ids:
            for comp in product.component_ids:
                components.add(comp)

        return components
