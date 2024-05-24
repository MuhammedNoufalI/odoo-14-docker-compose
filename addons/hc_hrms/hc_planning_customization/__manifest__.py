# -*- coding: utf-8 -*-

{
    'name': 'Planning Customization',
    "author": "Hashcode IT Solutions",
    'website': 'https://hashcodeit.com/',
    'version': '16.0.1.0.8',
    'support': 'info@hashcodeit.com',
    'category': 'Inventory',
    'summary': 'This module is used to add some customization for planning',
    'description': """ """,
    'depends': ['planning', 'hc_branch', 'web_domain_field','hr_employee_firstname', 'hc_shift_time' ],
    'external_dependencies': {
        'python': ['pandas'],
    },
    'data': [
        'security/security.xml',
        "data/sequence.xml",
        "views/employee_views.xml",
        "views/planning_views.xml",
        "views/planning_template_views.xml",
    ],
    'assets': {
        'web.assets_qweb': [
            'hc_planning_customization/static/src/xml/**/*',
        ],
    },
    "images": ["static/description/icon.png"],
    'license': 'OPL-1',
    'installable': False,
    'auto_install': False,
    'application': False,
}
