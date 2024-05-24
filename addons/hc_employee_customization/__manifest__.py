# -*- coding:utf-8 -*-

{
    'name': 'Employee & Payroll Customization',
    'category': 'Generic Modules/Human Resources',
    "author": "Hashcode IT Solutions",
    'website': 'https://hashcodeit.com/',
    'version': '14.0.0.1',
    'support': 'info@hashcodeit.com',
    'sequence': 1,
    'summary': 'Employee & Payroll Customizations',
    'description': "",
    'depends': ['hr_payroll', 'hr','hr_contract','hr_work_entry_contract'],
    'data': [
        "security/ir.model.access.csv",
        'views/hr_salary_rules_views.xml',
        'views/hr_contract_views.xml',
        # 'views/hr_employee_views.xml',
        # 'views/cost_center_code_views.xml',
    ],
    "images": ["static/description/icon.png"],
    'license': 'OPL-1',
    'application': True,
}
