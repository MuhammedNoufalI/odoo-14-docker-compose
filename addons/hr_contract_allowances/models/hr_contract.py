# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from odoo import tools, _
from odoo.exceptions import UserError

class Allowance(models.Model):
    _name = 'hr.allowance'
    _rec_name = 'name'
    _description = 'Allowance'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Allowance Name", required=True)
    active = fields.Boolean(string="Active", default=True)


class ContractAllowanceLine(models.Model):
    _name = 'hr.contract.allowance.line'
    _rec_name = 'allowance_id'
    _description = 'Contract Allowance Line'

    allowance_id = fields.Many2one(comodel_name="hr.allowance", string="Allowance")
    contract_id = fields.Many2one(comodel_name="hr.contract", string="Contract")
    amount = fields.Float(string="Amount")
    payslip_id = fields.Many2one(comodel_name="hr.payslip", string="Payslip")


class ContractDeductionsLine(models.Model):
    _name = 'hr.contract.deduction.line'
    _rec_name = 'allowance_id'
    _description = 'Contract Deduction Line'

    allowance_id = fields.Many2one(comodel_name="hr.allowance", string="Deduction")
    contract_id = fields.Many2one(comodel_name="hr.contract", string="Contract")
    amount = fields.Float(string="Amount")
    payslip_id = fields.Many2one(comodel_name="hr.payslip", string="Payslip")


class Contract(models.Model):
    _name = "hr.contract"
    _inherit = 'hr.contract'

    @api.constrains('state')
    def _check_state(self):
        for record in self:
            if record.state == 'open':
                contract_ids = self.env['hr.contract'].search(
                    [('employee_id', '=', record.employee_id.id), ('state', '=', 'open')])
                if len(contract_ids) > 1:
                    raise exceptions.ValidationError(_('Employee Must Have Only One Running Contract'))

    # allowances_ids = fields.One2many(comodel_name="hr.contract.allowance.line", inverse_name="contract_id")
    # deduction_ids = fields.One2many(comodel_name="hr.contract.deduction.line", inverse_name="contract_id")
    #
    # def get_all_allowances(self):
    #     return sum(self.allowances_ids.mapped('amount'))
    #
    # def get_all_deductions(self):
    #     return sum(self.deduction_ids.mapped('amount'))

    #
    # def add_allowance_amount(self, name):
    #     result = 0
    #     for contract in self:
    #         for allowances in contract.allowances_ids:
    #             if allowances.allowance_id.name == name:
    #                 result = allowances.amount
    #                 break;
    #
    #     return result
    #
    #
    # def add_deductions_amount(self, name):
    #     result = 0
    #     for contract in self:
    #         for deductions in contract.deduction_ids:
    #             if deductions.allowance_id.name == name:
    #                 result = deductions.amount
    #                 break;
    #
    #     return result

    basic = fields.Monetary(
        'Basic',
        # compute='_compute_basic_amount'
    )
    hra = fields.Monetary('House Rent Allowance')
    other_allowance = fields.Monetary('Other Allowance')
    # gross_salary = fields.Monetary('Gross Salary')

    # last_month_arrears = fields.Monetary('Previous Month Salary Arrears')
    # medical_reimbursement = fields.Monetary('MEDICAL Reimbursement')
    # other_reimbursement = fields.Monetary('OTHER Reimbursement')
    # new_joiners_unpaid_salary = fields.Monetary()
    #
    # hra_deduction = fields.Monetary("HRA Deduction")
    # absent_days = fields.Monetary('Previous Month Absent Days')
    # loan = fields.Monetary('Loan/ Salary Advance')
    # other_deductions = fields.Monetary('OTHER Deductions')
    # rta = fields.Monetary(string='RTA Fines')
    # ticket_deduction = fields.Monetary()
    # visa_fines = fields.Monetary('Visa Fines')
    # insurance_premium_deduction = fields.Monetary()

    # @api.depends('wage')
    # def _compute_basic_amount(self):
    #     for rec in self:
    #         rec.basic = (rec.wage / 100) * 60

    # @api.onchange('wage')
    # def _onchange_wage(self):
    #     if self.wage:
    #         if not self.wage == self.other_allowance + self.hra + self.basic:
    #             raise UserError('Gross Not Matching')
