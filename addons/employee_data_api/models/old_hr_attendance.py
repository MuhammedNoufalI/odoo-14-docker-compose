# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import timedelta


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    zk_check_in_end_datetime = fields.Datetime(
        string="Check-In End (Date & Time)", compute='_zk_check_in_end_datetime', store=True
    )
    zk_punch_line = fields.One2many('zk.punch.line', 'attendance_id', string='Punches', readonly=1)

    @api.depends('check_in')
    def _zk_check_in_end_datetime(self):
        for rec in self:
            check_in = rec.check_in
            if check_in:
                rec.zk_check_in_end_datetime = check_in + timedelta(days=1)
            else:
                rec.zk_check_in_end_datetime = False


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
    ], string="Check-In/Out", compute='_compute_punch_type_selection')
    device_Id = fields.Char(string='DeviceId')

    def _compute_punch_type_selection(self):
        for punch in self:
            if punch.punch_type == "0":
                punch.punch_type_selection = 'check_in'
            elif punch.punch_type == "1":
                punch.punch_type_selection = 'check_out'
            else:
                punch.punch_type_selection = False
