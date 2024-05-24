from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError, ValidationError


class BusinessTransferLetter(models.Model):
    _name = "business.transfer.letter"
    _description = "Business Transfer Letter"
    _rec_name = 'employee_name'

    employee_id = fields.Many2one('hr.employee', 'Employee ID')
    employee_name = fields.Char(string='Employee Name')
    employee_code = fields.Char(string='Employee Code')
    business_unit = fields.Char('Business Unit')
    old_business_unit = fields.Char('Old Business Unit')
    company_name = fields.Char('Company Name')
    street = fields.Char('street1')
    street2 = fields.Char('street2')
    zip = fields.Char('zip')
    city = fields.Char('city')
    state_id = fields.Char('state')
    country_id = fields.Char(string='Country')
    employee_job_position = fields.Char('Employee job Position')
    contract_id = fields.Many2one('hr.contract', string="Contract ID")
    salary_rule_ids = fields.One2many('old.contract.salary.rule', 'transfer_id', string="Salary Rule Lines")
    total_salary = fields.Float('Total Salary')
    employee_new_position = fields.Many2one('hr.job', "New Job Position")
    new_total_salary = fields.Float(string='Total Salary', compute='_compute_new_salary')
    new_salary_rule_ids = fields.One2many('hc.contract.salary.rule', 'transfer_id', string="Salary Rule Lines")
    salary_structure = fields.Many2one("hr.payroll.structure", 'Salary Structure')
    state = fields.Selection(
        [('draft', 'Draft'),
         ('confirm', 'Confirmed')], string="state", default='draft')

    def transfer_form_confirm(self):
        for rec in self:
            if not rec.new_salary_rule_ids:
                raise UserError("Please add new salary details")
            rec.state = 'confirm'

    def transfer_form_rest_to_draft(self):
        for rec in self:
            rec.state = 'draft'

    @api.depends('new_salary_rule_ids.amount')
    def _compute_new_salary(self):
        for rec in self:
            amount_total = 0
            if rec.new_salary_rule_ids:
                for rule in rec.new_salary_rule_ids:
                    amount_total = amount_total + rule.amount
            rec.new_total_salary = amount_total


class OldContractSalary(models.Model):
    _name = 'old.contract.salary.rule'

    transfer_id = fields.Many2one('business.transfer.letter', string="New ID")
    salary_rule_id = fields.Many2one('hr.salary.rule', string='Salary Rule')
    amount = fields.Float(string="Amount")


class HcContractSalary(models.Model):
    _inherit = 'hc.contract.salary.rule'

    transfer_id = fields.Many2one('business.transfer.letter', string="New ID")
