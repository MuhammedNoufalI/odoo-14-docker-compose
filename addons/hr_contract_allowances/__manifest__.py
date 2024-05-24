# -*- coding: utf-8 -*-
{'name': "Employee Contract Allowances ",
 'summary': """
       Multiple Allowances for employee""",
 'description': """
            Add many allowances to any employee, include in payroll and END of Service Reward calculation
    """,
 'website': "https://ivalue-s.com",
 'email': "info@ivalue-s.com",
 'author': "I VALUE solutions",
 'license': "OPL-1",
 'category': 'HR',
 'version': '0.1',
 'images': ['static/description/Banner.png'],
 'depends': ['base', 'mail', 'hr_contract', 'hr_payroll', 'hr_work_entry_contract'],
 'data': [
     'data/data.xml',
     'security/ir.model.access.csv',
     'views/hr_contract_views.xml',
     'views/hr_pyslip_view.xml',
     'views/hr_salary_rule_view.xml'
 ],
 'demo': []
 }
