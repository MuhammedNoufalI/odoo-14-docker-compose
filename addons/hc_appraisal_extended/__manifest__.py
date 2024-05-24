# -*- coding: utf-8 -*-
{
    'name': 'Appraisal Extended',
    "author": 'awn',
    'maintainer': 'awn,rhn,frs',
    'company': 'Hash Code IT Solutions',
    'website': 'https://hashcodeit.com/',
    'version': '14.0.1.0.1',
    'support': 'info@hashcodeit.com',
    'category': 'Human Resources',
    'summary': 'Appraisal Extended',
    'description': """ Appraisal Extended """,
    'depends': ['web','hr_appraisal','hr_contract','hc_employee_customization', 'hc_salary_info_extension'],
    'data': [
        'report/promotion_letter.xml',
        'report/promotion_letter_template.xml',
        'views/hr_appraisal_views.xml',
    ],
    "images": ["static/description/icon.png"],
    'license': 'OPL-1',
    'installable': True,
    'application': True,
    'auto_install': False,
}
