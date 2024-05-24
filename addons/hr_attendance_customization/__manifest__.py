# -*- coding: utf-8 -*-
{
    'name': "Hr Attendance Customization",
    'summary': """
        - Remove Extra field From Tree View
        - Attendance Report
    """,
    'description': """
        - Remove Extra field From Tree View
        - Attendance Report
    """,
    'author': "odooErp.ae",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'hr', 'hr_attendance', 'gm_hr_custom', 'to_attendance_device','employee_data_api','hc_shift_time'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'report/report.xml',
        'report/report_temp.xml',
        'wizard/wizard.xml'
    ],
    'demo': [
        'demo/demo.xml',
    ],
}
