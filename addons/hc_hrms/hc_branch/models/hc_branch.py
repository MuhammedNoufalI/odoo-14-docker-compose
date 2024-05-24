# -*- coding: utf-8 -*-

from odoo import fields, models
from odoo.exceptions import UserError


class HcBranch(models.Model):
    _name = 'hc.branch'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    _description = 'Branches'

    name = fields.Char(string="Name")
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 copy=False, default=lambda self: self.env['res.company']._company_default_get())
    code = fields.Char(string="Code")
    email = fields.Char(string="Email")
    working_schedule_ids = fields.Many2many('resource.calendar', string="Applicable Working Schedule",
                                            help="Create Multiple Working Times Applicable for the Branch (Menu is Available in the Configuration) ")
    latitude = fields.Char(string="Latitude")
    longitude = fields.Char(string="Longitude")
    attendance_device_ids = fields.One2many('hc.attendance.device', 'branch_id', string="Device Ids")

    # Attendace Policies
    allowed_late_time = fields.Float(string="Allowed Late Time", help="Late By Given Time, Considered to Be Full Day",
                                     tracking=True)
    allowed_checkin_from = fields.Float(string="Allowed Checkin From",
                                        help="From the Given 'Checkin From' Time Between 'Checkin To' Time, Complete Attendance Can Be given.",
                                        tracking=True)
    allowed_checkin_to = fields.Float(string="Allowed Checkin To", tracking=True,
                                      help="From the Given 'Checkin To' Time Between 'Checkin From' Time, Complete Attendance Can Be given.")
    allowed_missed_punch_count = fields.Integer(string="Allowed Missed Punch", tracking=True,
                                                help="As the Comapny Policy, Days Given will be treated as full day present for tje Missed Punch in a month")
    total_hours_absence_limit = fields.Float(string="Total Hours Absence Limit", tracking=True,
                                             help="Total Hours of absence accumulated can be upto Given Days per month in one year")
    late_checkin_for_approval = fields.Float(string="Late Checkin Approval ", tracking=True,
                                             help="Late check-in Need to be approved with a proof or reason")
    is_special_approval = fields.Boolean(string="Special Approval Available", tracking=True)
    flexible_break_time_limit = fields.Float("Allowed Flexible Break Time Per Day")
    is_weekend_special_pay = fields.Boolean('Weekend Special Pay Eligible')
    max_weekends_eligible = fields.Integer('Max No of Weekends Eligible')
    amount = fields.Float('Amount')
    key_holder_ids = fields.One2many('hc.key.holder', 'branch_id', string="Key Holder Ids")
    kh_allowed_late = fields.Float(string='Key Holder Allowed Late Punch/Month', help="Allowed Late Punch Per Month")
    kh_max_warning = fields.Float(string='Key Holder Warning Count',
                                  help="Maximum No of Written Warning for the KeyHolder for late punch in an Year")
    penalty = fields.Float(string="Penalty Amount", help="Penalty Amount if there any in case of Late punch")

    # branch address

    street = fields.Char('Street')
    street2 = fields.Char('Street2')
    zip_code = fields.Char('Zip')
    city = fields.Char('City')
    state_id = fields.Many2one(
        "res.country.state", string='State', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one(
        'res.country', string='Country')
    phone = fields.Char('Phone')

    # Deduction Policies

    def action_branch_navigate_location(self):
        if not self.latitude and not self.longitude:
            raise UserError("Please Add Branch Latitude and Longitude")
        url = "https://www.google.com/maps/dir/?api=1&destination=%s,%s" % (self.latitude, self.longitude)
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new'
        }


class HcAttendanceDevice(models.Model):
    _name = 'hc.attendance.device'
    _description = 'Hc Attendance device'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name")
    device_id = fields.Char('Device ID', copy=False)
    branch_id = fields.Many2one('hc.branch', string="Branch Id")

    # _sql_constraints = [('device_id', 'unique(device_id)', 'Device ID Must Be Unique!')]
