# -*- coding: utf-8 -*-
{
    'name': "hr_payslip_custom",

    'summary': """
        hr_payslip_custom""",

    'description': """
        hr_payslip_custom
    """,
    'category': 'hr',
    'version': '0.1',
    'depends': ['base', 'hr', 'hr_payroll','mail','gm_hr_custom','hr_resignation','ps_report'],

    'data': [
        'data/data.xml',
        'views/hr_payslip.xml',
        ],
    'application':True,
}