# -*- coding: utf-8 -*-
import base64
import xlwt
import io
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import models, api, fields


class SaleByVendorWizard(models.Model):

    _name = 'sale.by.vendor.wiz'
    _description = 'Sale By Vendor Wizard'

    start_dt = fields.Datetime(string='From', default=fields.Date.today().replace(day=1))
    end_dt = fields.Datetime(string='To', default=fields.Date.context_today)

    state = fields.Boolean(string='State')
    file = fields.Binary(string='File')
    filenm = fields.Char(
        string='Filename', default='Sale_By_Vendor_Report.xls')

    def get_datetime_usertimezone(self, dt):
        user_tz = pytz.timezone(self.env.user.tz)
        datetm_usertz = pytz.utc.localize(dt).astimezone(user_tz)
        return datetm_usertz.strftime("%Y-%m-%d %H:%M:%S")

    def get_data(self, report_type):
        sales_orders = self.env['sale.order'].sudo().search([
            ('date_order', '>=', self.start_dt),
            ('date_order', '<=', self.end_dt),
            ('state', 'in', ('sale', 'done')),
        ])

        pos_orders = self.env['pos.order'].sudo().search([
            ('date_order', '>=', self.start_dt),
            ('date_order', '<=', self.end_dt),
            ('state', 'in', ('sale', 'done')),
        ])

        data_dict = {}

        for sale_order in sales_orders:
            for line in sale_order.order_line:
                if line.product_id.x_studio_vendor_number:
                    if line.product_id.x_studio_vendor_number in data_dict:
                        data_dict[line.product_id.x_studio_vendor_number].get('amount').append(line.product_id.id)

                        data_dict[line.product_id.x_studio_vendor_number] = {
                            'vendor': line.product_id.x_studio_vendor_number,
                            # 'amount': data_dict[line.product_id.x_studio_vendor_number].get('amount').append(line.product_id.id),
                            'amount': data_dict[line.product_id.x_studio_vendor_number].get('amount'),
                            'amount_pr': '',  # 2/7*100
                            'quantity': data_dict[line.product_id.x_studio_vendor_number].get('quantity', 0) + line.product_uom_qty,
                            'sales': data_dict[line.product_id.x_studio_vendor_number].get('sales', 0) + line.price_subtotal,
                            'sales_pr': '',  # 50000/325000*100
                            'gross_profit': '',
                            'gross_profit_pr': '',
                            'cost': data_dict[line.product_id.x_studio_vendor_number].get('cost', 0) + (line.product_id.standard_price * line.product_uom_qty),
                        }
                    else:
                        data_dict[line.product_id.x_studio_vendor_number] = {
                            'vendor': line.product_id.x_studio_vendor_number,
                            'amount': [line.product_id.id],
                            'amount_pr': '',  # 2/7*100
                            'quantity': line.product_uom_qty,
                            'sales': line.price_subtotal,
                            'sales_pr': '',  # 50000/325000*100
                            'gross_profit': '',
                            'gross_profit_pr': '',
                            'cost': line.product_id.standard_price * line.product_uom_qty,
                        }

        for pos_order in pos_orders:
            for line in pos_order.lines:
                if line.product_id.x_studio_vendor_number:
                    if line.product_id.x_studio_vendor_number in data_dict:
                        data_dict[line.product_id.x_studio_vendor_number].get('amount').append(line.product_id.id)

                        data_dict[line.product_id.x_studio_vendor_number] = {
                            'vendor': line.product_id.x_studio_vendor_number,
                            # 'amount': data_dict[line.product_id.x_studio_vendor_number].get('amount').append(line.product_id.id),
                            'amount': data_dict[line.product_id.x_studio_vendor_number].get('amount'),
                            'amount_pr': '',  # 2/7*100
                            'quantity': data_dict[line.product_id.x_studio_vendor_number].get('quantity', 0) + line.qty,
                            'sales': data_dict[line.product_id.x_studio_vendor_number].get('sales', 0) + line.price_subtotal,
                            'sales_pr': '',  # 50000/325000*100
                            'gross_profit': '',
                            'gross_profit_pr': '',
                            'cost': data_dict[line.product_id.x_studio_vendor_number].get('cost', 0) + (line.product_id.standard_price * line.qty),
                        }
                    else:
                        data_dict[line.product_id.x_studio_vendor_number] = {
                            'vendor': line.product_id.x_studio_vendor_number,
                            'amount': [line.product_id.id],
                            'amount_pr': '',  # 2/7*100
                            'quantity': line.qty,
                            'sales': line.price_subtotal,
                            'sales_pr': '',  # 50000/325000*100
                            'gross_profit': '',
                            'gross_profit_pr': '',
                            'cost': line.product_id.standard_price * line.qty,
                        }

        final_lines = []

        total_amount = 0
        total_qty = 0
        total_sales = 0
        total_cost = 0
        total_gross_profit = 0

        for key, value in data_dict.items():
            total_amount += len(set(value.get('amount')))
            total_qty += value.get('quantity')
            total_sales += value.get('sales')
            total_cost += value.get('cost')

        if total_amount == 0:
            total_amount = 1
        if total_sales == 0:
            total_sales = 1

        for key, value in data_dict.items():
            amount_pr = len(set(value.get('amount'))) / total_amount * 100
            sales_pr = value.get('sales') / total_sales * 100
            gross_profit = value.get('sales') - value.get('cost')
            total_gross_profit += gross_profit
            gross_profit_pr = gross_profit / total_cost * 100

            line_vals = [
                value.get('vendor'),
                len(set(value.get('amount'))),
                '{:.2f}'.format(amount_pr),  # round(amount_pr),
                value.get('quantity'),
                '{:.2f}'.format(value.get('sales')),  # value.get('sales'),
                '{:.2f}'.format(sales_pr),  # round(sales_pr),
                '{:.2f}'.format(gross_profit),
                '{:.2f}'.format(gross_profit_pr),  # round(gross_profit_pr),
            ]
            final_lines.append(line_vals)
        return {
            'lines': final_lines,
            'total_amount': total_amount,
            'total_qty': total_qty,
            'total_sales': '{:.2f}'.format(total_sales),
            'total_cost': '{:.2f}'.format(total_cost),
            'total_gross_profit': '{:.2f}'.format(total_gross_profit),
        }

    def print_pdf(self):
        data = self.get_data('pdf')

        from_dt = self.get_datetime_usertimezone(self.start_dt)
        to_dt = self.get_datetime_usertimezone(self.end_dt)
        report_data = data
        self.state = True

        ctx = {
            'from_dt': from_dt,
            'to_dt': to_dt,
            'report_data': report_data,
        }

        record_id = self.env['sale.order'].sudo().search([], limit=1).id
        report = self.env.ref('sale_by_vendor.action_report_sale_by_vendor_report').with_context(ctx).sudo()._render_qweb_pdf([record_id])[0]

        self.file = base64.b64encode(report)
        self.filenm = 'Sale_By_Vendor_Report.PDF'

        return {
            'name': 'Download File',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.by.vendor.wiz',
            'res_id': self.id,
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
        }

    def print_xls(self):
        data = self.get_data('xls')

        from_dt = self.get_datetime_usertimezone(self.start_dt)
        to_dt = self.get_datetime_usertimezone(self.end_dt)

        self.state = True

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Sale_By_Vendor_Report')

        row = 0
        worksheet.write_merge(row, row + 1, 0, 7, 'Sale By Vendor Report', xlwt.easyxf('font:bold on;alignment: horizontal  center;'))
        row += 2
        worksheet.write(row, 0, 'From:', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 1, from_dt, xlwt.easyxf('font:bold on'))
        worksheet.write(row, 2, '', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 3, '', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 4, '', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 5, '', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 6, 'To:', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 7, to_dt, xlwt.easyxf('font:bold on'))
        row += 3

        worksheet.write(row, 0, 'Vendor', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 1, 'Amount', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 2, '% of Total', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 3, 'Quantity', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 4, 'Sales', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 5, '% of Total', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 6, 'Gross Profit', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 7, '% of Total', xlwt.easyxf('font:bold on'))
        row += 1

        for line in data.get('lines'):
            worksheet.write(row, 0, line[0])
            worksheet.write(row, 1, line[1])
            worksheet.write(row, 2, str(line[2]) + '%')
            worksheet.write(row, 3, line[3])
            worksheet.write(row, 4, line[4])
            worksheet.write(row, 5, str(line[5]) + '%')
            worksheet.write(row, 6, line[6])
            worksheet.write(row, 7, str(line[7]) + '%')
            row += 1

        worksheet.write(row, 0, '', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 1, '', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 2, '', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 3, '', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 4, '', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 5, '', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 6, '', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 7, '', xlwt.easyxf('font:bold on'))
        row += 1

        worksheet.write(row, 0, 'Grand Totals', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 1, str(data.get('total_amount')), xlwt.easyxf('font:bold on'))
        worksheet.write(row, 2, '', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 3, str(data.get('total_qty')), xlwt.easyxf('font:bold on'))
        worksheet.write(row, 4, str(data.get('total_sales')), xlwt.easyxf('font:bold on'))
        worksheet.write(row, 5, '', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 6, str(data.get('total_gross_profit')), xlwt.easyxf('font:bold on'))
        worksheet.write(row, 7, '', xlwt.easyxf('font:bold on'))
        row += 1

        fp = io.BytesIO()
        workbook.save(fp)
        self.file = base64.encodestring(fp.getvalue())
        self.filenm = 'Sale_By_Vendor_Report.xls'

        return {
            'name': 'Download File',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.by.vendor.wiz',
            'res_id': self.id,
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
        }
