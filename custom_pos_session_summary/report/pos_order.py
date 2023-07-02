from odoo import fields,models,api,_


class action_print_pos_session(models.AbstractModel):
    _name = 'report.custom_pos_session_summary.pos_session'
    _description = "pos_session"

    @api.model
    def _get_report_values(self, docids, data=None):
        wizard_id = self.env['pos.session.report.wizard'].browse(docids)       
        res = {
            'doc_ids': docids,
            'doc_model': 'pos.order',
            'lines': data.get('my_data'),
            'start_dt': data.get('start_date'),
            'end_dt': data.get('end_date'),
        }
        return res
