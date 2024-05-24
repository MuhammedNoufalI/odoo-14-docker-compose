# -*- coding: utf-8 -*-

{
    'name': "Hc Attendance Customization",
    "author": "frs",
    'maintainer': '',
    'company': 'Hash Code IT Solutions',
    'website': 'https://hashcodeit.com/',
    'version': '14.0.1.0.0',
    'support': 'info@hashcodeit.com',
    'category': 'Attendance',
    'summary': "",
    'description': """
    """,
    'depends': ['hr', 'hr_attendance','employee_data_api', 'hc_shift_time'],
    'data': [
        'views/hr_attendance_view.xml',
        'views/hc_raw_attendance.xml',
    ],

    "images": ["static/description/icon.png"],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': False,
}
