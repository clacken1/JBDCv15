# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import Warning

class SaleSummaryReport(models.AbstractModel):

    _name='report.all_in_one_report.report_sales_summary'
    _description = "All Sale Summary Report"

    def _get_report_values(self, docids, data=None):
        sale_summary_rec = self.env['all.sale.summary.wizard'].browse(docids)       
        if sale_summary_rec.report_type == 'sas':
            domain = [
            ('order_id.state', '=', 'sale'),
            ('order_id.date_order', '>=', sale_summary_rec.start_dt), ('order_id.date_order', '<=', sale_summary_rec.end_dt)]
            if sale_summary_rec.categ_ids:
                domain += [('product_id.categ_id', 'in', sale_summary_rec.categ_ids.ids)]
            if sale_summary_rec.product_ids:
                domain += [('product_id', 'in', sale_summary_rec.product_ids.ids)]
            sale_order_line_ids = self.env['sale.order.line'].search(domain)
            total_cost = 0.0
            total_price =0.0
            total_gross =0.0
            summary_data = []
            svl_obj = self.env['stock.valuation.layer']
            for line in sale_order_line_ids:
                domain = [
                    ('create_date', '<', line.order_id.date_order.date()),
                    ('product_id', '=', line.product_id.id)
                ]   
                stock_valuation_layer_id = svl_obj.search(domain, order='create_date desc', limit=1)
                cost = abs(stock_valuation_layer_id.value if stock_valuation_layer_id else line.product_id.standard_price)

                # stock_valuation_layer_ids = svl_obj.search(domain)
                # product_qty = sum(stock_valuation_layer_ids.mapped('quantity'))
                # product_value = sum(stock_valuation_layer_ids.mapped('value'))
                # if product_qty and product_value:
                #     cost = product_value / product_qty
                # else:
                #     cost = line.product_id.standard_price
                price = line.price_unit
                profit = price - cost
                total_cost += cost
                total_price += price
                total_gross += profit
                summary_data.append({
                    'date': line.order_id.date_order.date(),
                    'code': line.product_id.default_code,
                    'product': line.product_id.display_name,
                    'quantity': line.product_uom_qty,
                    'cost': cost,
                    'price': price,
                    'profit': profit,
                    'gp_per': profit/price if price else 0,
                })
        else:
            domain = [
            ('move_id.state', '=', 'posted'),
            ('move_id.invoice_date', '>=', sale_summary_rec.start_dt), ('move_id.invoice_date', '<=', sale_summary_rec.end_dt)]
            if sale_summary_rec.categ_ids:
                domain += [('product_id.categ_id', 'in', sale_summary_rec.categ_ids.ids)]
            if sale_summary_rec.product_ids:
                domain += [('product_id', 'in', sale_summary_rec.product_ids.ids)]
            sale_order_line_ids = self.env['account.move.line'].search(domain)
            total_cost = 0.0
            total_price =0.0
            total_gross =0.0
            summary_data = []
            svl_obj = self.env['stock.valuation.layer']
            for line in sale_order_line_ids:
                domain = [
                    ('create_date', '<', line.move_id.invoice_date),
                    ('product_id', '=', line.product_id.id)
                ]   
                stock_valuation_layer_id = svl_obj.search(domain, order='create_date desc', limit=1)
                cost = abs(stock_valuation_layer_id.value if stock_valuation_layer_id else line.product_id.standard_price)

                # stock_valuation_layer_ids = svl_obj.search(domain)
                # product_qty = sum(stock_valuation_layer_ids.mapped('quantity'))
                # product_value = sum(stock_valuation_layer_ids.mapped('value'))
                # if product_qty and product_value:
                #     cost = product_value / product_qty
                # else:
                #     cost = line.product_id.standard_price
                price = line.price_unit
                profit = price - cost
                total_cost += cost
                total_price += price
                total_gross += profit
                summary_data.append({
                    'date': line.move_id.invoice_date,
                    'code': line.product_id.default_code,
                    'product': line.product_id.display_name,
                    'quantity': line.quantity,
                    'cost': cost,
                    'price': price,
                    'profit': profit,
                    'gp_per': profit/price if price else 0,
                })

            domain = [
                ('order_id.state', 'not in', ['draft', 'cancel']),
                ('order_id.date_order', '>=', sale_summary_rec.start_dt), ('order_id.date_order', '<=', sale_summary_rec.end_dt)]
            if sale_summary_rec.categ_ids:
                domain += [('product_id.categ_id', 'in', sale_summary_rec.categ_ids.ids)]
            if sale_summary_rec.product_ids:
                domain += [('product_id', 'in', sale_summary_rec.product_ids.ids)]
            sale_order_line_ids = self.env['pos.order.line'].search(domain)
            summary_data = []
            svl_obj = self.env['stock.valuation.layer']
            for line in sale_order_line_ids:
                domain = [
                    ('create_date', '<', line.order_id.date_order.date()),
                    ('product_id', '=', line.product_id.id)
                ]   
                stock_valuation_layer_id = svl_obj.search(domain, order='create_date desc', limit=1)
                cost = stock_valuation_layer_id.value if stock_valuation_layer_id else line.product_id.standard_price

                # stock_valuation_layer_ids = svl_obj.search(domain)
                # product_qty = sum(stock_valuation_layer_ids.mapped('quantity'))
                # product_value = sum(stock_valuation_layer_ids.mapped('value'))
                # if product_qty and product_value:
                #     cost = product_value / product_qty
                # else:
                #     cost = line.product_id.standard_price
                price = line.price_unit
                profit = price - cost
                total_cost += cost
                total_price += price
                total_gross += profit
                summary_data.append({
                    'date': line.order_id.date_order.date(),
                    'code': line.product_id.default_code,
                    'product': line.product_id.display_name,
                    'quantity': line.qty,
                    'cost': cost,
                    'price': price,
                    'profit': profit,
                    'gp_per': profit/price if price else 0,
                })
            summary_data = sorted(summary_data, key = lambda i: i['date'])

        return {
            'summary': True if sale_summary_rec.report_type != 'sas' else False,
            'currency_precision': 2,
            'doc_ids': docids,
            'doc_model': 'all.sale.summary.wizard',
            'start_dt' : sale_summary_rec.start_dt.date(),
            'end_dt' : sale_summary_rec.end_dt.date(),
            'current_dt':datetime.now(),
            'summary_data': summary_data,
            'total_cost': total_cost,
            'total_price': total_price,
            'total_gross': total_gross,
        }


