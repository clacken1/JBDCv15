{
    'name': "Internal Transfer Report -custom_report_stock_transfer",
    'version': '15.1.1.1',
    'summary': "custom_report_stock_transfer",
    'description': """custom_report_stock_transfer""",
    'depends': ['stock'],
    'data': [
        'security/ir.model.access.csv',
        'reports/report_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
