# -*- coding: utf-8 -*-

{
    'name': "Inventory Variance Report",
    'version': "15.0.0.1",
    'summary': "Inventory Variance Report",
    'description': """Inventory Variance Report""",
    'depends': ['stock_account'],
    'data': [
        'reports/inventory_variance_report.xml',
        'views/view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
