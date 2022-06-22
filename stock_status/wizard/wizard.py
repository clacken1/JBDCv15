# -*- coding: utf-8 -*-
import base64
import xlwt
import io
import pytz
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import models, api, fields


class StockStatusWizard(models.Model):

    _name = 'stock.status.wiz'
    _description = 'Stock Status Wizard'

    start_dt = fields.Datetime(string='Inventory At Date', default=fields.Date.today().replace(day=1))
    end_dt = fields.Datetime(string='To', default=fields.Date.context_today)

    all_product = fields.Boolean(string='All Products')
    product_ids = fields.Many2many('product.product', string='Products')

    state = fields.Boolean(string='State')
    file = fields.Binary(string='File')
    filenm = fields.Char(
        string='Filename', default='Stock_Status_Report.xls')

    def get_datetime_usertimezone(self, dt):
        user_tz = pytz.timezone(self.env.user.tz)
        datetm_usertz = pytz.utc.localize(dt).astimezone(user_tz)
        return datetm_usertz.strftime("%Y-%m-%d %H:%M:%S")

    def get_data(self, report_type):
        # warehouse_id = self.env['stock.warehouse'].sudo().search([('company_id', '=', self.env.company.id)], limit=1).id
        if not self.all_product:
            products = self.env['product.product'].with_context({"from_date": self.start_dt, "to_date": self.end_dt}).search([('id', 'in', self.product_ids.ids), ('detailed_type', '=', 'product')])
        else:
            products = self.env['product.product'].with_context({"from_date": self.start_dt, "to_date": self.end_dt}).search([('detailed_type', '=', 'product')])

        data_dict = {}

        for product in products.with_context({"from_date": self.start_dt, "to_date": self.end_dt}):
            product = product.with_context({"from_date": self.start_dt, "to_date": self.end_dt})
            dict_key = False

            if product.x_studio_vendor_number and product.x_studio_listed_vendor:
                dict_key = str(product.x_studio_vendor_number) + '_' + str(product.x_studio_listed_vendor)
            elif product.x_studio_vendor_number and not product.x_studio_listed_vendor:
                dict_key = str(product.x_studio_vendor_number)
            elif not product.x_studio_vendor_number and product.x_studio_listed_vendor:
                dict_key = str(product.x_studio_listed_vendor)
            elif not product.x_studio_vendor_number and not product.x_studio_listed_vendor:
                dict_key = 'undefined'

            res = product._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'), from_date=self.start_dt, to_date=self.end_dt)

            if dict_key in data_dict:
                data_dict[dict_key].append({
                    'key': dict_key,
                    'item': product.default_code or '-',
                    'description': product.name or '-',
                    'category': product.categ_id and product.categ_id.display_name or '-',
                    'vendor_no': product.x_studio_vendor_number or '-',
                    'cost': '{:,.2f}'.format(product.standard_price),
                    'qty_on_hand': '{:,.2f}'.format(res[product.id]['qty_available']),
                    'qty_available': '{:,.2f}'.format(res[product.id]['free_qty']),
                    'vendor_name': product.x_studio_listed_vendor or '-',
                    'float_qty_on_hand': res[product.id]['qty_available'],
                    'float_qty_available': res[product.id]['free_qty'],
                })
            else:
                data_dict[dict_key] = [{
                    'key': dict_key,
                    'item': product.default_code or '-',
                    'description': product.name or '-',
                    'category': product.categ_id and product.categ_id.display_name or '-',
                    'vendor_no': product.x_studio_vendor_number or '-',
                    'cost': '{:,.2f}'.format(product.standard_price),
                    'qty_on_hand': '{:,.2f}'.format(res[product.id]['qty_available']),
                    'qty_available': '{:,.2f}'.format(res[product.id]['free_qty']),
                    'vendor_name': product.x_studio_listed_vendor or '-',
                    'float_qty_on_hand': res[product.id]['qty_available'],
                    'float_qty_available': res[product.id]['free_qty'],
                }]

        key_list = []
        vals_list = []
        for key, value in data_dict.items():
            if key not in key_list:
                key_list.append(key)
            for val in value:
                vals_list.append([
                    val['key'],
                    val['item'],
                    val['description'],
                    val['category'],
                    val['vendor_no'],
                    val['cost'],
                    val['qty_on_hand'],
                    val['qty_available'],
                    val['vendor_name'],
                    val['float_qty_on_hand'],
                    val['float_qty_available'],
                ])
        return {
            'key_list': key_list,
            'vals_list': vals_list,
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

        record_id = self.env['stock.quant'].sudo().search([], limit=1).id
        report = self.env.ref('stock_status.action_report_stock_status_report').with_context(ctx).sudo()._render_qweb_pdf([record_id])[0]

        self.file = base64.b64encode(report)
        self.filenm = 'Stock_Status_Report.PDF'

        return {
            'name': 'Download File',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.status.wiz',
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
        worksheet = workbook.add_sheet('Stock_Status_Report')

        row = 0
        worksheet.write_merge(row, row + 1, 0, 6, 'Stock Status Report', xlwt.easyxf('font:bold on;alignment: horizontal  center;'))
        row += 2
        worksheet.write(row, 0, 'From:', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 1, from_dt, xlwt.easyxf('font:bold on'))
        worksheet.write(row, 2, '', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 3, '', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 4, '', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 5, 'To:', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 6, to_dt, xlwt.easyxf('font:bold on'))
        row += 3

        worksheet.write(row, 0, 'Item #', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 1, 'Description', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 2, 'Category', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 3, 'Vendor #', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 4, 'Cost', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 5, 'Qty on hand', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 6, 'Available Quantity', xlwt.easyxf('font:bold on'))
        row += 1

        grand_total_qty_on_hand = 0
        grand_total_qty_available = 0

        for key in data.get('key_list'):
            if key != 'undefined':
                counter = 0
                for line in data.get('vals_list'):
                    if line[0] == key:
                        counter += 1

                if counter > 0:
                    worksheet.write_merge(row, row, 0, 1, 'Vendor-' + key.split('_', 1)[0], xlwt.easyxf('font:bold on'))
                    worksheet.write_merge(row, row, 2, 3, 'Name:' + key.split('_', 1)[1], xlwt.easyxf('font:bold on'))
                    worksheet.write(row, 4, '', xlwt.easyxf('font:bold on'))
                    worksheet.write(row, 5, '', xlwt.easyxf('font:bold on'))
                    worksheet.write(row, 6, '', xlwt.easyxf('font:bold on'))
                    row += 1

                    total_qty_on_hand = 0
                    total_qty_available = 0

                    for line in data.get('vals_list'):
                        if line[0] == key:
                            worksheet.write(row, 0, line[1])
                            worksheet.write(row, 1, line[2])
                            worksheet.write(row, 2, line[3])
                            worksheet.write(row, 3, line[4])
                            worksheet.write(row, 4, line[5])
                            worksheet.write(row, 5, line[6])
                            worksheet.write(row, 6, line[7])
                            row += 1

                            total_qty_on_hand += line[9]
                            total_qty_available += line[10]

                            grand_total_qty_on_hand += line[9]
                            grand_total_qty_available += line[10]

                    worksheet.write(row, 0, '')
                    worksheet.write(row, 1, '')
                    worksheet.write(row, 2, 'Total for Vendor', xlwt.easyxf('font:bold on'))
                    worksheet.write(row, 3, '')
                    worksheet.write(row, 4, '')
                    worksheet.write(row, 5, '{:,.2f}'.format(total_qty_on_hand), xlwt.easyxf('font:bold on'))
                    worksheet.write(row, 6, '{:,.2f}'.format(total_qty_available), xlwt.easyxf('font:bold on'))
                    row += 1

        counter1 = 0
        for line in data.get('vals_list'):
            if line[0] == 'undefined':
                counter1 += 1

        if counter1 > 0:
            worksheet.write_merge(row, row, 0, 6, 'Products with "No Vendor# and No Vendor name defined"', xlwt.easyxf('font:bold on'))
            row += 1

        total_qty_on_hand1 = 0
        total_qty_available1 = 0

        for key in data.get('key_list'):
            if key == 'undefined':
                for line in data.get('vals_list'):
                    if line[0] == key:
                        worksheet.write(row, 0, line[1])
                        worksheet.write(row, 1, line[2])
                        worksheet.write(row, 2, line[3])
                        worksheet.write(row, 3, line[4])
                        worksheet.write(row, 4, line[5])
                        worksheet.write(row, 5, line[6])
                        worksheet.write(row, 6, line[7])
                        row += 1

                        total_qty_on_hand1 += line[9]
                        total_qty_available1 += line[10]

                        grand_total_qty_on_hand += line[9]
                        grand_total_qty_available += line[10]

        worksheet.write(row, 0, '')
        worksheet.write(row, 1, '')
        worksheet.write(row, 2, 'Total', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 3, '')
        worksheet.write(row, 4, '')
        worksheet.write(row, 5, '{:,.2f}'.format(total_qty_on_hand1), xlwt.easyxf('font:bold on'))
        worksheet.write(row, 6, '{:,.2f}'.format(total_qty_available1), xlwt.easyxf('font:bold on'))
        row += 1

        worksheet.write(row, 0, '')
        worksheet.write(row, 1, '')
        worksheet.write(row, 2, '')
        worksheet.write(row, 3, '')
        worksheet.write(row, 4, '')
        worksheet.write(row, 5, '')
        worksheet.write(row, 6, '')
        row += 1

        worksheet.write(row, 0, '')
        worksheet.write(row, 1, '')
        worksheet.write(row, 2, 'Grand Total', xlwt.easyxf('font:bold on'))
        worksheet.write(row, 3, '')
        worksheet.write(row, 4, '')
        worksheet.write(row, 5, '{:,.2f}'.format(grand_total_qty_on_hand), xlwt.easyxf('font:bold on'))
        worksheet.write(row, 6, '{:,.2f}'.format(grand_total_qty_available), xlwt.easyxf('font:bold on'))
        row += 1

        fp = io.BytesIO()
        workbook.save(fp)
        self.file = base64.encodestring(fp.getvalue())
        self.filenm = 'Stock_Status_Report.xls'

        return {
            'name': 'Download File',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.status.wiz',
            'res_id': self.id,
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
        }
