# -*- coding: utf-8 -*-

{
    'name': 'Branch Management',
    "author": "Hashcode IT Solutions",
    'website': 'https://hashcodeit.com/',

    'version': '16.0.1.0.1',
    'category': 'Human Resources',
    'summary': 'Categorizing the company with the branch',
    'description': """ """,
    'depends': ['base', 'hr', 'hr_work_entry', 'hr_attendance', 'hr_contract', 'resource'],
    'data': [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/hc_branch_views.xml",
        "views/hr_employee_views.xml",
        "views/attendance_device_views.xml",
        "views/hc_company_views.xml",
        "wizard/change_branch_wiz_views.xml",
    ],
    "images": ["static/description/icon.png"],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': True,
    "images": [],
    
}
