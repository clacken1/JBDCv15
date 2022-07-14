{
    'name': "AP & AR Sales Report - custom_report_ap_ar",
    'version': '15.1.1.1',
    'summary': "custom_report_ap_ar",
    'description': """custom_report_ap_ar""",
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'reports/report_view.xml',
        'views/view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
