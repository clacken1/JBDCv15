from odoo import fields,models,api,_

class ResCompany(models.Model):
    _inherit = "res.company"

    report_header_tilte = fields.Char('Report Header Title')

class PrintPOSMultiOrderReport(models.AbstractModel):
    _name = 'report.pos_custom_sales_report.print_pos_multi_order_report'
    _description = "Print POS Multi Order Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        res = {
            'doc_ids': docids,
            'doc_model': 'pos.order',
            'lines': data.get('filter_data'),
            'company_id': self.env.user.company_id,
        }
        return res
