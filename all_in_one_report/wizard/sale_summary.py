# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import date, datetime
from odoo.exceptions import Warning ,ValidationError

class AllSalesSummary(models.TransientModel):

    _name='all.sale.summary.wizard'
    _description = "All Sale Summary Wizard"

    start_dt = fields.Datetime('Start Date', required=True)
    end_dt = fields.Datetime('End Date', required=True)
    report_type = fields.Selection([
        ('sas', 'Sales Analysis Summary'),
        ('sa', 'Sales Analysis')
        ], 'Report Type', default='sas', required=True)
    categ_ids = fields.Many2many('product.category', string='Product Categories')
    product_ids = fields.Many2many('product.product', string='Products')

    @api.onchange('categ_ids')
    def onchange_categ_ids(self):
        domain = {'product_ids': []}
        if self.categ_ids:
            domain = {'product_ids': [('categ_id', 'in', self.categ_ids.ids)]}
        return {'domain': domain}

    def sale_summary_generate_report(self):
        if(self.start_dt <= self.end_dt):
            if self.report_type == 'sas':
                return self.env.ref('all_in_one_report.action_sales_summary_report').report_action(self)
            else:
                return self.env.ref('all_in_one_report.action_sales_summary_report').report_action(self)
        else:
            raise ValidationError(_("Please enter valid start and end date."))


class AllConsignmentSummary(models.TransientModel):

    _name='all.consignment.summary.wizard'
    _description = "All Consignment"

    start_dt = fields.Datetime('Start Date', required=True)
    end_dt = fields.Datetime('End Date', required=True)


    def consignment_summary_generate_report(self):
        if(self.start_dt <= self.end_dt):
            return self.env.ref('all_in_one_report.action_consignment_summary_report').report_action(self)
        else:
            raise ValidationError(_("Please enter valid start and end date."))