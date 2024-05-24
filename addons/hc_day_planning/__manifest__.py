# -*- coding: utf-8 -*-

{
    'name': "Hc Day Planning",
    "author": "frs",
    'maintainer': '',
    'company': 'Hash Code IT Solutions',
    'website': 'https://hashcodeit.com/',
    'version': '14.0.1.0.0',
    'support': 'info@hashcodeit.com',
    'category': 'Planning',
    'summary': "",
    'description': """
    """,
    'depends': ['planning', 'hr_contract'],
    'data': [
        'views/planning_slot_view.xml',
        'views/planning_slot_template.xml',
        'data/cron_job.xml'
    ],

    "images": ["static/description/icon.png"],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': False,
}
