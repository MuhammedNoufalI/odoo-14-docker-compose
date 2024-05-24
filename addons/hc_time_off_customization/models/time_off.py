# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError


class HcTimeOff(models.Model):
    _inherit = "hr.leave"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            employee = vals.get('employee_id', False)
            leave_type = vals.get('holiday_status_id', False)
            allocation = vals.get('holiday_allocation_id', False)
            if employee:
                employee_id = self.env['hr.employee'].search([('id', '=', employee)])
                leave_type_id = self.env['hr.leave.type'].search([('id', '=', leave_type)]) if leave_type else False
                if not employee_id.joining_date:
                    raise UserError(
                        _("Please Set the Joining Date for the Employee"))
                eligible_date = employee_id.joining_date + relativedelta(months=6)
                if leave_type_id.is_applicable and not fields.Date.today() >= eligible_date:
                    raise UserError(
                        _("Sorry, You are not eligible To Request for this Leave Type. Please Contact Your Administrator"))
                if leave_type_id.is_gender_based:
                    if employee_id.gender != leave_type_id.gender:
                        raise UserError(
                            _("Sorry, You are not eligible To Request for this Leave Type. Please Contact Your Administrator"))
                if leave_type_id.parent_time_off_type_id:
                    leave_allocation_id = self.env['hr.leave.allocation'].search([('state', '=', 'validate'),
                                                                                  ('holiday_status_id', '=',
                                                                                   leave_type_id.parent_time_off_type_id.id),
                                                                                  ('employee_id', '=', employee)])
                    total_allocated_days = 0.0
                    leaves = 0.0
                    for allocation in leave_allocation_id:
                        total_allocated_days += allocation.number_of_days_display
                        leaves += allocation.leaves_taken
                    remaining_days = total_allocated_days - leaves
                    if not remaining_days <= 0.0 or 0:
                        raise UserError(
                            _("Sorry, You are not Eligible for the selected Type, Please Chose the Following Type - %s") % (
                                leave_type_id.parent_time_off_type_id.name))
            res = super(HcTimeOff, self).create(vals)
            return res


class HcTimeOffType(models.Model):
    _inherit = "hr.leave.type"

    parent_time_off_type_id = fields.Many2one('hr.leave.type', string="Parent Time Off Type")
    is_gender_based = fields.Boolean('Is Gender Based')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ('other', 'Others')])
    is_applicable = fields.Boolean(string='Is Applicable', help="Time Off Applicable Only After 6 Months From the Employees Joining Date")
    include_to_net_working = fields.Boolean(string="Include to Net Working Days", help='Include to the Net Working Days of the Employee')
    is_applicable_one_time = fields.Boolean(string='Is Applicable Only One Time')
    is_shift_weekday_leave = fields.Boolean(string="Weekday Leave", help="This is the Time Off Type Which can be allocated for the Retails Employee's Allowed Leaved in the Week")
    is_compensatory_timeoff_type = fields.Boolean(string="Is Compensatory")
    # prev_al_start_date = fields.Date(string="Previous AL Start Date", help="Start Date of the Last Annual Leave")
    autogenerate_time_off_allocation = fields.Boolean(string='Autogenerate Time Off Allocation')
    carry_forward = fields.Boolean(string='Carry Forward')
    leave_type_rule_ids = fields.One2many('hr.leave.type.rule', 'leave_type_id', string="Rules")


class HrTimeOffTypeRule(models.Model):
    _name = "hr.leave.type.rule"
    _description = "Hr Time Off Type Rule"

    from_days = fields.Integer(string='From')
    to_days = fields.Integer(string='To')
    total_leaves = fields.Integer(string='Total Leaves')
    is_initial_year = fields.Boolean(string='Initial Year')
    leave_type_id = fields.Many2one('hr.leave.type', string="Leave Type")


