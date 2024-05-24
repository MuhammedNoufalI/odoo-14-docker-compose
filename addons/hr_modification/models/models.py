# -*- coding: utf-8 -*-
import copy

from odoo import models, fields, api, _
from datetime import date
import numpy as np
from datetime import datetime, timedelta
from odoo.exceptions import UserError


class InheritHrPayslip(models.Model):
    _inherit = 'hr.payslip'

    emp_total_leaves = fields.Integer("Total Sick Leaves")
    emp_month_leaves = fields.Integer("Month Sick Leaves")
    total_days = fields.Integer("Total Days")
    full_paid_remaining = fields.Integer("Fully Paid Remaining", compute="_get_fully_paid_remaining")
    paid_leaves = fields.Integer("Paid Leaves", readonly=True)
    deduct_able_sick_leaves = fields.Integer("Sick Leaves Full Deductible", readonly=True)
    annual_leave_remaining = fields.Integer("Annual Leave Remaining", compute="_onchange_employee_id_annual",
                                            readonly=True)
    month_annual_leave = fields.Integer("Month Annual Leave", readonly=True)
    month_unpaid_leaves = fields.Integer("Unpaid Leaves", readonly=True)
    month_unpaid_leaves_half = fields.Integer("Half Paid Leaves", readonly=True)
    name = fields.Char(string='Payslip Name', readonly=False,
                       states={'draft': [('readonly', False)]})
    half_deductible_leaves = fields.Integer("Half Deductible Sick Leaves", readonly=True)
    work_days_manually = fields.Boolean("Get Work Days From Manually System")
    month_absence = fields.Integer("Month Absence", readonly=True)
    month_attendance = fields.Integer("Month Attendance", readonly=True)

    # replace fields
    # struct_id = fields.Many2one('hr.payroll.structure', string='Structure',
    #                             readonly=True, states={'draft': [('readonly', False)]}, default=13,
    #                             help='Defines the rules that have to be applied to this payslip, accordingly '
    #                                  'to the contract chosen. If you let empty the field contract, this field isn\'t '
    #                                  'mandatory anymore and thus the rules applied will be all the rules set on the '
    #                                  'structure of all contracts of the employee valid for the chosen period')
    # struct_id_2 = fields.Many2one('hr.payroll.structure', string='Variable Additions', readonly=True,
    #                               states={'draft': [('readonly', False)], 'verify': [('readonly', False)]}, default=14)
    # struct_id_3 = fields.Many2one('hr.payroll.structure', string='Variable Deductions', readonly=True,
    #                               states={'draft': [('readonly', False)], 'verify': [('readonly', False)]}, default=15)

    @api.depends('employee_id')
    def _get_fully_paid_remaining(self):
        for rec in self:
            if rec.employee_id:
                rec.full_paid_remaining = rec.employee_id.fully_paid_rmng_sick_lve
            else:
                rec.full_paid_remaining = 0

    @api.depends('employee_id')
    def _onchange_employee_id_annual(self):
        for rec in self:
            if rec.employee_id:
                # rec.annual_leave_remaining = rec.employee_id.remaining_leaves
                rec.annual_leave_remaining = self.get_annual_leaves_remaining(self.employee_id)
            else:
                rec.annual_leave_remaining = 0

    def get_annual_leaves_remaining(self, employee_id=None):
        annual_leaves = self.env['hr.leave.report'].search(
            [('employee_id', '=', employee_id.id), ('holiday_status_id.is_annual_leave', '=', True),
             ('state', '=', 'validate')])
        total_allowed = annual_leaves.filtered(lambda rec: rec.number_of_days > 0)
        used_days = annual_leaves.filtered(lambda rec: rec.number_of_days < 0)
        if total_allowed:
            return sum(total_allowed.mapped('number_of_days')) + sum(used_days.mapped('number_of_days'))
        else:
            return 0

    @api.onchange("employee_id", 'date_from', 'date_to')
    def _onchange_employee(self):
        for rec in self:
            if rec.employee_id:
                rec.name = "Salary Slip-" + rec.employee_id.name + "-" + str(rec.date_from.month) + '-' + str(
                    rec.date_from.year)
            # to get only business days
            # days = np.busday_count(rec.date_from, rec.date_to)
            d1 = date(rec.date_to.year, rec.date_to.month, rec.date_to.day)
            d2 = date(rec.date_from.year, rec.date_from.month, rec.date_from.day)
            delta = (d1 - d2) + timedelta(days=1)
            rec.total_days = delta.days
            domain = [('employee_id', '=', rec.employee_id.id), ('holiday_status_id.is_sick_leave', '=', True),
                      ('state', '=', 'validate')]
            # rec.emp_total_leaves = sum(self.env['hr.leave'].sudo().search(domain).mapped('number_of_days'))
            domain += [('date_from', '>=', rec.date_from), ('date_to', '<=', rec.date_to)]
            rec.emp_month_leaves = sum(self.env['hr.leave'].sudo().search(domain).mapped('number_of_days'))
            rec.paid_leaves = sum(self.env['hr.leave'].sudo().search(
                [('employee_id', '=', rec.employee_id.id), ('state', '=', 'validate'),
                 ('holiday_status_id.pay_type', '=', 'paid'), ('request_date_from', '>=', rec.date_from),
                 ('request_date_to', '<=', rec.date_to)]).mapped('number_of_days'))
            rec.month_annual_leave = sum(self.env['hr.leave'].sudo().search(
                [('employee_id', '=', rec.employee_id.id), ('state', '=', 'validate'),
                 ('holiday_status_id.period_type', '=', 'annual'), ('request_date_from', '>=', rec.date_from),
                 ('request_date_to', '<=', rec.date_to)]).mapped(
                'number_of_days'))
            rec.month_unpaid_leaves = sum(self.env['hr.leave'].sudo().search(
                [('employee_id', '=', rec.employee_id.id),
                 ('state', '=', 'validate') , ('holiday_status_id.pay_type', '=', 'unpaid'),('holiday_status_id.is_unpaid_leave', '=', True),
                 ('request_date_from', '>=', rec.date_from),
                 ('request_date_to', '<=', rec.date_to)
                 ]).mapped(
                'number_of_days'))
            rec.month_unpaid_leaves_half = sum(self.env['hr.leave'].sudo().search(
                [('employee_id', '=', rec.employee_id.id),
                 ('state', '=', 'validate'), ('holiday_status_id.pay_type', '=', 'half_paid'),
                 ('request_date_from', '>=', rec.date_from),
                 ('request_date_to', '<=', rec.date_to)
                 ]).mapped(
                'number_of_days'))


            if rec.month_unpaid_leaves:
                rec.deduct_able_sick_leaves = rec.month_unpaid_leaves
            else:
                rec.deduct_able_sick_leaves = 0
            if rec.month_unpaid_leaves_half:
                rec.half_deductible_leaves = rec.month_unpaid_leaves_half
            else:
                rec.half_deductible_leaves = 0
            if rec.paid_leaves:
                rec.emp_month_leaves = rec.paid_leaves
            else:
                rec.emp_month_leaves = 0


            # if rec.emp_month_leaves:
            #     if rec.emp_total_leaves < 15:
            #         if emp_rm_sk_leaves:
            #             if emp_rm_sk_leaves > rec.emp_month_leaves:
            #                 emp_rm_sk_leaves -= rec.emp_month_leaves
            #             else:
            #                 rec.half_deductible_leaves = rec.emp_month_leaves - emp_rm_sk_leaves
            #         else:
            #             rec.deduct_able_sick_leaves = rec.emp_month_leaves
            #
            #     elif 15 < rec.emp_total_leaves < 45:
            #         # if employee has fully paid sick leave remaining
            #         if emp_rm_sk_leaves:
            #             if emp_rm_sk_leaves < rec.emp_month_leaves:
            #                 rec.half_deductible_leaves = rec.emp_month_leaves - emp_rm_sk_leaves
            #             else:
            #                 emp_rm_sk_leaves -= rec.emp_month_leaves
            #         elif emp_rm_half_sk_leaves:
            #             if rec.emp_month_leaves > emp_rm_half_sk_leaves:
            #                 rec.deduct_able_sick_leaves = rec.emp_month_leaves - emp_rm_half_sk_leaves
            #                 rec.half_deductible_leaves = rec.emp_month_leaves - (
            #                         rec.emp_month_leaves - emp_rm_half_sk_leaves)
            #             else:
            #                 emp_rm_half_sk_leaves -= rec.emp_month_leaves
            #                 rec.half_deductible_leaves = rec.emp_month_leaves
            #         else:
            #             rec.half_deductible_leaves = rec.emp_month_leaves
            #     # if total done leaves are greater than 45
            #     else:
            #         if emp_rm_half_sk_leaves:
            #             if emp_rm_half_sk_leaves > rec.emp_month_leaves:
            #                 emp_rm_half_sk_leaves -= rec.emp_month_leaves
            #             else:
            #                 rec.half_deductible_leaves = rec.emp_month_leaves - emp_rm_half_sk_leaves
            #         else:
            #             rec.deduct_able_sick_leaves = rec.emp_month_leaves
            #
            # else:
            #     rec.half_deductible_leaves = 0
            #     rec.deduct_able_sick_leaves = 0

    # @api.onchange("employee_id", 'date_from', 'date_to', 'work_days_manually')
    # def _get_total_days(self):
    #     for rec in self:
    #         # days = np.busday_count(rec.date_from, rec.date_to)
    #         # rec.total_days = days + 4
    #         d1 = date(rec.date_to.year, rec.date_to.month, rec.date_to.day)
    #         d2 = date(rec.date_from.year, rec.date_from.month, rec.date_from.day)
    #         delta = (d1 - d2) + timedelta(days=1)
    #
    #         rec.total_days = delta.days
    #         att = self.env['employee.attendance'].search([('employee_id', '=', rec.employee_id.id),
    #                                                       ('date_from', '>=', rec.date_from),
    #                                                       ('date_to', '<=', rec.date_to)], limit=1)
    #
    #         hours = rec.employee_id.resource_calendar_id.work_period
    #         wage = rec.contract_id.wage / 30 / hours if hours else 0
    #
    #         leaves = rec.emp_month_leaves + rec.month_annual_leave + rec.month_unpaid_leaves + int(
    #             rec.month_absence) + rec.compassionate_leaves + rec.parental_leaves + rec.maternity_leaves
    #         + rec.maternity_leaves_half
    #
    #     comp_mach_attend = self.env['ir.config_parameter'].sudo().get_param(
    #         'hr_modification.compare_attendance_with_machine')
    #
    #     if rec.worked_days_line_ids:
    #         if comp_mach_attend and not rec.employee_id.is_senior:
    #             work_days = rec.total_days - leaves
    #         else:
    #             payslip_dates = self._get_payslip_dates_list(rec.date_from, rec.date_to)
    #             leaves_dates_list = self._get_leaves_dates_list(rec.employee_id, rec.date_from, rec.date_to)
    #             work_days = 0
    #             leaves = 0
    #             if not len(leaves_dates_list) == rec.total_days:
    #                 work_days = len(set(payslip_dates) - set(leaves_dates_list)) - rec.total_days // 7
    #                 leaves = len(leaves_dates_list) + rec.total_days // 7
    #             else:
    #                 work_days = len(set(payslip_dates) - set(leaves_dates_list))
    #                 leaves = len(leaves_dates_list)
    #             if leaves_dates_list and not len(leaves_dates_list) == rec.total_days:
    #                 work_days -= 1
    #                 leaves += 1
    #
    #         rec.worked_days_line_ids = [(1, rec.worked_days_line_ids.id, {
    #             'total_days': rec.total_days,
    #             'total_leaves': leaves,
    #             'number_of_days': work_days,
    #             # 'number_of_hours': work_days * hours,
    #             'number_of_hours': rec.attendance_total_hours,
    #             'work_entry_type_id': 1,
    #         })]
    #     else:
    #         if comp_mach_attend and not rec.employee_id.is_senior:
    #             work_days = rec.total_days - leaves
    #         else:
    #             payslip_dates = self._get_payslip_dates_list(rec.date_from, rec.date_to)
    #             leaves_dates_list = self._get_leaves_dates_list(rec.employee_id, rec.date_from, rec.date_to)
    #             work_days = 0
    #             leaves = 0
    #             if not len(leaves_dates_list) == rec.total_days:
    #                 work_days = len(set(payslip_dates) - set(leaves_dates_list)) - rec.total_days // 7
    #                 leaves = len(leaves_dates_list) + rec.total_days // 7
    #             else:
    #                 leaves = len(leaves_dates_list)
    #                 work_days = len(set(payslip_dates) - set(leaves_dates_list))
    #
    #             if leaves_dates_list and not len(leaves_dates_list) == rec.total_days:
    #                 work_days -= 1
    #                 leaves += 1
    #
    #         rec.worked_days_line_ids = [(0, 0, {'total_days': rec.total_days,
    #                                             'total_leaves': leaves,
    #                                             'number_of_days': work_days,
    #                                             'number_of_hours': rec.attendance_total_hours,
    #                                             # 'number_of_hours': work_days * hours,
    #                                             'work_entry_type_id': 1,
    #                                             })]
    
    def compute_sheet(self):
        for rec in self:
            rec._onchange_employee()
        return super(InheritHrPayslip   , self).compute_sheet()

