# -*- coding: utf-8 -*-
{
    'name': 'Employee Attendance API',
    "author": "Hashcode IT Solutions",
    'website': 'https://hashcodeit.com/',

    'version': '16.0.1.0.0',
    'support': 'info@hashcodeit.com',
    'category': 'Human Resources',
    'summary': 'API for sending raw attendance to server',
    'description': """ """,
    'depends': ['base','hr', 'hc_shift_time', 'hc_employee_customization', 'hr_appraisal', 'hr_attendance'],
    'data': [
            "security/ir.model.access.csv",
            "views/api_logs_views.xml",
            "views/res_config_settings.xml",
            "views/hr_employee_views.xml",
    ],
    "images": ["static/description/icon.png"],
    'license': 'OPL-1',
    'installable': False,
    'auto_install': False,
    'application': False,
}
