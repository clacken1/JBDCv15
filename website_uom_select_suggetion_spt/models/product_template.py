from odoo import models, fields, api, _
from odoo.addons.website.models import ir_http

class ProductTemplate(models.Model):
    _inherit = "product.template"

    product_uom_category_id = fields.Many2one('uom.category',
                                              string="UOM Category",
                                              compute="_get_uom_category")

    product_uom_ids = fields.Many2many('uom.uom', 'product_template_uom_rel',
                                       'product_id', 'uom_id',
                                       string="Product UOMs")

    @api.depends('uom_id')
    def _get_uom_category(self):
        for rec in self:
            rec.product_uom_category_id = rec.uom_id.category_id.id
            rec.product_uom_ids = [(4,rec.uom_id.id)]

class ProductProduct(models.Model):
    _inherit = "product.product" 

    def _compute_cart_qty(self):
        website = ir_http.get_request_website()
        if not website:
            self.cart_qty = 0
            return
        cart = website.sale_get_order()
        qty = 0
        for product in self:
            # product.cart_qty = sum(cart.order_line.filtered(lambda p: p.product_id.id == product.id and p.product_uom.id == product.uom_id.id).mapped('product_uom_qty')) if cart else 0
            order_line = cart.order_line.filtered(lambda p: p.product_id.id == product.id)
            if order_line:
                for prod in order_line:
                    qty += int(prod.product_uom.factor_inv) * int(prod.product_uom_qty)
            if qty:
                product.cart_qty = int(qty)
            else:
                product.cart_qty = 0
