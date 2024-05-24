# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import timedelta


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    zk_check_in_end_datetime = fields.Datetime(
        string="Check-In End (Date & Time)")
    zk_punch_line = fields.One2many('zk.punch.line', 'attendance_id', string='Punches', readonly=1)



class ZkPunchLine(models.Model):
    _name = "zk.punch.line"
    _description = "Attendance"
    _rec_name = 'attendance_id'

    attendance_id = fields.Many2one(
        'hr.attendance', string="Attendance Reference", index=True,
        required=True, ondelete='cascade'
    )
    company_name = fields.Char(string='CompanyName', required=1)
    badge_number = fields.Char(string='BadgeNumber', required=1)
    punch_date_time = fields.Datetime(string='PunchDateTime')
    punch_type = fields.Char(string='PunchType')
    punch_type_selection = fields.Selection([
        ('check_in', 'Check-In'),
        ('check_out', 'Check-Out')
    ], string="Check-In/Out")
    device_Id = fields.Char(string='DeviceId')
