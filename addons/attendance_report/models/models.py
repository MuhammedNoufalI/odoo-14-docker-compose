# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta
from pytz import timezone
import pytz
from datetime import date, timedelta
import copy


class attendance_report(models.Model):
    _inherit = 'hr.attendance'

    checkin_date = fields.Date("check in date", compute="_compute_date", store=True)
    checkout_date = fields.Date("check in date", compute="_compute_date", store=True)

    @api.depends('check_in', 'check_out')
    def _compute_date(self):
        for rec in self:
            if rec.check_in:
                rec.checkin_date = rec.check_in.date()
            else:
                rec.checkin_date = False
        for rec1 in self:
            if rec1.check_out:
                rec1.checkout_date = rec1.check_out.date()
            else:
                rec1.checkout_date = False


class AttendanceReport(models.TransientModel):
    _name = 'attendance.report'
    _description = "Attendance Report Wizard"

    payroll_period = fields.Many2one('hc.payroll.period', string="Payroll Period")
    from_date = fields.Date('From Date', readonly=True,
                            required=True)
    to_date = fields.Date("To Date", readonly=True,  required=True)
    employee_id = fields.Many2many('hr.employee', string="Employee")

    @api.onchange('payroll_period')
    def onchange_date_range(self):
        if self.payroll_period:
            self.from_date = self.payroll_period.date_from
            self.to_date = self.payroll_period.date_to

    def print_report(self):
        domain = []
        datas = []
        if self.employee_id:
            domain.append(('id', '=', self.employee_id.ids))

        employees = self.env['hr.employee'].search(domain)
        for employee in employees:
            tz = pytz.timezone('Asia/Dubai')
            date_from = tz.localize(datetime.combine(fields.Datetime.from_string(str(self.from_date)), time.min))
            date_to = tz.localize(datetime.combine(fields.Datetime.from_string(str(self.to_date)), time.max))
            delta = date_to - date_from
            sick_leave = 0
            annual_leave = 0
            unpaid_leave = 0
            maternity_leave = 0
            parental_leave = 0
            bereavement_leave = 0
            attendance = self.env['hr.attendance'].search([('date', '>=', date_from),
                                                           ('date', '<=', date_to),
                                                           ('employee_id', '=', employee.id)])

            weekend = attendance.filtered(lambda r: r.is_weekend == True)
            total_number_of_leave = attendance.filtered(lambda r: r.time_off == True)

            leaves = self.env['hr.leave'].search(
                [('employee_id', '=', employee.id), ('request_date_from', '>=', date_from),
                 ('request_date_to', '<=', date_to),
                 ('state', '=', 'validate')])

            for leave in leaves:
                if leave.holiday_status_id.is_sick_leave:
                    sick_leave += leave.number_of_days
                if leave.holiday_status_id.is_annual_leave:
                    annual_leave += leave.number_of_days
                if leave.holiday_status_id.is_unpaid_leave:
                    unpaid_leave += leave.number_of_days
                if leave.holiday_status_id.is_maternity:
                    maternity_leave += leave.number_of_days
                if leave.holiday_status_id.is_parental:
                    parental_leave += leave.number_of_days
                if leave.holiday_status_id.is_compassionate:
                    bereavement_leave += leave.number_of_days
            total_hours = (len(attendance) - len(total_number_of_leave)) * 8
            datas.append({
                'id': employee.oe_emp_sequence,
                'name': employee.name,
                'present': len(attendance) - sick_leave,
                'absent': (delta.days + 1) - len(attendance),
                'sick_leaves': sick_leave,
                'unpaid_absent': unpaid_leave,
                'parental_leave': parental_leave,
                'bereavement_leave': bereavement_leave,
                'maternity_leave': maternity_leave,
                'annual_leave': annual_leave,
                'total_hours': total_hours,
                'day_off': len(weekend),
                'absences': len(total_number_of_leave)

            })
            flag = False
            less_than7 = False
        res = {
            'attendances': datas,
            'start_date': self.from_date,
            'end_date': self.to_date,
        }
        data = {
            'form': res,
        }
        return self.env.ref('attendance_report.report_hr_attendance').report_action([], data=data)

    def get_absences(self, employee=None, date_from=None, date_to=None, attendance_dates=None):
        """
            To get the absence of the employee for a specific date
            range for one employee at a time
            ==================Logic===============
            1: added subtract 31 days from the date from and added 31 days
            to date to for the purpose that it should not miss any leave
            in the given date range
            2: after that get all the dates of the leaves
            3: if attendance found or leave found then will not be considered as absence

            RETURN: length of the list of dates which does not exits in attendance_dates and leave_dates
            then it is considered as absence
        """
        df_to_dt_dates = []
        all_leaves_date = []
        e_date_from = copy.deepcopy(date_from) - timedelta(days=31)
        e_date_to = copy.deepcopy(date_to) + timedelta(days=31)
        domain = [('date_from', '>=', e_date_from),
                  ('date_to', '<=', e_date_to),
                  ('employee_id', '=', employee.id)]
        all_leaves = self.env['hr.leave'].search(domain)
        for rec in all_leaves:
            l_df = copy.deepcopy(rec.request_date_from)
            l_dt = copy.deepcopy(rec.request_date_to)
            while l_df <= l_dt:
                all_leaves_date.append(l_df)
                l_df += timedelta(days=1)

        while date_from <= date_to:
            df_to_dt_dates.append(date_from)
            date_from += timedelta(days=1)

        return len([rec for rec in df_to_dt_dates if rec not in (all_leaves_date + attendance_dates)])

    @staticmethod
    def get_attendance_dates(all_attendances=None):
        return [att.checkin_date for att in all_attendances]

    def get_leave(self, domain_for_leave=None, date_from=None, date_to=None, employee=None, attendance_date=None):
        """
            This method is to get the leaves in a specific date range

                 ============ Below Logic Applied ========
            1: extended the report date from and date to up to one month for the
                purpose to don't miss any leaves in the specified date range
            2: get the list of all the dates of the specific leave
            3: get the list of all the dates between date from and date to
            4: the purpose of getting the lists of the dates is that for comparison purpose
            e.g. if sick leave is from 14 to 19 jan and the report is getting
            print from 16 jan to 15 feb then it should get 4 days sick leave and ignore
            2 days of 14 and 15 because these dates are not given in the report date from and date to.

            return: length of the matching dates means if dates match leaves exists
        """

        l_date_from = copy.deepcopy(date_from) - timedelta(days=31)
        l_date_to = copy.deepcopy(date_to) + timedelta(days=31)
        all_leaves_date = []
        df_to_dt_dates = []
        domain = [('date_from', '>=', l_date_from),
                  ('date_to', '<=', l_date_to),
                  ('employee_id', '=', employee.id)]
        domain += domain_for_leave
        all_leaves = self.env['hr.leave'].search(domain)

        for rec in all_leaves:
            l_df = copy.deepcopy(rec.date_from)
            l_dt = copy.deepcopy(rec.date_to)
            while l_df <= l_dt:
                all_leaves_date.append(l_df.date())
                l_df += timedelta(days=1)

        while date_from <= date_to:
            df_to_dt_dates.append(date_from)
            date_from += timedelta(days=1)

        all_leaves_date = [d for d in all_leaves_date if d not in attendance_date]
        # all leaves date is enough to get the leaves but safety purpose below line is not removed
        # but, we can simply return just the above all_leaves_date
        return len([rec for rec in df_to_dt_dates if rec in all_leaves_date])
