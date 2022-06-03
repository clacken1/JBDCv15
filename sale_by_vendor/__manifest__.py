# -*- coding: utf-8 -*-

{
    'name': "Sale By Vendor",
    'version': "15.0.0.1",
    'summary': "Sale By Vendor",
    'description': """Sale By Vendor""",
    'depends': ['sale_stock', 'stock_account', 'point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'reports/sale_by_vendor_report.xml',
        'wizard/wizard_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
