# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import date, datetime
from odoo.exceptions import Warning ,ValidationError

class CustomStockTransferReport(models.TransientModel):

    _name='custom.stock.transfer.report'
    _description = "Custom Stock Transfer Report"

    start_dt = fields.Date('Start Date', required=True)
    end_dt = fields.Date('End Date', required=True)

    def generate_report(self):
        if(self.start_dt <= self.end_dt):
            return self.env.ref('custom_report_stock_transfer.action_st_report').read()[0]
        else:
            raise ValidationError(_("Please enter valid start and end date."))


class report_custom_stock_transfer_report(models.AbstractModel):

    _name='report.custom_report_stock_transfer.report_custom_str'
    _description = "Report Custom Stock Transfer"

    def _get_report_values(self, docids, data=None):
        wizard_id = self.env['custom.stock.transfer.report'].browse(docids)       
        domain = [
            ('picking_id.picking_type_id.code', '=', 'internal'),
            ('picking_id.date_done', '>=', wizard_id.start_dt), 
            ('picking_id.date_done', '<=', wizard_id.end_dt)]
        stock_move_ids = self.env['stock.move.line'].search(domain)
        return {
            'docs': stock_move_ids,
            'doc_model': 'stock.move.line',
            'start_dt' : wizard_id.start_dt,
            'end_dt' : wizard_id.end_dt,
        }
