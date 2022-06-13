# -*- coding: utf-8 -*-
{
    "name" : "All inn one Report",
    "version" : "15.0.0.1",
    'summary': '',
    "description": """""",
    "depends" : [
        'sale_stock'],
    "data": [
        'security/ir.model.access.csv',
        'wizard/sales_summary_report.xml',
        'wizard/sale_summary.xml',
    ],
    "auto_install": False,
    "installable": True,
}
