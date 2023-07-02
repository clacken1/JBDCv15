import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools.translate import _
from odoo.exceptions import except_orm
from odoo import models, fields, api
from odoo.tools.misc import str2bool, xlwt
from xlwt import easyxf
import pytz
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

try:
    from StringIO import StringIO 
except ImportError:
    from io import StringIO,BytesIO  


class Session(models.TransientModel):
    _name = 'pos.session.report.wizard'
    _description = 'POS order Payment Report'

    start_date = fields.Datetime(required=True)
    end_date = fields.Datetime(required=True, default=fields.Datetime.now)
    pos_ids = fields.Many2many('pos.config',string='Point Of Sale')
    
    @api.model
    def get_lines(self):
        vals = []
        domain = [
            ('start_at', '>=', self.start_date),
            ('start_at', '<=', self.end_date)
        ]
        if self.pos_ids:
            domain += [('config_id','in', self.pos_ids.ids)]
        order = self.env['pos.session'].search(domain)
        payments = self.env['pos.payment']
        user = self.env['res.users'].browse(self.env.uid)
        tz = pytz.timezone(user.tz)
        for pos in order:
            startdate = pytz.utc.localize(pos.start_at).astimezone(tz)
            enddate = pytz.utc.localize(pos.stop_at).astimezone(tz)
            startdate = startdate.strftime("%Y-%m-%d %H:%M:%S")
            enddate = enddate.strftime("%Y-%m-%d %H:%M:%S")
            payment_ids = payments.search([('session_id', '=', pos.id)])
            payment_method_names = payment_ids.mapped('payment_method_id').mapped('name')
            state = 'Opening Control'
            if pos.state == 'opened':
                state = 'In Progress'
            elif pos.state == 'closing_control':
                state = 'Closing Control'
            elif pos.state == 'closed':
                state = 'Closed & Posted'
            vals.append({
                'pos_name': pos.config_id.name,
                'opend_by': pos.user_id.name or '',
                'start_dt': startdate,
                'stop_dt': enddate,
                'state': state,
                'name': pos.name,
                'payment_method': ','.join(payment_method_names),
                'total': pos.total_payments_amount,
                'currency_id': pos.currency_id,
            })
        return vals
    
    def _print_exp_report(self, data):
        res = {}
        import base64
        filename = 'POS Session Report.xls'
        workbook = xlwt.Workbook(encoding="UTF-8")
        worksheet = workbook.add_sheet('POS Session Report')
        
        header_style = easyxf('font:height 200;pattern: pattern solid, fore_colour gray25; align: horiz center;font: color black; font:bold True;' "borders: top thin,left thin,right thin,bottom thin")
        font_bold = easyxf('font:height 200;pattern: pattern solid, fore_colour gray25; align: horiz left;font: color black; font:bold True;' "borders: top thin,left thin,right thin,bottom thin")

        worksheet.col(0).width = 180 * 30
        worksheet.col(1).width = 180 * 30
        worksheet.col(2).width = 180 * 30
        worksheet.col(3).width = 180 * 30
        worksheet.col(4).width = 150 * 30
        worksheet.col(5).width = 150 * 30
        worksheet.col(6).width = 210 * 40
        worksheet.col(7).width = 180 * 30

        company_id = self.env.user.company_id
        worksheet.write_merge(0, 1, 0, 7, 'Sales Summary by Location', easyxf(
            'font:height 400; align: horiz center;font:bold True;' "borders: top thin,bottom thin , left thin, right thin"))

        date_from = data['form']['start_date']
        date_end = data['form']['end_date']
        user = self.env['res.users'].browse(self.env.uid)
        tz = pytz.timezone(user.tz)
        startdate = pytz.utc.localize(self.start_date).astimezone(tz)
        enddate = pytz.utc.localize(self.end_date).astimezone(tz)
        startdate = startdate.strftime("%Y-%m-%d %H:%M:%S")
        enddate = enddate.strftime("%Y-%m-%d %H:%M:%S")

        worksheet.write(3, 1, 'Start Date', font_bold)
        worksheet.write_merge(3, 3, 2, 3, str(startdate))
        worksheet.write(4, 1, 'End Date', font_bold)
        worksheet.write_merge(4, 4, 2, 3, str(enddate))
        
        worksheet.write_merge(7, 7, 0, 7, 'POS Session Report', header_style)        

        worksheet.write_merge(8, 9, 0, 0, 'Point Of Sale', header_style)
        worksheet.write_merge(8, 9, 1, 1, 'Opened by', header_style)
        worksheet.write_merge(8, 9, 2, 2, 'Opening Date', header_style)
        worksheet.write_merge(8, 9, 3, 3, 'Closing Date ', header_style)

        worksheet.write_merge(8, 9, 4, 4, 'Status', header_style)
        worksheet.write_merge(8, 9, 5, 5, 'Session ID', header_style)
        worksheet.write_merge(8, 9, 6, 6, 'Payment Methods', header_style)
        worksheet.write_merge(8, 9, 7, 7, 'Total  ', header_style)
        line_details = self.get_lines()
        if line_details:
            i = 10
            style_2 = easyxf('font:height 200; align: horiz right;')
            style_2.num_format_str = '#,##0.00'
            for line in line_details:


                worksheet.row(i).height = 20 * 15
                worksheet.write(i, 0, line.get('pos_name', False))
                worksheet.write(i, 1, line.get('opend_by', False))
                worksheet.write(i, 2, line.get('start_dt'))
                worksheet.write(i, 3, line.get('stop_dt'))
                worksheet.write(i, 4, line.get('state'))
                worksheet.write(i, 5, line.get('name'))
                worksheet.write(i, 6, line.get('payment_method'))
                worksheet.write(i, 7, line.get('total', 0), style_2)
                i += 1

        import io
        fp = io.BytesIO()
        workbook.save(fp)
        export_id = self.env['pos.session.report.wizard.download'].create(
            {'excel_file': base64.encodestring(fp.getvalue()),
             'file_name': filename},)
        fp.close()
        
        return {
            'view_mode': 'form',
            'res_id': export_id.id,
            'res_model': 'pos.session.report.wizard.download',
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
        user = self.env['res.users'].browse(self.env.uid)
        tz = pytz.timezone(user.tz)
        startdate = pytz.utc.localize(self.start_date).astimezone(tz)
        enddate = pytz.utc.localize(self.end_date).astimezone(tz)
        startdate = startdate.strftime("%Y-%m-%d %H:%M:%S")
        enddate = enddate.strftime("%Y-%m-%d %H:%M:%S")
        return self.env.ref('custom_pos_session_summary.action_print_pos_session').report_action([], data={
            'my_data':datas,
            'start_date': startdate,
            'end_date': enddate,
            })

class pos_excel_report_download(models.TransientModel):
    _name = "pos.session.report.wizard.download"
    
    excel_file = fields.Binary('Excel Report')
    file_name = fields.Char('Excel File', size=64)