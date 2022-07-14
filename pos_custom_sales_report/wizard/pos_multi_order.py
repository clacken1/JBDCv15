import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools.translate import _
from odoo.exceptions import except_orm
from odoo import models, fields, api
from odoo.tools.misc import str2bool, xlwt
from xlwt import easyxf

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

try:
    from StringIO import StringIO 
except ImportError:
    from io import StringIO,BytesIO  


class PosMultiOrderReort(models.TransientModel):
    _name = 'pos.multi.order.wizard'
    _description = 'POS Multi order Report'

    start_date = fields.Datetime(required=True)
    end_date = fields.Datetime(required=True, default=fields.Datetime.now)
    
    @api.model
    def get_lines(self):
        vals = []
        
        domain = [
            ('state', 'in', ['paid','done','invoiced']),
            ('date_order', '>=', self.start_date),
            ('date_order', '<=', self.end_date)
        ]
        order = self.env['pos.order'].search(domain)
        for pos in order:
            for pay_line in pos.payment_ids:
                vals.append({
                    'pos_name': pos.config_id.name,
                    'name': pos.name,
                    'session_name': pos.session_id.name,
                    'date_order': pos.date_order,
                    'receipt_ref':pos.pos_reference,
                    'return': pos.name ,
                    'partner_id': pos.partner_id.name or '',
                    'sales_person': pos.user_id.name or '',
                    'order_id': pos.id,
                    'length': len(pos.ids),
                    'untax_amount' : pos.amount_total - pos.amount_tax,
                    'tax' : pos.amount_tax,
                    'total' : pos.amount_total,
                    'payment_method' : pay_line.payment_method_id.name,
                    'payment_amount' : pay_line.amount
                })

        return vals
    
    def _print_exp_report(self, data):
        # pass
        res = {}
        import base64
        filename = 'POS Multi Order Report.xls'
        workbook = xlwt.Workbook(encoding="UTF-8")
        worksheet = workbook.add_sheet('POS Multi Order Report')
        
        header_style = easyxf('font:height 200;pattern: pattern solid, fore_colour gray25; align: horiz center;font: color black; font:bold True;' "borders: top thin,left thin,right thin,bottom thin")
        font_bold = easyxf('font:height 200;pattern: pattern solid, fore_colour gray25; align: horiz left;font: color black; font:bold True;' "borders: top thin,left thin,right thin,bottom thin")

        col_count = 7

        worksheet.col(0).width = 180 * 30
        worksheet.col(1).width = 180 * 30
        worksheet.col(2).width = 180 * 30
        worksheet.col(3).width = 180 * 30
        worksheet.col(4).width = 180 * 30
        worksheet.col(5).width = 180 * 30
        for index in range(6, 20):
            if index in [12, 16]:
                worksheet.col(index).width = 210 * 30
            else:
                worksheet.col(index).width = 180 * 30
        company_id = self.env.user.company_id
        worksheet.write_merge(0, 1, 0, col_count, company_id.name, easyxf(
            'font:height 400; align: horiz center;font:bold True;' "borders: top thin,bottom thin , left thin, right thin"))
        worksheet.write(3, 1, 'Start Date', font_bold)

        date_from = data['form']['start_date']
        date_end = data['form']['end_date']
        address = ''
        if company_id.street:
            address += company_id.street
        if company_id.street2:
            address +=  ', ' + company_id.street2
        if company_id.city:
            address +=  ', ' + company_id.city
        if company_id.state_id:
            address +=  ', ' + company_id.state_id.name
        if company_id.zip:
            address +=  '-' + company_id.zip
        if company_id.country_id:
            address +=  ', ' + company_id.country_id.name

        worksheet.write_merge(3, 3, 2, 3, str(date_from))
        worksheet.write(4, 1, 'End Date', font_bold)
        worksheet.write_merge(4, 4, 2, 3, str(date_end))
        worksheet.write(5, 1, 'Address', font_bold)
        worksheet.write_merge(5, 5, 2, 6, address)
        
        worksheet.write_merge(7, 7, 0, col_count, 'POS Multi Order Report', header_style)        

        worksheet.write_merge(8, 9, 0, 0, 'Date', header_style)
        worksheet.write_merge(8, 9, 1, 1, 'Order Ref', header_style)
        worksheet.write_merge(8, 9, 2, 2, 'Receipt Number', header_style)
        worksheet.write_merge(8, 9, 3, 3, 'Untax Amount ', header_style)

        worksheet.write_merge(8, 9, 4, 4, 'Tax', header_style)
        worksheet.write_merge(8, 9, 5, 5, 'Total', header_style)
        worksheet.write_merge(8, 9, 6, 6, 'Payment Method', header_style)
        worksheet.write_merge(8, 9, 7, 7, 'Payment Amount', header_style)

        line_details = self.get_lines()
        if line_details:
            i = 10
            total_total = 0
            style_2 = easyxf('font:height 200; align: horiz right;')
            style_2.num_format_str = '0.00'
            check_lenght = 0
            pay_length = 8
            total_payment_dict = {}
            for line in line_details:
                total_total += line.get('total')
                worksheet.row(i).height = 20 * 15
                worksheet.write(i, 0, line.get('date_order').strftime("%Y-%m-%d, %H:%M:%S"))
                worksheet.write(i, 1, line.get('name', False))
                worksheet.write(i, 2, line.get('receipt_ref', False))
                worksheet.write(i, 3, line.get('untax_amount'))
                worksheet.write(i, 4, line.get('tax'))
                worksheet.write(i, 5, line.get('total'))
                worksheet.write(i, 6, line.get('payment_method'))
                worksheet.write(i, 7, line.get('payment_amount', False))
                i += 1
        import io
        fp = io.BytesIO()
        workbook.save(fp)
        export_id = self.env['pos.payment.report.download'].create(
            {'excel_file': base64.encodestring(fp.getvalue()),
             'file_name': filename},)
        fp.close()
        
        return {
            'view_mode': 'form',
            'res_id': export_id.id,
            'res_model': 'pos.payment.report.download',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'context': self._context,
            'target': 'new',
            
        }

    def generate_report(self):
        data = {}
        data['ids'] = self._context.get('active_ids', [])
        data['model'] = self._context.get('active_model', 'ir.ui.menu')
        for record in self:
            data['form'] = record.read(['start_date', 'end_date'])[0]
        return self._print_exp_report(data)


    def generate_pdf_report(self):
        datas = self.get_lines()

        datas = {
             'filter_data': datas,
        }
        return self.env.ref('pos_custom_sales_report.action_print_order_multi_details').report_action([], data=datas)


class pos_excel_report_download(models.TransientModel):
    _name = "pos.payment.report.download"
    
    excel_file = fields.Binary('Excel Report')
    file_name = fields.Char('Excel File', size=64)