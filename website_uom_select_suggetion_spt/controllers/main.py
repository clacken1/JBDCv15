import json

from odoo import http,fields
from odoo.http import request
from odoo.addons.sale.controllers.variant import VariantController
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale_product_configurator.controllers.main import WebsiteSale as WebsiteSaleConfigurator
from odoo.tools.json import scriptsafe as json_scriptsafe


class KitsWebsiteSale(WebsiteSale):
    @http.route(['/shop/cart/update'], type='http', auth="public", methods=['GET', 'POST'], website=True, csrf=False)
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        """This route is called when adding a product to cart (no options)."""
        sale_order = request.website.sale_get_order(force_create=True)
        if sale_order.state != 'draft':
            request.session['sale_order_id'] = None
            sale_order = request.website.sale_get_order(force_create=True)

        product_custom_attribute_values = None
        if kw.get('product_custom_attribute_values'):
            product_custom_attribute_values = json.loads(kw.get('product_custom_attribute_values'))

        no_variant_attribute_values = None
        if kw.get('no_variant_attribute_values'):
            no_variant_attribute_values = json.loads(kw.get('no_variant_attribute_values'))

        product = request.env['product.product'].search([('id','=',product_id)])

        uom_id = kw.get('uom_id')
        uom = False
        if uom_id == 'NaN':
            uom = product.uom_id.id
        else:
            uom = int(product.product_uom_ids.filtered(lambda l: l.name == uom_id).id)

        sale_order._cart_update(
            product_id=int(product_id),
            add_qty=add_qty,
            set_qty=set_qty,
            # uom_id=int(kw.get('uom_id')) if kw.get('uom_id') else product.uom_id.id,
            uom_id=uom,
            product_custom_attribute_values=product_custom_attribute_values,
            no_variant_attribute_values=no_variant_attribute_values
        )

        if kw.get('express'):
            return request.redirect("/shop/checkout?express=1")

        return request.redirect("/shop/cart")


    @http.route(['/shop/cart/update_json'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update_json(self, product_id, line_id=None, add_qty=None, set_qty=None, display=True, **kw):
        """
        This route is called :
            - When changing quantity from the cart.
            - When adding a product from the wishlist.
            - When adding a product to cart on the same page (without redirection).
        """
        order = request.website.sale_get_order(force_create=1)
        if order.state != 'draft':
            request.website.sale_reset()
            if kw.get('force_create'):
                order = request.website.sale_get_order(force_create=1)
            else:
                return {}

        pcav = kw.get('product_custom_attribute_values')
        nvav = kw.get('no_variant_attribute_values')
        if kw.get('uom_id'):
            value = order._cart_update(
                product_id=product_id,
                line_id=line_id,
                add_qty=add_qty,
                set_qty=set_qty,
                product_custom_attribute_values=json_scriptsafe.loads(pcav) if pcav else None,
                no_variant_attribute_values=json_scriptsafe.loads(nvav) if nvav else None,
                uom_id=kw.get('uom_id')
            )
        else:
            value = order._cart_update(
            product_id=product_id,
            line_id=line_id,
            add_qty=add_qty,
            set_qty=set_qty,
            product_custom_attribute_values=json_scriptsafe.loads(pcav) if pcav else None,
            no_variant_attribute_values=json_scriptsafe.loads(nvav) if nvav else None
        )

        if not order.cart_quantity:
            request.website.sale_reset()
            return value

        order = request.website.sale_get_order()
        value['cart_quantity'] = order.cart_quantity

        if not display:
            return value

        value['website_sale.cart_lines'] = request.env['ir.ui.view']._render_template("website_sale.cart_lines", {
            'website_sale_order': order,
            'date': fields.Date.today(),
            'suggested_products': order._cart_accessories()
        })
        value['website_sale.short_cart_summary'] = request.env['ir.ui.view']._render_template("website_sale.short_cart_summary", {
            'website_sale_order': order,
        })
        return value
    
    @http.route(['/sale-order'], type='json', auth="public", website=True, method=['post'])
    def getSaleOrder(self, **post):
        """This route is called when displaying the message about stock. i.e. remaning product in stock,
        quantity of selected product added in cart.
        """
        prod_uom = False
        ordered_qty = False
        prod = post['product_id']
        prod_uom = post['uom_name']
        if prod:
            product = request.env['product.product'].search([('id','=',prod)])
            uom = request.env['uom.uom'].search([('name','=',prod_uom)])
            available_qty = product.free_qty - product.cart_qty
            stock_qty = int(available_qty / uom.factor_inv) if product.free_qty > 0 else 0
            val = {
                'uom':prod_uom,
                'product_uom':product.uom_id.name,
                'qty':stock_qty,
            }
        else:
            val = {
                'uom':post.get('uom_name'),
                'qty':post.get('cart_qty'),
            }
            
        return val


class KitsWebsiteSaleConfigurator(WebsiteSaleConfigurator):
    @http.route(['/shop/cart/update_option'], type='http', auth="public", methods=['POST'], website=True, multilang=False)
    def cart_options_update_json(self, product_and_options, goto_shop=None, lang=None, **kwargs):
        """This route is called when submitting the optional product modal.
            The product without parent is the main product, the other are options.
            Options need to be linked to their parents with a unique ID.
            The main product is the first product in the list and the options
            need to be right after their parent.
            product_and_options {
                'product_id',
                'product_template_id',
                'quantity',
                'parent_unique_id',
                'unique_id',
                'product_custom_attribute_values',
                'no_variant_attribute_values'
            }
        """
        if lang:
            request.website = request.website.with_context(lang=lang)

        order = request.website.sale_get_order(force_create=True)
        if order.state != 'draft':
            request.session['sale_order_id'] = None
            order = request.website.sale_get_order(force_create=True)

        product_and_options = json.loads(product_and_options)
        if product_and_options:
            # The main product is the first, optional products are the rest
            main_product = product_and_options[0]
            value = order._cart_update(
                product_id=main_product['product_id'],
                add_qty=main_product['quantity'],
                uom_id=kwargs.get("uom_id"),
                product_custom_attribute_values=main_product['product_custom_attribute_values'],
                no_variant_attribute_values=main_product['no_variant_attribute_values'],
            )

            # Link option with its parent.
            option_parent = {main_product['unique_id']: value['line_id']}
            for option in product_and_options[1:]:
                parent_unique_id = option['parent_unique_id']
                option_value = order._cart_update(
                    product_id=option['product_id'],
                    set_qty=option['quantity'],
                    linked_line_id=option_parent[parent_unique_id],
                    product_custom_attribute_values=option['product_custom_attribute_values'],
                    no_variant_attribute_values=option['no_variant_attribute_values'],
                )
                option_parent[option['unique_id']] = option_value['line_id']

        return str(order.cart_quantity)


class KitsVariantController(VariantController):
    @http.route()
    def get_combination_info(self, product_template_id, product_id, combination, add_qty, pricelist_id, **kw):
        res = super(KitsVariantController, self).get_combination_info(product_template_id, product_id, combination, add_qty, pricelist_id, **kw)
        product = request.env['product.product'].sudo().browse(product_id) 
        if kw.get('uom_id'):
            uom = request.env['uom.uom'].sudo().browse(kw.get('uom_id'))
        else:
            uom = product.product_uom_ids.filtered(lambda l: l.name == res.get('uom_name'))

        unit_uom_quantity = uom._compute_quantity(1, product.uom_id)
        res.update({
            'price': unit_uom_quantity * res.get('price'),
            'list_price': unit_uom_quantity * res.get('list_price'),
            'uom_name': uom.name,
            'uom_free_qty' : int((product.free_qty - product.cart_qty) / uom.factor_inv) if product.free_qty > 0 else 0,
            'uom_factor_inv' : int(res.get('free_qty') / uom.factor_inv) if product.free_qty > 0 else 0,
        })
        return res