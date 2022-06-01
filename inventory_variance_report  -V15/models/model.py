# -*- coding: utf-8 -*-
from odoo import fields, models, api


class StockValuationLayer(models.Model):
    """Stock Valuation Layer"""

    _inherit = 'stock.valuation.layer'

    flag_move_change = fields.Boolean(string='Move Change', store=True, compute="_compute_flag_move_change")
    accounting_date = fields.Date(string='Accounting Date', store=True, related='account_move_id.date')

    @api.depends('account_move_id', 'account_move_id.state', 'account_move_id.line_ids')
    def _compute_flag_move_change(self):
        for layer in self:
            layer.flag_move_change = False
            if layer.account_move_id and layer.account_move_id.state == 'posted' and layer.quantity != 0:
                total = abs(sum(layer.account_move_id.line_ids.mapped('debit')))
                total = abs(total)
                unit_cost = total / layer.quantity
                if layer.quantity < 0:
                    total = -total
                layer.unit_cost = abs(unit_cost)
                layer.value = total


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def get_inventory_value(self):
        value = 0
        stock_layer_obj = self.env['stock.valuation.layer'].sudo()
        qty = self.qty_done
        if self.location_dest_id.usage == 'internal':
            qty = self.qty_done
        if self.location_id.usage == 'internal':
            qty = -self.qty_done

        inv_value_line = stock_layer_obj.search([
            ('product_id', '=', self.product_id.id),
            ('quantity', '=', qty),
            ('stock_move_id', '=', self.move_id.id),
        ], limit=1)
        if inv_value_line:
            value = inv_value_line.value
        return value


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    def get_history_lines(self):
        domain = [
            ('product_id', '=', self.product_id.id),
            ('company_id', '=', self.company_id.id),
            '|',
            ('location_id', '=', self.location_id.id),
            ('location_dest_id', '=', self.location_id.id),
        ]
        lines = self.env['stock.move.line'].sudo().search(domain)
        return lines

    def get_locations(self):
        lines = self.get_history_lines()
        location_ids = []
        for line in lines:
            if line.location_id and line.location_id.usage == 'internal':
                location_ids.append(line.location_id.id)
            elif line.location_dest_id and line.location_dest_id.usage == 'internal':
                location_ids.append(line.location_dest_id.id)
        if location_ids:
            locations = self.env['stock.location'].sudo().browse(set(location_ids))
            return locations
        else:
            return False
