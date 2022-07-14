# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import date, datetime
from odoo.exceptions import Warning ,ValidationError

class AccountMoveCustomerInvoiceAP(models.TransientModel):

    _name='account.move.customer.invoice.ap'
    _description = "Account Move Customer Invoice AP"

    start_dt = fields.Date('Start Date', required=True)
    end_dt = fields.Date('End Date', required=True)
    report_type = fields.Selection([('customer', 'Customer'), ('vendor', 'Vendor')])

    def generate_report(self):
        if(self.start_dt <= self.end_dt):
            return self.env.ref('custom_report_ap_ar.action_ap_customer_invoice_report').read()[0]
        else:
            raise ValidationError(_("Please enter valid start and end date."))


class ReportAPCustomerInvoiceDocument(models.AbstractModel):

    _name='report.custom_report_ap_ar.report_ap_customer_invoice_document'
    _description = "Report AP Customer Invoice Document"

    def _get_report_values(self, docids, data=None):
        ap_customer_invoice_id = self.env['account.move.customer.invoice.ap'].browse(docids)       
        domain = [('state', '=', 'posted'),
        ('invoice_date', '>=', ap_customer_invoice_id.start_dt), ('invoice_date', '<=', ap_customer_invoice_id.end_dt)]
        if ap_customer_invoice_id.report_type == 'customer':
            domain += [('move_type', '=', 'out_invoice')]
        elif ap_customer_invoice_id.report_type == 'vendor':
            domain += [('move_type', '=', 'in_invoice')]
        move_ids = self.env['account.move'].search(domain)
        return {
            'docs': move_ids,
            'report_type': ap_customer_invoice_id.report_type,
            'doc_model': 'account.move',
            'start_dt' : ap_customer_invoice_id.start_dt,
            'end_dt' : ap_customer_invoice_id.end_dt,
        }


class AccountMove(models.Model):
    _inherit = 'account.move'

    def ap_customer_invoice(self):
        return self.env.ref('custom_report_ap_ar.action_ap_customer_invoice_report').read()[0]

    def ap_vendor_bills(self):
        return self.env.ref('custom_report_ap_ar.action_ap_customer_invoice_report').read()[0]
