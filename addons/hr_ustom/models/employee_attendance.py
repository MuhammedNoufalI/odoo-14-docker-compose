# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import time
from pytz import timezone
from odoo import api, fields, models, _
from odoo import SUPERUSER_ID
import pytz
import pandas as pd
import logging
_logger = logging.getLogger(__name__)
class EmpAttendanceDetails(models.Model):
    _name = 'employee.attendance'
    _rec_name = 'employee_id'
    employee_id = fields.Many2one('hr.employee',string='Employee')
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    employee_attendance_line = fields.One2many(comodel_name="employee.attendance.lines", inverse_name="emp_attendance_line_id", string="", required=False, )
    employee_absent_line = fields.One2many(comodel_name="employee.absent.lines", inverse_name="emp_attendance_line_id", string="", required=False, )
    total_late = fields.Float(strinbg='Late',compute='compute_totals',store=True)
    total_early = fields.Float(strinbg='Early',compute='compute_totals',store=True)
    total_overtime = fields.Float(strinbg='Overtime',compute='compute_totals',store=True)
    deduction = fields.Float(string='Deduction',compute='compute_deduction',inverse="_inverse_deduction",store=True)
    total_absent = fields.Integer(string='Absent',compute='compute_total_absent',store=True)
    @api.depends('employee_attendance_line','employee_attendance_line.late','employee_attendance_line.early','employee_attendance_line.over_time')
    def compute_totals(self):
        for rec in self:
            rec.total_late = sum(rec.employee_attendance_line.mapped('late'))
            rec.total_early = sum(rec.employee_attendance_line.mapped('early'))
            rec.total_overtime = sum(rec.employee_attendance_line.mapped('over_time'))
    @api.depends('employee_absent_line')
    def compute_total_absent(self):
        for rec in self:
            rec.total_absent = len(rec.employee_absent_line)


    def _inverse_deduction(self):
        pass
    @api.depends('employee_absent_line')
    def compute_deduction(self):
        count = 0
        total = 0
        for att in self:
            deductions = self.env['hr.attendance.deduction'].search([('type', '=', 'absent')],order='absent_repeat desc')
            for rec in att.employee_absent_line:
                count +=1
                # res = self.env['hr.attendance.deduction'].search([('type','=','absent'),('absent_repeat','<=',count)],order='absent_repeat desc' , limit=1)
                for ded in deductions:
                    if int(ded.absent_repeat) <= count:
                        total += ded.deduction
                        break
            att.deduction = total
    def is_public_holiday(self,date,resource_calendar_id):
        return any (x.date_from <= date and date <= x.date_to for x in resource_calendar_id.public_holiday_ids)
    def is_leave_request(self,date):
        holidays = self.env['hr.leave'].sudo().search([
            ('employee_id', '=', self.employee_id.id),
            ('date_from', '<=', fields.Datetime.now()),
            ('date_to', '>=', fields.Datetime.now()),
            ('state', 'not in', ('cancel', 'refuse'))
        ])
        return any (x.date_from <= date and date <= x.date_to for x in self.employee_id.resource_calendar_id.public_holiday_ids)
    def check_has_leave(self,check_in):
        res = self.env['hr.leave'].search([
            ('employee_id', '=', self.employee_id.id),
            ('state', '=', 'validate'),
            ('date_from', '<=', check_in),
            ('date_to', '>=', check_in),
        ])
        return res
    def get_work_to(self, date_out, working_hours_id):
        hour = 0.0
        if type(date_out) is datetime:
            working_hours = working_hours_id
            for line in working_hours.custom_attendance_ids:
                if int(line.shift_end_day) == date_out.weekday():
                    hour = line.hour_to
        return hour
    def _compute_early(self,earl):
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        early = 0.0
        over_time = 0.00
        if earl.check_in:
            check_in_date = datetime.strptime(str(earl.check_in), '%Y-%m-%d %H:%M:%S').date()
        total_time_off = 0.0
        if earl.check_out and earl.check_in and earl.employee_id.resource_calendar_id:
            check_out = self._get_check_time(earl.check_out).replace(tzinfo=None)
            wrok_to = self.get_work_to(check_out, earl.employee_id.resource_calendar_id)
            str_time = str(wrok_to)
            hour = str_time.split('.')[0]
            minte = str_time.split('.')[1]
            if float(minte) < 10 and float(minte) > 1:
                minte = (60 * float(minte) * 10) / 100
            else:
                minte = (60 * float(minte)) / 100
            work_end = datetime(year=check_out.year, month=check_out.month, day=check_out.day, hour=00,
                                minute=00) + timedelta(hours=float(hour), minutes=float(minte))
            work_end = pytz.utc.localize(datetime.strptime(str(work_end), DATETIME_FORMAT)).replace(tzinfo=None)

            over_time = 0.00

            if check_out < work_end:
                if str(check_out.weekday()) in earl.employee_id.resource_calendar_id.custom_attendance_ids.mapped(
                        'shift_end_day'):
                    dif = work_end - check_out
                    early = (float(dif.seconds) / 3600)
                else:
                    early = 0.00
            elif check_out > work_end:
                if str(check_out.weekday()) in earl.employee_id.resource_calendar_id.custom_attendance_ids.mapped(
                        'shift_end_day'):
                    dif2 = check_out - work_end
                    over_time = float(dif2.seconds) / 3600
                else:
                    check_in = self._get_check_time(earl.check_in).replace(tzinfo=None)
                    over_time = float((check_out - check_in).seconds) / 3600

            else:
                early = 0.00
                over_time = 0.00
        return early,over_time
    def get_work_from(self, date_in, working_hours_id):
        hour = 0.0
        if type(date_in) is datetime:
            working_hours = working_hours_id
            for line in working_hours.custom_attendance_ids:
                if int(line.shift_start_day) == date_in.weekday():
                    hour = line.hour_from
        return hour
    def _get_check_time(self, check_date):
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        user_id = self.env['res.users']
        user = user_id.browse(SUPERUSER_ID)
        tz = pytz.timezone((self.env.user.tz or 'UTC'))
        checkdate = pytz.utc.localize(datetime.strptime(str(check_date), DATETIME_FORMAT)).astimezone(tz)
        return checkdate
    def check_leave_of_type_hour(self,work_start):
        res = self.env['hr.leave'].sudo().search([
            ('holiday_status_id.request_unit', '=', 'hour'),
            ('request_unit_hours', '=', True),
            ('employee_id', '=', self.employee_id.id),
            ('date_from', '<=', work_start),
            ('date_to', '>=', work_start),
            ('state', 'not in', ('cancel', 'refuse'))
        ],limit=1)
        if res:
            return  res.date_to
        else:
            return work_start
    def _compute_late(self,lat):
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

        late = 0.0
        if lat.check_in != False:
            check_in_date = datetime.strptime(str(lat.check_in), '%Y-%m-%d %H:%M:%S').date()

        if lat.check_in and lat.employee_id.resource_calendar_id:
            check_in = self._get_check_time(lat.check_in).replace(tzinfo=None)
            # check_in = lat.check_in
            wrok_from = self.get_work_from(check_in, lat.employee_id.resource_calendar_id)
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
            self.check_leave_of_type_hour(work_start)
            if check_in > work_start:
                if str(check_in.weekday()) in lat.employee_id.resource_calendar_id.custom_attendance_ids.mapped(
                        'shift_start_day'):
                    dif = check_in - work_start
                    late = float(dif.seconds) / 3600
                else:
                    late = 0.00
            else:
                late = 0.00
        else:
            late = 0.00
        return late
    def get_custom_resource_calendar_line(self,resource_calendar_id,shift_start_day,shift_end_day):
        line = resource_calendar_id.custom_attendance_ids.filtered(lambda x:x.shift_start_day == shift_start_day and x.shift_end_day == shift_end_day)
        if line:
            line = line[0]
        return line
    def compute_attendance(self):
        attendance_ids = self.env['hr.attendance'].search([('employee_id','=',self.employee_id.id),('check_in','>=',self.date_from),('check_out','<=',self.date_to)],order='check_in')
        attendance_dates = [rec.check_in.date() for rec in attendance_ids]
        custom_attendance_dates = self.employee_id.resource_calendar_id.custom_attendance_ids.mapped('shift_start_day')
        lines = []
        absent_lines = []
        # for attendance in attendance_ids:
        delta =self.date_to-self.date_from  # as timedelta
        days = [self.date_from + timedelta(days=i) for i in range(delta.days + 1)]
        if self.employee_id.is_custom_shift:
            for dr in days:
                attendances = attendance_ids.filtered(lambda x:x.check_in.date() == dr)
                if attendances:
                    late_attendance = attendances[0]
                    early_attendance = attendances[-1]
                    line = self.get_custom_resource_calendar_line(self.employee_id.resource_calendar_id,str(late_attendance.check_in.date().weekday()),str(early_attendance.check_out.date().weekday()))
                    early , over_time = self._compute_early(early_attendance)
                    if line:
                        vals = {
                            'date':late_attendance.check_in.date(),
                            'shift_start_day':line.shift_start_day,
                            'hour_from':line.hour_from,
                            'shift_end_day': line.shift_end_day,
                            'hour_to':line.hour_to,
                            'check_in':late_attendance.check_in,
                            'late':self._compute_late(late_attendance),
                            'early':early,
                            'over_time':over_time,
                            'check_out':early_attendance.check_out,
                            'attendance_ids':[(6, 0, attendances.ids)],
                        }
                        lines.append((0,0,vals))
                    else:
                        if str(late_attendance.check_in.date().weekday()) not in custom_attendance_dates:
                            vals = {
                                'date': late_attendance.check_in.date(),
                                'shift_start_day': str(late_attendance.check_in.date().weekday()),
                                'hour_from': 0,
                                'shift_end_day': str(early_attendance.check_out.date().weekday()),
                                'hour_to':0 ,
                                'check_in': late_attendance.check_in,
                                'late': self._compute_late(late_attendance),
                                'early': 0,
                                'over_time': over_time,
                                'check_out': early_attendance.check_out,
                                'attendance_ids': [(6, 0, attendances.ids)],
                            }
                            lines.append((0, 0, vals))
            for dr in days:
                if not self.check_has_leave(dr) and  not self.is_public_holiday(dr,self.employee_id.resource_calendar_id) and dr not in attendance_dates  and str(dr.weekday()) in self.employee_id.resource_calendar_id.custom_attendance_ids.mapped('shift_start_day'):
                    vals = {'date':dr}
                    absent_lines.append((0,0,vals))
        else:
            for attendance in attendance_ids:
                vals = {
                    'date': attendance.check_in.date(),
                    'shift_start_day': str(attendance.check_in.date().weekday()),
                    'hour_from': attendance.get_work_from(attendance.check_in, attendance.employee_id.resource_calendar_id),
                    'shift_end_day': str(attendance.check_out.date().weekday()),
                    'hour_to': attendance.get_work_to(attendance.check_out, attendance.employee_id.resource_calendar_id),
                    'check_in': attendance.check_in,
                    'late': attendance.late,
                    'early': attendance.early,
                    'over_time': attendance.over_time,
                    'check_out': attendance.check_out,
                    'attendance_ids': [(6, 0, attendance.ids)],
                }
                lines.append((0, 0, vals))
            for dr in days:
                if not self.check_has_leave(dr) and  not self.is_public_holiday(dr,self.employee_id.resource_calendar_id) and dr not in attendance_dates  and str(dr.weekday()) in self.employee_id.resource_calendar_id.attendance_ids.mapped('dayofweek'):
                    vals = {'date':dr}
                    absent_lines.append((0,0,vals))
        self.employee_attendance_line = False
        self.employee_attendance_line = lines
        self.employee_absent_line = False
        self.employee_absent_line = absent_lines

