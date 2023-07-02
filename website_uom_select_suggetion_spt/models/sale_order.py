import logging
import math
from odoo import models, api
from odoo.http import request
from odoo import _,fields
from odoo.exceptions import UserError, ValidationError

from odoo.addons.website_sale.models.sale_order import SaleOrder as MainSaleOrder
from odoo.addons.website_sale_stock.models.sale_order import SaleOrder

_logger = logging.getLogger(__name__)


class WSSaleOrder(MainSaleOrder):
    _inherit = "sale.order"

    def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):
        """ Add or set product quantity, add_qty can be negative """
        self.ensure_one()
        product_context = dict(self.env.context)
        product_context.setdefault('lang', self.sudo().partner_id.lang)
        SaleOrderLineSudo = self.env['sale.order.line'].sudo().with_context(product_context)
        # change lang to get correct name of attributes/values
        product_with_context = self.env['product.product'].with_context(product_context)
        product = product_with_context.browse(int(product_id)).exists()

        if not product or (not line_id and not product._is_add_to_cart_allowed()):
            raise UserError(_("The given product does not exist therefore it cannot be added to cart."))

        try:
            if add_qty:
                add_qty = int(add_qty)
        except ValueError:
            add_qty = 1
        try:
            if set_qty:
                set_qty = int(set_qty)
        except ValueError:
            set_qty = 0
        quantity = 0
        order_line = False
        if self.state != 'draft':
            request.session['sale_order_id'] = None
            raise UserError(_('It is forbidden to modify a sales order which is not in draft status.'))
        if line_id is not False:
            order_line = self._cart_find_product_line(product_id, line_id, **kwargs)[:1]
            if 'uom_id' in kwargs.keys():
                order_line_ids = order_line.order_id.order_line
                current_prod_ids = order_line_ids.filtered(
                    lambda l: l.product_id.id == product_id)
                if current_prod_ids:
                    if current_prod_ids.filtered(lambda l: l.product_uom.id == kwargs.get("uom_id")):
                        order_line = current_prod_ids.filtered(
                            lambda l: l.product_uom.id == kwargs.get("uom_id"))
                    else:
                        order_line = self.env['sale.order.line']

        # Create line if no line with product_id can be located
        if not order_line:
            no_variant_attribute_values = kwargs.get('no_variant_attribute_values') or []
            received_no_variant_values = product.env['product.template.attribute.value'].browse([int(ptav['value']) for ptav in no_variant_attribute_values])
            received_combination = product.product_template_attribute_value_ids | received_no_variant_values
            product_template = product.product_tmpl_id

            # handle all cases where incorrect or incomplete data are received
            combination = product_template._get_closest_possible_combination(received_combination)

            # get or create (if dynamic) the correct variant
            product = product_template._create_product_variant(combination)

            if not product:
                raise UserError(_("The given combination does not exist therefore it cannot be added to cart."))

            product_id = product.id

            values = self._website_product_id_change(self.id, product_id, qty=1, **kwargs)

            # add no_variant attributes that were not received
            for ptav in combination.filtered(lambda ptav: ptav.attribute_id.create_variant == 'no_variant' and ptav not in received_no_variant_values):
                no_variant_attribute_values.append({
                    'value': ptav.id,
                })

            # save no_variant attributes values
            if no_variant_attribute_values:
                values['product_no_variant_attribute_value_ids'] = [
                    (6, 0, [int(attribute['value']) for attribute in no_variant_attribute_values])
                ]

            # add is_custom attribute values that were not received
            custom_values = kwargs.get('product_custom_attribute_values') or []
            received_custom_values = product.env['product.template.attribute.value'].browse([int(ptav['custom_product_template_attribute_value_id']) for ptav in custom_values])

            for ptav in combination.filtered(lambda ptav: ptav.is_custom and ptav not in received_custom_values):
                custom_values.append({
                    'custom_product_template_attribute_value_id': ptav.id,
                    'custom_value': '',
                })

            # save is_custom attributes values
            if custom_values:
                values['product_custom_attribute_value_ids'] = [(0, 0, {
                    'custom_product_template_attribute_value_id': custom_value['custom_product_template_attribute_value_id'],
                    'custom_value': custom_value['custom_value']
                }) for custom_value in custom_values]

            # update uom and price
            selected_product_uom = self.env["uom.uom"].browse(
                kwargs.get("uom_id"))
            if not selected_product_uom:
                selected_product_uom = product.uom_id
            default_product_uom = self.env["uom.uom"].browse(
                values.get("product_uom"))
            if not default_product_uom:
                default_product_uom = product.uom_id
            values.update({
                "product_uom": kwargs.get("uom_id",default_product_uom.id),
                "price_unit": default_product_uom._compute_price(values.get("price_unit"), selected_product_uom),
            })

            # create the line
            values.update({
                'name': product.name
            })
            # create the line
            order_line = SaleOrderLineSudo.create(values)

            try:
                order_line._compute_tax_id()
            except ValidationError as e:
                # The validation may occur in backend (eg: taxcloud) but should fail silently in frontend
                _logger.debug("ValidationError occurs during tax compute. %s" % (e))
            if add_qty:
                add_qty -= 1

        # compute new quantity
        if set_qty:
            quantity = set_qty * order_line.product_uom.factor_inv
        elif add_qty is not None:
            quantity= (order_line.product_uom_qty*order_line.product_uom.factor_inv) + (add_qty*order_line.product_uom.factor_inv or 0)

        # Remove zero of negative lines
        if quantity <= 0:
            linked_line = order_line.linked_line_id
            order_line.unlink()
            if linked_line:
                # update description of the parent
                linked_product = product_with_context.browse(linked_line.product_id.id)
                linked_line.name = linked_line.get_sale_order_line_multiline_description_sale(linked_product)
        else:
            # update line
            no_variant_attributes_price_extra = [ptav.price_extra for ptav in order_line.product_no_variant_attribute_value_ids]
            values = self.with_context(no_variant_attributes_price_extra=tuple(no_variant_attributes_price_extra))._website_product_id_change(self.id, product_id, qty=quantity, **kwargs)
            order = self.sudo().browse(self.id)
            if self.pricelist_id.discount_policy == 'with_discount' and not self.env.context.get('fixed_price'):
                product_context.update({
                    'partner': order.partner_id,
                    'quantity': quantity/order_line.product_uom.factor_inv,
                    'date': order.date_order,
                    'pricelist': order.pricelist_id.id,
                })
            product_with_context = self.env['product.product'].with_context(product_context).with_company(order.company_id.id)
            product = product_with_context.browse(product_id)
            values['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(
                order_line._get_display_price(product),
                order_line.product_id.taxes_id,
                order_line.tax_id,
                self.company_id
            )

            if values.get('product_uom_qty'):
                values['product_uom_qty'] = quantity/order_line.product_uom.factor_inv

            if 'uom_id' in kwargs.keys():
                values.update({
                    "product_uom": kwargs.get("uom_id"),
                })
            else:
                # values.update({'product_uom' : order_line.product_uom.name})
                values['product_uom'] = order_line.product_uom.id

            order_line.write(values)

            # link a product to the sales order
            if kwargs.get('linked_line_id'):
                linked_line = SaleOrderLineSudo.browse(kwargs['linked_line_id'])
                order_line.write({
                    'linked_line_id': linked_line.id,
                })
                linked_product = product_with_context.browse(linked_line.product_id.id)
                linked_line.name = linked_line.get_sale_order_line_multiline_description_sale(linked_product)
            order_line.name = order_line.get_sale_order_line_multiline_description_sale(product)

        option_lines = self.order_line.filtered(lambda l: l.linked_line_id.id == order_line.id)

        return {'line_id': order_line.id, 'quantity': quantity, 'option_ids': list(set(option_lines.ids))}

class WSSSaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends('order_line.product_uom_qty', 'order_line.product_id')
    def _compute_cart_info(self):
        for order in self:
            if order.mapped('website_order_line.product_uom_qty') and order.mapped('website_order_line.product_uom'):
                res_list = []
                for i in range(0, len(order.mapped('website_order_line.product_uom_qty'))):
                    res_list.append(order.mapped('website_order_line.product_uom_qty')[i] * order.mapped('website_order_line.product_uom.factor_inv')[i])
                    order.cart_quantity =int(sum(res_list))
            else:
                order.cart_quantity = int(sum(order.mapped('website_order_line.product_uom_qty')))
            # order.cart_quantity = int(sum(order.mapped('website_order_line.product_uom_qty')))
            order.only_services = all(l.product_id.type in ('service', 'digital') for l in order.website_order_line)
    
    def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):
        values = super(SaleOrder, self)._cart_update(product_id, line_id, add_qty, set_qty, **kwargs)
        values = self._cart_lines_stock_update(values, **kwargs)
        return values

    def _cart_lines_stock_update(self, values, **kwargs):
        line_id = values.get('line_id')
        for line in self.order_line:
            if line.product_id.type == 'product' and not line.product_id.allow_out_of_stock_order:
                order_line_prod_qty=[]
                for order_line in self.order_line.filtered(lambda p: p.product_id.id == line.product_id.id):
                    order_line_prod_qty.append(order_line.product_uom_qty * order_line.product_uom.factor_inv)
                cart_qty = sum(order_line_prod_qty)
                # cart_qty = sum(self.order_line.filtered(lambda p: p.product_id.id == line.product_id.id).mapped('product_uom_qty'))
                if (line_id == line.id) and cart_qty > line.product_id.with_context(warehouse=self.warehouse_id.id).free_qty:
                    qty = line.product_id.with_context(warehouse=self.warehouse_id.id).free_qty - cart_qty
                    quantity = math.floor(qty/line.product_uom.factor_inv)
                    new_val = super(SaleOrder, self)._cart_update(line.product_id.id, line.id, quantity, 0, **kwargs)
                    values.update(new_val)

                    # Make sure line still exists, it may have been deleted in super()_cartupdate because qty can be <= 0
                    if line.exists() and new_val['quantity']:
                        line.warning_stock = _('You ask for %s products but only %s is available') % (cart_qty, new_val['quantity'])
                        values['warning'] = line.warning_stock
                    else:
                        self.warning_stock = _("Some products became unavailable and your cart has been updated. We're sorry for the inconvenience.")
                        values['warning'] = self.warning_stock
        return values


MainSaleOrder._cart_update = WSSaleOrder._cart_update