# -*- coding: utf-8 -*-
import base64
import xlwt
import io
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import models, api, fields


class StockStatusWizard(models.Model):

    _name = 'stock.status.wiz'
    _description = 'Stock Status Wizard'

    start_dt = fields.Datetime(string='From', default=fields.Date.today().replace(day=1))
    end_dt = fields.Datetime(string='To', default=fields.Date.context_today)

    state = fields.Boolean(string='State')
    file = fields.Binary(string='File')
    filenm = fields.Char(
        string='Filename', default='Stock_Status_Report.xls')

    def get_datetime_usertimezone(self, dt):
        user_tz = pytz.timezone(self.env.user.tz)
        datetm_usertz = pytz.utc.localize(dt).astimezone(user_tz)
        return datetm_usertz.strftime("%Y-%m-%d %H:%M:%S")

    def get_data(self, report_type):
        records = self.env['stock.move'].sudo().search([
            ('date', '>=', self.start_dt),
            ('date', '<=', self.end_dt),
            ('state', '=', 'done'),
        ])

        return records

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

        # total_1 = 0
        # total_3 = 0
        # total_4 = 0
        # total_6 = 0

        # worksheet.write(row, 0, '3')
        # worksheet.write(row, 1, str(2))
        # worksheet.write(row, 2, '29%')
        # worksheet.write(row, 3, '10')
        # worksheet.write(row, 4, '50000')
        # worksheet.write(row, 5, '15%')
        # worksheet.write(row, 6, '30000')
        # worksheet.write(row, 7, '12%')
        # row += 1

        # worksheet.write(row, 0, '', xlwt.easyxf('font:bold on'))
        # worksheet.write(row, 1, '', xlwt.easyxf('font:bold on'))
        # worksheet.write(row, 2, '', xlwt.easyxf('font:bold on'))
        # worksheet.write(row, 3, '', xlwt.easyxf('font:bold on'))
        # worksheet.write(row, 4, '', xlwt.easyxf('font:bold on'))
        # worksheet.write(row, 5, '', xlwt.easyxf('font:bold on'))
        # worksheet.write(row, 6, '', xlwt.easyxf('font:bold on'))
        # worksheet.write(row, 7, '', xlwt.easyxf('font:bold on'))
        # row += 1

        # worksheet.write(row, 0, 'Grand Totals', xlwt.easyxf('font:bold on'))
        # worksheet.write(row, 1, str(total_1), xlwt.easyxf('font:bold on'))
        # worksheet.write(row, 2, '', xlwt.easyxf('font:bold on'))
        # worksheet.write(row, 3, str(total_3), xlwt.easyxf('font:bold on'))
        # worksheet.write(row, 4, str(total_4), xlwt.easyxf('font:bold on'))
        # worksheet.write(row, 5, '', xlwt.easyxf('font:bold on'))
        # worksheet.write(row, 6, str(total_6), xlwt.easyxf('font:bold on'))
        # worksheet.write(row, 7, '', xlwt.easyxf('font:bold on'))
        # row += 1

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
