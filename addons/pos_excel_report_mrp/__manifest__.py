{
    'name': 'POS Order Report MRP',
    'version': '1.0',
    'license': 'LGPL-3',
    'depends': ['point_of_sale', 'mrp'],
    'data': [
        'report/pos_order_excel_report_wizard.xml',
        'security/ir.model.access.csv',
        'data/server_action.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,

}
