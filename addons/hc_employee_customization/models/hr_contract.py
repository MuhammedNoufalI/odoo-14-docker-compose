# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date, time
from dateutil.relativedelta import relativedelta


class HrContract(models.Model):
    _inherit = 'hr.contract'
    _description = 'Employee Contract'

    total_salary = fields.Float(string='Total Salary',
                                compute='_compute_salary_amount',tracking=True)  # compute='_compute_total_salary'
    salary_rule_ids = fields.One2many('hc.contract.salary.rule', 'contract_id', string="Salary Rule Lines")

    @api.depends('salary_rule_ids.amount')
    def _compute_salary_amount(self):
        for rec in self:
            amount_total = 0
            if rec.salary_rule_ids:
                for rule in rec.salary_rule_ids:
                    amount_total = amount_total + rule.amount
            rec.total_salary = amount_total

    @api.model
    def create(self, vals):
        employee_id = vals.get('employee_id')
        employee = self.env['hr.employee'].search([('id', '=', employee_id)])
        end_date = vals.get('date_end')
        start_date = vals.get('date_start')
        employee.no_of_contracts += 1
        if employee.oe_emp_sequence is False:
            raise UserError(_("Please Update the Employee ID of the Employee."))
        if not self.env.context.get('skip_contract_closing'):
            contract = self.env['hr.contract'].search(
                [('employee_id', '=', employee_id), ('state', '!=', 'cancel'), ('date_end', '=', None)], limit=1)
            if contract and contract.date_end:
                contract.date_end = datetime.strptime(start_date, "%Y-%m-%d") - relativedelta(days=1)
                contract.state = 'close'
        if vals.get('name', '') == '':
            vals['name'] = employee.oe_emp_sequence + '/00' + str(employee.no_of_contracts)
        res = super(HrContract, self).create(vals)
        if not res['salary_rule_ids']:
            salary_rules = self.env['hr.salary.rule'].search([('update_to_contract', '=', True)])
            if salary_rules:
                salary_rule_list = []
                for rule in salary_rules:
                    salary_rule_dict = {
                        'salary_rule_id': rule.id,
                        'amount': 0,
                    }
                    salary_rule_list.append((0, 0, salary_rule_dict))
                res.salary_rule_ids = salary_rule_list
        return res

    # @api.onchange('structure_type_id')
    # def update_salary_rules(self):

    def update_salary_rules(self):
        for rec in self:
            if rec.structure_type_id.default_struct_id:
                # lines = [(5, 0, 0)]
                lines = []
                for rule in self.structure_type_id.default_struct_id.rule_ids.filtered(lambda x: x.update_to_contract):
                    val = {
                        'salary_rule_id': rule.id,
                        'is_updated': True,
                    }
                    lines.append((0, 0, val))
                if lines:
                    rec.salary_rule_ids = False
                    rec.salary_rule_ids = lines

    # @api.onchange('struct_id')
    # def _onchange_salary_rule(self):
    #     new_list = []
    #     for rules in self.struct_id.rule_ids:
    #         replaced_field_name = rules.name.replace(' ', '_')
    #         replaced_field_lower_case = replaced_field_name.lower()
    #         new_list.append('x_' + replaced_field_lower_case)
    # view_arch = """
    #                  <xpath expr="//group[@name='allowances_employee_customization']" position="inside">
    #                            <field name='""" + 'x_' + rules.name + """' attrs="{'invisible': [('""" + 'x_' + rules.name + """', 'not in',  list)]}"/>
    #                  </xpath>
    #             """
    # view_id = self.env['ir.ui.view'].browse(
    #     self.env['ir.ui.view'].get_view_id('hr_contract.hr_contract_view_form'))
    # view = self.env['ir.ui.view'].update({
    #     'model': 'hr.contract',
    #     'model_data_id': 'hr.contract',
    #     'type': 'form',
    #     'mode': 'extension',
    #     'arch': view_arch,
    #     'inherit_id': view_id.id})


class HcContractSalaryRule(models.Model):
    _name = 'hc.contract.salary.rule'
    _description = 'Employee Contract'

    contract_id = fields.Many2one('hr.contract', string="Contract ID")
    salary_rule_id = fields.Many2one('hr.salary.rule', string="Salary Rule")
    amount = fields.Float(string="Amount")
    is_updated = fields.Boolean("Is Updated")

    # @api.model
    # def create(self, vals):
    #     res = super(HcContractSalaryRule, self).create(vals)
    #     if res['contract_id'].salary_rule_ids.filtered(lambda r: r.salary_rule_id.code == res['salary_rule_id'].code):
    #         raise UserError(_("Salary Rule Already Exist"))

        # return res

