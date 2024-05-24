# -*- coding: utf-8 -*-
{
    'name': "HR End of Service Custom",

    'summary': """
        HR End of Service Custom""",

    'description': """
        HR CUSTOM
    """,
    'category': 'hr',
    'version': '0.1',
    'depends': ['base', 'hr', 'hr_holidays', 'hr_gratuity_settlement', 'hr_payroll', 'hr_resignation'],

    'data': [
        'data/salary_rule.xml',
        'views/hr_leave_type.xml',
        'views/hr_gratuity.xml',
        'views/hr_resignation.xml',
        'views/menuitems.xml',
    ],
'application':True,
}