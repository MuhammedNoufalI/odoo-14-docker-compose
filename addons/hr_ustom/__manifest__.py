# -*- coding: utf-8 -*-
{
    'name': "Hr Custom",

    'summary': """
        HR CUSTOM""",

    'description': """
        HR CUSTOM
    """,
    'category': 'hr',
    'version': '0.1',
    'depends': ['base', 'hr', 'resource','gm_hr_custom','planning','hr_holidays','report_xlsx'],

    'data': [
        # 'data/data.xml',
        'security/ir.model.access.csv',
        'views/working_time_view.xml',
        'views/hr_employee_view.xml',
        'views/employee_attendance_view.xml',
        'views/hr_holidays.xml',
        'reports/report.xml',
        'reports/templates.xml',
        'wizard/employee_attendance_multi.xml',
    ],
'application':True,
}