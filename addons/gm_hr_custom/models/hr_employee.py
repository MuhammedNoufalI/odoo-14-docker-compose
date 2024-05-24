# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import  datetime , date

# _____ Model Inherit

class hr_attendance(models.Model):
    _inherit = 'hr.employee'

    attendance_id = fields.Many2one(comodel_name="hr.attendance.structure", related='resource_calendar_id.attendance_id',
                                    string="Attendance Rule", required=False, )
    # attendance_id = fields.Many2one(comodel_name="hr.attendance.structure", related='resource_calendar_id.attendance_id',
    #                                 string="Attendance Rule", required=False, )
    job_nature_allwance_10 = fields.Float(string="Job Nature Allowance 10%")
    taxable_allowance = fields.Float(string="Taxable Allowance")
    transportation_allowance = fields.Float(string="Transportation Allowance")
    social_allowance = fields.Float(string="Social Allowance")
    special_social_allowance = fields.Float(string="Special Social Allowance")
    other_allowance = fields.Float(string="Other Allowance")
    sea_allowance10 = fields.Float(string="Sea Allowance 10%")
    job_nature_allwance_5 = fields.Float(string="Job Nature Allowance 5%")
    time_allwance_15 = fields.Float(string="Time Allowance 15%")
    representation_allwance_20 = fields.Float(string="Representation Allow. 20%")
    sea_allowance5 = fields.Float(string="Sea Allowance 5%")
    time_allwance_25 = fields.Float(string="Time Allowance 25%")
    representation_allwance_30 = fields.Float(string="Representation Allow. 30%")
    representation_allwance_15 = fields.Float(string="Representation Allow. 15%")
    representation_allwance_10 = fields.Float(string="Representation Allow. 10%")
    grade_allowance = fields.Float(string="Grade Allowance")
    correction = fields.Float(string="Correction")
    add_rewards = fields.Float(string="Rewards")
    add_profit = fields.Float(string="Profits")
    add_bonus = fields.Float(string="Bonus")
    is_absent = fields.Boolean('Absent Today', compute='_compute_leave_status', search='_search_absent_employee',store=True)

    def _search_absent_employee(self, operator, value):
        holidays = self.env['hr.leave'].sudo().search([
            ('employee_id', '!=', False),
            ('state', 'not in', ['cancel', 'refuse']),
            ('date_from', '<=', datetime.datetime.utcnow()),
            ('date_to', '>=', datetime.datetime.utcnow())
        ])
        return [('id', 'in', holidays.mapped('employee_id').ids)]


    @api.model
    def _compute_leave_status(self):
        # Used SUPERUSER_ID to forcefully get status of other user's leave, to bypass record rule
        holidays = self.env['hr.leave'].sudo().search([
            ('employee_id', 'in', self.ids),
            ('date_from', '<=', fields.Datetime.now()),
            ('date_to', '>=', fields.Datetime.now()),
            ('state', 'not in', ('cancel', 'refuse'))
        ])
        leave_data = {}
        for holiday in holidays:
            leave_data[holiday.employee_id.id] = {}
            leave_data[holiday.employee_id.id]['leave_date_from'] = holiday.date_from.date()
            leave_data[holiday.employee_id.id]['leave_date_to'] = holiday.date_to.date()
            leave_data[holiday.employee_id.id]['current_leave_state'] = holiday.state
            leave_data[holiday.employee_id.id]['current_leave_id'] = holiday.holiday_status_id.id

        for employee in self:
            employee.leave_date_from = leave_data.get(employee.id, {}).get('leave_date_from')
            employee.leave_date_to = leave_data.get(employee.id, {}).get('leave_date_to')
            employee.current_leave_state = leave_data.get(employee.id, {}).get('current_leave_state')
            employee.current_leave_id = leave_data.get(employee.id, {}).get('current_leave_id')
            employee.is_absent = leave_data.get(employee.id) and leave_data.get(employee.id, {}).get('current_leave_state') not in ['cancel', 'refuse', 'draft']


