# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import date


class HolidaysAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    is_applicable_one_time = fields.Boolean("Is Applicable One Time")
    state = fields.Selection(selection_add=[('expired', 'Expired')])

    @api.onchange('holiday_status_id')
    def _onchange_holiday_status_id(self):
        if self.holiday_status_id:
            if self.holiday_status_id.is_applicable_one_time:
                self.is_applicable_one_time = True

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            leave_allocation_id = self.env['hr.leave.allocation'].search([('is_applicable_one_time', '=', True),
                                                                          ('state', '=', 'validate'),
                                                                          ('holiday_status_id', '=',
                                                                           vals.get('holiday_status_id'))])
            if len(leave_allocation_id) > 1:
                raise UserError(
                    _("Sorry, You are not eligible To Request for this Leave Type. Please Contact Your Administrator"))
        return super(HolidaysAllocation, self).create(vals_list)

    def leave_allocation_expiry(self):
        for allocation in self.search([]):
            if allocation.date_to:
                if allocation.state == 'validate' and fields.Date.today() > allocation.date_to:
                    allocation.state = 'expired'

    def auto_leave_allocation(self):
        employees = self.env['hr.employee'].search([])
        leave_types = self.env['hr.leave.type'].search([])
        for employee in employees:
            for leave_type in leave_types:
                if leave_type.autogenerate_time_off_allocation:
                    leave_allocation = self.search(
                        [('state', '=', 'validate'), ('holiday_status_id', '=', leave_type.id),
                         ('employee_id', '=', employee.id)])
                    if not leave_allocation:
                        today = date.today()
                        joining_date = employee.joining_date
                        days_from_joining_date = (today - joining_date).days
                        allowed_no_of_days = 0
                        for rule in leave_type.leave_type_rule_ids:
                            if rule.from_days <= days_from_joining_date <= rule.to_days:
                                allowed_no_of_days = rule.total_leaves
                        name = 'Allocation For ' + leave_type.name
                        if allowed_no_of_days > 0:
                            allocation = self.create({
                                'name': name,
                                'holiday_status_id': leave_type.id,
                                'holiday_type': 'employee',
                                'employee_id': employee.id,
                                'number_of_days_display': allowed_no_of_days,
                                'number_of_days': allowed_no_of_days,
                            })


                    if leave_allocation and leave_type.carry_forward:
                        today = date.today()
                        joining_date = employee.joining_date
                        days_from_joining_date = (today - joining_date).days
                        if days_from_joining_date > 364:
                            allowed_no_of_days = 0
                            for rule in leave_type.leave_type_rule_ids:
                                if rule.from_days <= days_from_joining_date <= rule.to_days:
                                    allowed_no_of_days = rule.total_leaves
                            name = 'Allocation For ' + leave_type.name
                            remaining_leaves = leave_allocation.number_of_days_display - leave_allocation.leaves_taken
                            allowed_no_of_days = remaining_leaves + allowed_no_of_days
                            if allowed_no_of_days > 0:
                                allocation = self.create({
                                    'name': name,
                                    'holiday_status_id': leave_type.id,
                                    'holiday_type': 'employee',
                                    'employee_id': employee.id,
                                    'number_of_days_display': allowed_no_of_days,
                                    'number_of_days': allowed_no_of_days,
                                })