class ReportConsignmentSummary(models.AbstractModel):

    _name='report.all_in_one_report.report_consignment_summary'
    _description = "Report Consignment Summary"

    def _get_report_values(self, docids, data=None):
        consignment_rec = self.env['all.consignment.summary.wizard'].browse(docids)       
        domain = [
        ('create_date', '>=', consignment_rec.start_dt), ('create_date', '<=', consignment_rec.end_dt)]
        if consignment_rec.purchase and not consignment_rec.sales:
            domain += [('quantity', '>', 0)]
        if consignment_rec.sales and not consignment_rec.purchase:
            domain += [('quantity', '<', 0)]
        if consignment_rec.owner_ids:
            domain += [('owner_id', 'in', consignment_rec.owner_ids.ids)]
        if consignment_rec.product_ids:
            domain += [('product_id', 'in', consignment_rec.product_ids.ids)]
        stock_quant_ids = self.env['stock.quant'].search(domain)
        total_cost = 0.0
        total_total_cost = 0.0
        total_qty = 0.0
        summary_data = {}
        svl_obj = self.env['stock.valuation.layer']
        for stock_quant_id in stock_quant_ids:
            # domain = [
            #     ('create_date', '<', stock_quant_id.create_date.date()),
            #     ('product_id', '=', stock_quant_id.product_id.id)
            # ]   
            # stock_valuation_layer_id = svl_obj.search(domain, order='create_date desc', limit=1)
            # cost = stock_valuation_layer_id.value if stock_valuation_layer_id else stock_quant_id.product_id.standard_price

            # stock_valuation_layer_ids = svl_obj.search(domain)
            # product_qty = sum(stock_valuation_layer_ids.mapped('quantity'))
            # product_value = sum(stock_valuation_layer_ids.mapped('value'))
            # if product_qty and product_value:
            #     cost = product_value / product_qty
            # else:
            #     cost = line.product_id.standard_price
            qty_available = stock_quant_id.product_id.qty_available
            # qty_available = stock_quant_id.quantity
            cost = stock_quant_id.product_id.standard_price
            total_cost += cost
            total_total_cost += cost * qty_available
            total_qty += qty_available

            if stock_quant_id.owner_id.id not in summary_data:
                summary_data[stock_quant_id.owner_id.id] = {
                    'owner_name': stock_quant_id.owner_id.name or 'Undefined',
                    'data_list' : [{
                        'code': stock_quant_id.product_id.default_code,
                        'product': stock_quant_id.product_id.display_name,
                        'quantity': qty_available,
                        'cost': cost,
                        'total_cost': cost * qty_available,
                        # 'quantity': stock_quant_id.quantity,
                        # 'cost': cost,
                        # 'total_cost': cost * stock_quant_id.quantity,
                    }]
                }
            else:
                summary_data[stock_quant_id.owner_id.id]['data_list'].append({
                    'code': stock_quant_id.product_id.default_code,
                    'product': stock_quant_id.product_id.display_name,
                    'quantity': qty_available,
                    'cost': cost,
                    'total_cost': cost * qty_available,
                })
        print("==summary_data==", summary_data)
        final_list = []
        for i in summary_data:
            final_list.append(summary_data.get(i))
        print("==final_list==", final_list)
        return {
            'doc_ids': docids,
            'doc_model': 'all.consignment.summary.wizard',
            'start_dt' : consignment_rec.start_dt,
            'end_dt' : consignment_rec.end_dt,
            'current_dt':datetime.now(),
            'final_list': final_list,
            'total_cost': total_cost,
            'total_qty': total_qty,
            'total_total_cost': total_total_cost,
        }
    

