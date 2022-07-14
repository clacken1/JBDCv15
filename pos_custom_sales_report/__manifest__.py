{
    "name": "POS Sales Report - pos_custom_sales_report",
    'version': '15.1.1.1',
    "summary": """ 
    POS Custom Sales Report
    """,    
    'description':"POS Custom Sales Report",
    'sequence': 1,
    'category':"Point of Sale",
    "depends": [
        "point_of_sale",
    ],
    "data": [
        'security/ir.model.access.csv',
        'wizard/res_company_view.xml',
        'wizard/pos_multi_order.xml',
        'report/pos_order.xml',
        'report/pos_order_report.xml'
    ],
    'license': 'OPL-1',       
    'installable': True,
    'auto_install': False,
    'application': True,
}
