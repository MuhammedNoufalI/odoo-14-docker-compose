# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import time
from pytz import timezone
from odoo import api, fields, models, _
from odoo import SUPERUSER_ID
import pytz
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta



# ________________________________________________ Model Inherit

class hr_attendance(models.Model):
    _inherit = 'hr.attendance'

    late = fields.Float(string='Late Check In', compute='_compute_late', )
    early = fields.Float(string='Early Check Out', compute='_compute_early', )
    over_time = fields.Float(string='Over Time', compute='_compute_early', )
    # over_time_amount = fields.Float(string='Over Time Amount', compute='_compute_over_time', store=True)
    # over_time_hour = fields.Float(string='Over Time Hour', compute='_compute_over_time', store=True)
    approval_one = fields.Boolean(string="Direct Manager Approval", default=False)
    approval_sec = fields.Boolean(string="HR Manager Approval", default=False)

    repeate_late = fields.Integer(string="Repeate Late", required=False, compute='get_repeate_late')
    repeate_early = fields.Integer(string="Repeate early", required=False, compute='get_repeate_early')

    @api.depends('check_in', 'late')
    def get_repeate_late(self):
        for att in self:
            repeate_num_prev = 0
            att.repeate_late = 0
            for rec in self.env['hr.attendance'].search(
                    [('employee_id', '=', att.employee_id.id), ('check_in', '<', att.check_in)]):
                if rec.id != att.id and rec.late > 0:
                    check_in_date = datetime.strptime(str(rec.check_in), '%Y-%m-%d %H:%M:%S').date()
                    current_check_in = datetime.strptime(str(att.check_in), '%Y-%m-%d %H:%M:%S').date()
                    if check_in_date < current_check_in and check_in_date.year == current_check_in.year and check_in_date.month == current_check_in.month:
                        repeate_num_prev += 1
            if att.late > 0:
                att.repeate_late = repeate_num_prev + 1
            else:
                att.repeate_late = 0

    @api.depends('check_out', 'early')
    def get_repeate_early(self):
        for att in self:
            att.repeate_early = 0
            repeate_num_prev = 0
            for rec in self.env['hr.attendance'].search(
                    [('employee_id', '=', att.employee_id.id), ('check_out', '<', att.check_out)]):
                print (rec.check_out, 'lllllllllllll')
                if rec.id != att.id and rec.early > 0:
                    check_out_date = datetime.strptime(str(rec.check_out), '%Y-%m-%d %H:%M:%S').date()
                    current_check_out = datetime.strptime(str(att.check_out), '%Y-%m-%d %H:%M:%S').date()
                    if check_out_date < current_check_out and check_out_date.year == current_check_out.year and current_check_out.month == current_check_out.month:
                        repeate_num_prev += 1
            if att.early > 0:
                att.repeate_early = repeate_num_prev + 1
            else:
                att.repeate_early = 0

    def get_time_from_float(self, float_time):
        str_time = str(float_time)
        str_hour = str_time.split('.')[0]
        str_minute = ("%2d" % int(str(float("0." + str_time.split('.')[1]) * 60).split('.')[0])).replace(' ', '0')
        minute = (float(str_hour) * 60) + float(str_minute)
        return minute

    # def _get_check_time(self, check_date):
    #     user_id = self.env['res.users']
    #     DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    #     user = user_id.browse(SUPERUSER_ID)
    #     # tz = pytz.timezone(user.partner_id.tz) or pytz.utc
    #     tz = pytz.utc
    #     checkdate = pytz.utc.localize(
    #         datetime.strptime(check_date, DATETIME_FORMAT)).astimezone(tz)
    #     return checkdate
    def _get_check_time(self, check_date):
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        user_id = self.env['res.users']
        user = user_id.browse(SUPERUSER_ID)
        tz = pytz.timezone((self.env.user.tz or 'UTC'))
        checkdate = pytz.utc.localize(datetime.strptime(str(check_date), DATETIME_FORMAT)).astimezone(tz)
        return checkdate

    def get_work_from(self, date_in, working_hours_id):
        hour = 0.0
        if type(date_in) is datetime:
            working_hours = working_hours_id
            for line in working_hours.attendance_ids:
                if int(line.dayofweek) == date_in.weekday():
                    hour = line.hour_from
        return hour

    def get_work_to(self, date_out, working_hours_id):
        hour = 0.0
        if type(date_out) is datetime:
            working_hours = working_hours_id
            for line in working_hours.attendance_ids:
                if int(line.dayofweek) == date_out.weekday():
                    hour = line.hour_to
        return hour

    @api.depends('check_in')
    def _compute_late(self):
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        for lat in self:
            lat.late = 0.0
            if lat.check_in != False:
                check_in_date = datetime.strptime(str(lat.check_in), '%Y-%m-%d %H:%M:%S').date()

            if lat.check_in and lat.employee_id.resource_calendar_id:
                check_in = lat._get_check_time(lat.check_in).replace(tzinfo=None)
                wrok_from = lat.get_work_from(check_in, lat.employee_id.resource_calendar_id)
                str_time = str(wrok_from)
                hour = str_time.split('.')[0]
                minte = str_time.split('.')[1]
                if float(minte) < 10 and float(minte) > 1:
                    minte = (60 * float(minte) * 10) / 100
                else:
                    minte = (60 * float(minte)) / 100

                work_start = datetime(year=check_in.year, month=check_in.month, day=check_in.day, hour=00,
                                      minute=00) + timedelta(hours=float(hour), minutes=float(minte))
                work_start = pytz.utc.localize(datetime.strptime(str(work_start), DATETIME_FORMAT)).replace(tzinfo=None)

                if check_in > work_start:
                    if str(check_in.weekday()) in lat.employee_id.resource_calendar_id.attendance_ids.mapped(
                            'dayofweek'):
                        dif = check_in - work_start
                        lat.late = float(dif.seconds) / 3600
                    else:
                        lat.late = 0.00
                else:
                    lat.late = 0.00
            else:
                lat.late = 0.00

    @api.depends('check_out')
    def _compute_early(self):
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

        for earl in self:
            earl.early = 0.0
            earl.over_time = 0.00
            if earl.check_in:
                check_in_date = datetime.strptime(str(earl.check_in), '%Y-%m-%d %H:%M:%S').date()
            total_time_off = 0.0
            if earl.check_out and earl.check_in and earl.employee_id.resource_calendar_id:
                check_out = earl._get_check_time(earl.check_out).replace(tzinfo=None)
                wrok_to = earl.get_work_to(check_out, earl.employee_id.resource_calendar_id)
                # self.work_end = wrok_to
                str_time = str(round(wrok_to,2))
                hour = str_time.split('.')[0]
                minte = str_time.split('.')[1]
                if float(minte) < 10 and float(minte) > 1:
                    minte = (60 * float(minte) * 10) / 100
                else:
                    minte = (60 * float(minte)) / 100
                work_end = datetime(year=check_out.year, month=check_out.month, day=check_out.day, hour=00,
                                    minute=00) + timedelta(hours=float(hour), minutes=float(minte))
                work_end = pytz.utc.localize(datetime.strptime(str(work_end), DATETIME_FORMAT)).replace(tzinfo=None)

                earl.over_time = 0.00

                if check_out < work_end:
                    if str(check_out.weekday()) in earl.employee_id.resource_calendar_id.attendance_ids.mapped(
                            'dayofweek'):
                        dif = work_end - check_out
                        earl.early = (float(dif.seconds) / 3600)
                    else:
                        earl.early = 0.00
                elif check_out > work_end:
                    if str(check_out.weekday()) in earl.employee_id.resource_calendar_id.attendance_ids.mapped(
                            'dayofweek'):
                        dif2 = check_out - work_end
                        earl.over_time = float(dif2.seconds) / 3600
                    else:
                        check_in = earl._get_check_time(earl.check_in).replace(tzinfo=None)
                        earl.over_time = float((check_out - check_in).seconds) / 3600

                else:
                    earl.early = 0.00
                    earl.over_time = 0.00
