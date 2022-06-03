# -*- coding: utf-8 -*-

{
    'name': "Stock Status",
    'version': "15.0.0.1",
    'summary': "Stock Status",
    'description': """Stock Status""",
    'depends': ['sale_stock', 'stock_account', 'point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'reports/stock_status_report.xml',
        'wizard/wizard_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
