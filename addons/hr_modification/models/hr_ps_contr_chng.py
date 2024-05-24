from odoo import fields, models, api
from datetime import date, timedelta
import copy
import calendar


class InheritPayslipContract(models.Model):
    _inherit = 'hr.payslip'

    # extra_days = fields.Integer('Extra Days', readonly=True, compute='_get_extra_days')
    # per_day_wage = fields.Float("Per Day Wage", compute='_get_extra_days')
    # extra_days_deduction = fields.Integer("Days Deduction", compute="_get_deduction_days")
    #
    # @api.depends('employee_id', 'date_from', 'date_to')
    # def _get_deduction_days(self):
    #     for rec in self:
    #         if rec.date_from and rec.date_to and rec.employee_id and rec.contract_id:
    #             if not rec.contract_id.already_deducted and rec.contract_id.date_start > rec.date_from:
    #                 rec.extra_days_deduction = rec.contract_id.extra_days_to_deduct
    #                 num_days = calendar.monthrange(rec.date_from.year, rec.date_from.month)[1]
    #                 rec.per_day_wage = rec.contract_id.wage / num_days
    #             else:
    #                 rec.extra_days_deduction = 0
    #         else:
    #             rec.extra_days_deduction = 0
    #
    # @api.depends('employee_id', 'date_from', 'date_to')
    # def _get_extra_days(self):
    #     for rec in self:
    #         if rec.date_from and rec.date_to and rec.employee_id and rec.contract_id:
    #             if not rec.contract_id.extra_days_paid and rec.contract_id.extra_days_to_pay > 0:
    #                 payslip_dates = self._get_payslip_dates_list(rec.date_from, rec.date_to)
    #                 previous_month_dates = self.get_previous_month_dates(rec.date_from)
    #                 if rec.contract_id.date_start in payslip_dates + previous_month_dates:
    #                     rec.extra_days = rec.contract_id.extra_days_to_pay
    #                     num_days = calendar.monthrange(rec.date_from.year, rec.date_from.month)[1]
    #                     rec.per_day_wage = rec.contract_id.wage / num_days
    #                 else:
    #                     rec.extra_days = 0
    #                     rec.per_day_wage = 0
    #             else:
    #                 rec.extra_days = 0
    #                 rec.per_day_wage = 0
    #         else:
    #             rec.extra_days = 0
    #             rec.per_day_wage = 0
    #
    # def get_previous_month_dates(self, date_from=None):
    #     # payslip date_from will be considered as date to in that case
    #     date_to = copy.deepcopy(date_from)
    #     prev_month_from = date_from - timedelta(days=31)
    #     prev_month_dates = []
    #     while prev_month_from <= date_to:
    #         prev_month_dates.append(prev_month_from)
    #         prev_month_from += timedelta(days=1)
    #     return prev_month_dates
    #
    # def action_payslip_done(self):
    #     res = super().action_payslip_done()
    #     if self.extra_days > 0:
    #         self.contract_id.extra_days_paid = True
    #     if self.extra_days_deduction > 0:
    #         self.contract_id.already_deducted = True
    #     return res
    #
    # def approve_payslip(self):
    #     for rec in self:
    #         if rec.state == 'verify':
    #             rec.action_payslip_done()