class InheritHrEmployee(models.Model):
    _inherit = 'hr.employee'

    allocation_from_date = fields.Date("Allocation From Date", compute="_get_sick_leave_allocation_dates")
    allocation_to_date = fields.Date("Allocation To Date", compute="_get_sick_leave_allocation_dates")
    full_paid_allowed = fields.Integer("Fully Paid sick Leave Allowed")
    half_paid_allowed = fields.Integer("Half Paid sick Leave Allowed Up To")
    fully_paid_rmng_sick_lve = fields.Integer("Fully Paid Remaining Sick Leave", compute="_get_remaining_days")
    half_paid_rmng_sick_lve = fields.Integer("Half Paid Remaining Sick Leave", compute="_get_remaining_days")
    # hidden_check2 = fields.Boolean("Hidden Check 2", compute="_get_allowed_days")
    hidden_check = fields.Boolean("Hidden Check")
    is_senior = fields.Boolean("Is Senior")

    def _get_sick_leave_allocation_dates(self):
        for rec in self:
            current_year = datetime.today().year
            next_year = current_year + 1
            if current_year == 2023:
                previous_year = current_year - 1
                date_from = date(previous_year, 12, 1)
            else:
                date_from = date(current_year, 1, 16)
            date_to = date(next_year, 1, 15)
            rec.allocation_from_date = date_from
            rec.allocation_to_date = date_to

    # @api.depends('hidden_check2', 'joining_date')
    # def _get_allowed_days(self):
    #     for rec in self:
    #         rec.hidden_check2 = True
    #         emp_leave_allocation = rec.env['hr.leave.allocation'].search([
    #             ('employee_id', '=', rec.id),
    #             ('state', '=', 'validate'),
    #             ('date_from', '=', rec.allocation_from_date),
    #             ('date_to', '=', rec.allocation_to_date),
    #             ('number_of_days_display', '>=', 45.0),
    #             ('holiday_status_id.is_sick_leave', '=', True)
    #         ])
    #         if rec.has_completed_probation(rec) and not emp_leave_allocation and rec.contract_id.state == 'open':
    #             rec.assign_yearly_sick_leave(rec)
    #
    #         elif emp_leave_allocation and self.has_completed_probation(rec) and rec.contract_id.state == 'open':
    #             rec.full_paid_allowed = 15
    #             rec.half_paid_allowed = 45
    #         else:
    #             rec.full_paid_allowed = 0
    #             rec.half_paid_allowed = 0
    #         rec.hidden_check2 = True

    # def assign_yearly_sick_leave(self, employee=None):
    #     try:
    #         type_sick_leave = self.env['hr.leave.type'].search([('is_sick_leave', '=', True)], limit=1)
    #         allocation_done = self.env['hr.leave.allocation'].create({
    #             'employee_id': employee.id,
    #             'date_from': employee.allocation_from_date,
    #             'date_to': employee.allocation_to_date,
    #             'number_of_days_display': 90,
    #             'holiday_status_id': type_sick_leave.id if type_sick_leave else None
    #         })
    #         allocation_done.action_validate()
    #         if allocation_done:
    #             employee.full_paid_allowed = 15
    #             employee.half_paid_allowed = 30
    #         else:
    #             employee.full_paid_allowed = 0
    #             employee.half_paid_allowed = 0
    #     except Exception as e:
    #         raise UserError(_("Kindly Extend the Sick Time off To the next Year Or Check If There is "
    #                           "Any Leave Type Sick Leave with Is Sick Leave Mark As True"))

    def has_completed_probation(self, employee=None):
        today = datetime.today()
        hire_date = fields.Datetime.from_string(employee.joining_date)
        if hire_date:
            return (today - hire_date) >= timedelta(days=183)
        else:
            return False

    @api.depends('joining_date')
    def _get_remaining_days(self):
        for rec in self:
            if rec.id:
                rec.hidden_check = True
                total_leaves = sum(
                    self.env['hr.payslip'].search(
                        [('employee_id.id', '=', rec.id), ('state', '=', 'done'),
                         ('date_from', '>=', rec.allocation_from_date),
                         ('date_to', '<=', rec.allocation_to_date)]).mapped(
                        'emp_month_leaves'))
                if rec.full_paid_allowed or rec.half_paid_allowed:
                    if total_leaves > 15:
                        rec.fully_paid_rmng_sick_lve = 0
                    else:
                        rec.fully_paid_rmng_sick_lve = rec.full_paid_allowed - total_leaves
                    if 15 < total_leaves < 45:
                        rec.half_paid_rmng_sick_lve = rec.half_paid_allowed - total_leaves
                    else:
                        rec.half_paid_rmng_sick_lve = 0
                else:
                    rec.fully_paid_rmng_sick_lve = 0
                    rec.half_paid_rmng_sick_lve = 0
            else:
                rec.fully_paid_rmng_sick_lve = 0
                rec.half_paid_rmng_sick_lve = 0
                rec.hidden_check = False


class InheritLeaveType(models.Model):
    _inherit = "hr.leave.type"

    is_unpaid_leave = fields.Boolean("Unpaid Leave", default=False)
    is_annual_leave = fields.Boolean("Annual Leave", default=False)
