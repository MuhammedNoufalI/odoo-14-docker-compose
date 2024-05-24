# -*- coding: utf-8 -*-

import datetime
from datetime import datetime, date, timedelta
import logging

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import format_date
import time
_logger = logging.getLogger(__name__)


class HrAppraisal(models.Model):
    _inherit = 'hr.appraisal'

    total_salary = fields.Float(string='Total Salary',readonly=True)  # compute='_compute_total_salary'
    salary_rule_ids = fields.One2many('hc.contract.salary.rule', 'appraisal_id', string="Salary Rule Lines",readonly=True)
    wage_type = fields.Selection([('monthly', 'Monthly Fixed Wage'), ('hourly', 'Hourly Wage')], default='monthly')
    wage = fields.Monetary('Wage', tracking=True, help="Employee's monthly gross wage.",readonly=True)
    currency_id = fields.Many2one(string="Currency", related='company_id.currency_id', readonly=True)

    new_total_salary = fields.Float(string='Total Salary', compute='_compute_new_salary', store=True)  # compute='_compute_total_salary'
    new_salary_rule_ids = fields.One2many('hc.contract.salary.rule', 'appraisal_new_id', string="Salary Rule Lines")
    new_wage_type = fields.Selection([('monthly', 'Monthly Fixed Wage'), ('hourly', 'Hourly Wage')],string='Wage Type', default='monthly',required=True)
    new_wage = fields.Monetary('Wage', tracking=True, help="Employee's monthly gross wage.")

    contract_id = fields.Many2one('hr.contract', string='Contract id', compute='_compute_current_contract')
    new_contract_date = fields.Date('Contract Start Date',  compute='_compute_contract_date')
    job_id = fields.Many2one(readonly=False)
    new_job_id = fields.Many2one('hr.job', readonly=False, string="New Job Position")
    last_job_position = fields.Char(string='Last job position')
    increment_amount = fields.Float('Increment Amount')
    expected_salary = fields.Float('Expected Salary')
    is_expected_salary_hide = fields.Boolean('Is Hide')
    struct_id = fields.Many2one('hr.payroll.structure', string='Salary Structure',
                                related='contract_id.struct_id')

    @api.onchange('new_total_salary')
    def _hide_expected_salary(self):
        for rec in self:
            if rec.new_total_salary == rec.expected_salary:
                rec.is_expected_salary_hide = True
            else:
                rec.is_expected_salary_hide = False



    @api.onchange('increment_amount')
    def _compute_expected_salary(self):
        for rec in self:
            if rec.increment_amount:
                rec.expected_salary = rec.increment_amount + rec.total_salary
            else:
                rec.expected_salary = False


    @api.depends('employee_id', 'contract_id')
    @api.onchange('employee_id','expected_salary')
    def _compute_current_contract(self):
        current_contract_obj = self.env['hr.contract'].search(['&',('employee_id', '=', self.employee_id.id), ('state', '=', 'open')], limit=1)
        for rec in self:
            if current_contract_obj and self.state in ['new', 'pending']:
                rec.contract_id = current_contract_obj.id
                self.compute_salary_amount(current_contract_obj)
            else:
                if not self.contract_id:
                    rec.contract_id = False

    def compute_salary_amount(self, current_contract):
        for rec in self:
            if self.contract_id:
                rule_list = []
                rule_list_name = []
                amount_total = 0
                self.salary_rule_ids = False
                for rule in current_contract.salary_rule_ids:
                    copy_rule = rule.copy()
                    copy_rule.contract_id = False
                    rule_list.append(copy_rule.id)
                    amount = 0.00
                    if rec.increment_amount:
                        if copy_rule.salary_rule_id.code == 'BASIC':
                            amount = rec.expected_salary*0.6
                        rule_list_name.append((0, 0, {
                             'salary_rule_id': copy_rule.salary_rule_id.id,
                             'amount': amount,
                         }))
                rec.wage = current_contract.wage
                rec.wage_type = current_contract.structure_type_id.wage_type
                rec.salary_rule_ids = rule_list
                if rec.increment_amount and not rec.new_salary_rule_ids:
                    rec.new_salary_rule_ids = rule_list_name
                if not rec.job_id:
                    rec.job_id = current_contract.job_id
                if rec.salary_rule_ids:
                    for rule in rec.salary_rule_ids:
                        amount_total = amount_total + rule.amount
                rec.total_salary = amount_total
            else:
                rec.wage = 0
                rec.wage_type = 'monthly'
                rec.salary_rule_ids = []

    @api.depends('new_salary_rule_ids.amount')
    def _compute_new_salary(self):
        for rec in self:
            amount_total = 0
            if rec.new_salary_rule_ids:
                for rule in rec.new_salary_rule_ids:
                    amount_total = amount_total + rule.amount
            rec.new_total_salary = amount_total

    @api.depends('new_contract_date')
    def _compute_contract_date(self):
        for rec in self:
            rec.new_contract_date = self.date_close

    def action_confirm(self):
        res = super(HrAppraisal, self).action_confirm()
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        if self.new_contract_date <= today:
            raise UserError(_("Pls Use Future date as Current date"))
        # if self.date_close < self.contract_id.date_end:
        #         raise UserError(_("You can only create new contract after the ending current running contract"))
        return res

    def write(self, vals):
        res = super(HrAppraisal, self).write(vals)
        for rec in self:
            if rec.expected_salary and rec.new_total_salary > rec.expected_salary or rec.new_total_salary < rec.expected_salary:
                raise UserError(_("Yours Total salary is not Satisfying with the Expected Salary"))
        return res


    # @api.model_create_multi
    # def create(self, vals):
    #     res = super(HrAppraisal, self).create(vals)
    #     current_contract = self.env['hr.contract'].search([('employee_id', '=', res.employee_id.id), ('state', '=', 'open')], limit=1)
    #     if current_contract:
    #         rule_list = []
    #         res.salary_rule_ids = False
    #         for rule in current_contract.salary_rule_ids:
    #             copy_rule = rule.copy()
    #             copy_rule.contract_id = False
    #             rule_list.append(copy_rule.id)
    #         res.update({
    #             'new_wage': current_contract.wage,
    #             'new_wage_type': current_contract.wage_type,
    #             'new_salary_rule_ids': rule_list,
    #         })
    #     return res

    def change_current_contract(self, current_obj):
        self.last_job_position = current_obj.job_id.name
        current_obj.update({'date_end': self.date_close - relativedelta(days=1)})


    def action_done(self):
        res = super(HrAppraisal, self).action_done()
        current_contract = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id), ('state', '=', 'open')])
        if current_contract:
            self.change_current_contract(current_contract)
        new_contract = self.env['hr.contract'].with_context(skip_contract_closing=True).create({
            'name': self.employee_id.oe_emp_sequence + '/00' + str(self.employee_id.no_of_contracts),
            'employee_id': self.employee_id.id,
            'job_id': self.new_job_id.id,
            'date_start': self.date_close,
            # 'resource_calendar_id': vals['resource_calendar_id'],
            'wage_type': self.new_wage_type,
            'wage': self.new_wage,
            'salary_rule_ids':  self.new_salary_rule_ids.ids,
            'kanban_state': 'done'
        })
        # self.created_contract_id = new_contract.id
        return res


    def action_open_contract(self):
        self.ensure_one()
        return {
            'type':'ir.actions.act_window',
            'name': 'Contracts',
            'res_model': 'hr.contract',
            'domain':[('employee_id', '=', self.employee_id.id)],
            'view_mode': 'tree,form',
            'target':'current'
        }


    def print_promotion_letter(self):
        return self.env.ref('hc_appraisal_extended.print_promotion_letter_pdf').report_action(self)



class HcContractSalaryRule(models.Model):
    _inherit = 'hc.contract.salary.rule'

    appraisal_id = fields.Many2one('hr.appraisal', string="Appraisal")
    appraisal_new_id = fields.Many2one('hr.appraisal', string="New Appraisal")

