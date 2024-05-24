# -*- coding: utf-8 -*-
{
    'name': "Hr Modification",
    'summary': """Hr Modification""",
    'description': """
        HR modification
    """,
    'author': "OdooERP.ae",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'hr_payroll', 'hr',
                'leave_custom',
                'hr_holidays',
                'hr_attendance'],
    'data': [
        # 'security/ir.model.access.csv',
        'data/data.xml',
        'views/inherit_res_config.xml',
        'views/views.xml',
        'views/inherit_hr_payslip_custom.xml',
        'views/templates.xml',
        'views/hr_contract.xml'

    ]
}
