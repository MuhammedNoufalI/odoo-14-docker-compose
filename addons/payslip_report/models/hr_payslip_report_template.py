from odoo import fields, models, api


class PayslipReportTemplate(models.Model):
    _name = 'hr.payslip.report.template'

    name = fields.Char('Name', reqired=True)
    description = fields.Text('Description')
    salary_rule_ids = fields.Many2many(
        'hr.salary.rule',
        'hr_payroll_report_template_salary_rule_rel',
        'hr_payroll_report_template_id',
        'salary_rule_id',
        'Salary Rules', required=True
    )
    employee_ids = fields.Many2many(
        'hr.employee',
        'payroll_report_template_employee_rel',
        'payroll_report_template_id',
        'employee_id',
        'Employees'
    )