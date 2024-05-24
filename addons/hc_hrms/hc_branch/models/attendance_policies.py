# -*- coding: utf-8 -*-

from odoo import fields, models


class HcAttendancePolicies(models.Model):
    _name = 'hc.attendance.policy'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    _description = 'Hc Attendance Policies'

    name = fields.Char(string="Name")
    allowed_late_time = fields.Float(string="Allowed Late Time", help="Late By Given Time, Considered to Be Full Day")
    allowed_checkin_from = fields.Float(string="Allowed Checkin From")
    allowed_checkin_to = fields.Float(string="Allowed Checkin To")
    allowed_missed_punch_count = fields.Integer(string="Allowed Missed Punch",
                                        help="As the Comapny Policy, Days Given will be treated as full day present for each month")
    total_hours_absence_limit = fields.Float(string="Total Hours of absence accumulated can be upto Given Days per month in one year")
    late_checkin_for_approval = fields.Float(string="Late Checkin Approval ", help="Late check-in Need to be approved with a proof or reason")
    branch_id = fields.Many2one('hc.branch', string="Branch Id")