class EmpAttendanceLines(models.Model):
    _name = 'employee.attendance.lines'
    emp_attendance_line_id = fields.Many2one('employee.attendance')
    date = fields.Date('Date')
    shift_start_day = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], 'Day of Week', required=True, index=True, default='0')
    shift_end_day = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], 'Day of Week', required=True, index=True, default='0')
    hour_from = fields.Float()
    hour_to = fields.Float()
    check_in = fields.Datetime('Check In')
    check_out = fields.Datetime('Check Out')
    attendance_ids = fields.Many2many('hr.attendance')
    late = fields.Float(string='Late Check In',) #compute='_compute_late'
    early = fields.Float(string='Early Check Out',) #compute='_compute_early'
    over_time = fields.Float(string='Over Time',) #compute='_compute_early'

    worked_hours = fields.Float(string='Worked Hours', compute='_compute_worked_hours', store=True, readonly=True)

    @api.depends('check_in', 'check_out','attendance_ids')
    def _compute_worked_hours(self):
        for attendance in self:
            if attendance.check_out and attendance.check_in:
                delta = attendance.check_out - attendance.check_in
                attendance.worked_hours =  sum(attendance.attendance_ids.mapped('worked_hours'))
                # attendance.worked_hours = delta.total_seconds() / 3600.0
            else:
                attendance.worked_hours = False
class EmpAbsentLines(models.Model):
    _name = 'employee.absent.lines'
    emp_attendance_line_id = fields.Many2one('employee.attendance')
    date = fields.Date('Date')


