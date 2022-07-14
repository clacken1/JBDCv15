{
    "name": "POS Sales Summary Report - custom_pos_session_summary",
    'version': '15.1.1.1',
    "summary": """ custom_pos_session_summary
    """,    
    'description':"custom_pos_session_summary",
    'category':"Point of Sale",
    "depends": [
        "point_of_sale",
    ],
    "data": [
        'security/ir.model.access.csv',
        'wizard/pos_order_payment_report.xml',
        'report/pos_order_payment_template.xml',
    ],
    'qweb': [],
    'css': [],
    'js': [],
    'images': [],
    'demo': [],
    'license': 'OPL-1',       
    'installable': True,
    'auto_install': False,
    'application': True,
}
