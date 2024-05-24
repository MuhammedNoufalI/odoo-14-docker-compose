# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta
from pytz import timezone
from datetime import date, timedelta
import copy


class InheritHrPaySlip(models.Model):
    _inherit = 'hr.payslip'

    attendance_total_hours = fields.Float("Attendance Total Hours")
    leave_day_attendance = fields.Float("Leave Day attendance")
    month_absence = fields.Integer("Month Absence")
    month_attendance = fields.Integer("Month Attendance")

    # @api.depends('employee_id', 'date_from', 'date_to')
    # def get_attendance_data(self):
    #     for rec in self:
    #         if rec.date_from and rec.date_to and rec.employee_id:
    #             should_compare = self.env['ir.config_parameter'].sudo().get_param(
    #                 'hr_modification.compare_attendance_with_machine')
    #             if should_compare and not rec.employee_id.is_senior:
    #                 self._compare_attendance_with_machine(rec)
    #             else:
    #                 self.get_data_with_month_days(rec)
    #         else:
    #             rec.attendance_total_hours = 0
    #             rec.month_attendance = 0
    #             rec.leave_day_attendance = 0
    #             rec.month_absence = 0

    def get_data_with_month_days(self, record=None):
        for rec in record:
            if rec.employee_id and rec.date_from and rec.date_to:
                payslip_dates = self._get_payslip_dates_list(rec.date_from, rec.date_to)
                leaves_dates_list = self._get_leaves_dates_list(rec.employee_id, rec.date_from, rec.date_to)
                month_attendance = 0
                month_absence = 0
                if not len(leaves_dates_list) == rec.total_days:
                    month_attendance = len(set(payslip_dates) - set(leaves_dates_list)) - rec.total_days // 7
                    month_absence = len(leaves_dates_list) + rec.total_days // 7
                if month_absence:
                    month_absence -= (
                            rec.emp_month_leaves + rec.month_annual_leave + rec.month_unpaid_leaves +
                            rec.deduct_able_sick_leaves + rec.half_deductible_leaves +
                            rec.maternity_leaves_half + rec.maternity_leaves + rec.compassionate_leaves +
                            rec.parental_leaves
                    )
                if leaves_dates_list and not len(leaves_dates_list) == rec.total_days:
                    month_attendance -= 1
                    month_absence += 1
                rec.month_attendance = month_attendance
                rec.month_absence = month_absence
                rec.leave_day_attendance = 0
                rec.attendance_total_hours = 0
                rec.set_leaves_of_month(rec, payslip_dates)
            else:
                rec.month_absence = 0
                rec.month_attendance = 0
                rec.leave_day_attendance = 0
                rec.attendance_total_hours = 0

    def _compare_attendance_with_machine(self, record=None):
        total_hours = 0
        leave_day_presence = 0
        for rec in record:
            if rec.employee_id and rec.date_from and rec.date_to:

                tz = timezone(rec.employee_id.resource_calendar_id.tz)
                date_from = tz.localize(datetime.combine(fields.Datetime.from_string(str(rec.date_from)), time.min))
                date_to = tz.localize(datetime.combine(fields.Datetime.from_string(str(rec.date_to)), time.max))

                intervals = rec.employee_id.list_work_time_per_day(date_from, date_to,
                                                                   calendar=rec.employee_id.resource_calendar_id)

                delta = date_to - date_from

                all_attendances = self.env['hr.attendance'].search(
                    [('checkin_date', '>=', rec.date_from), ('checkout_date', '<=', rec.date_to),
                     ('employee_id', '=', rec.employee_id.id)])

                attendance_dates = []
                if all_attendances:
                    attendance_dates = rec.get_attendance_dates(all_attendances)
                # get all attendances b/w date_from and date_to with the selected employee
                attendances = self.env['hr.attendance'].search([
                    ('employee_id', '=', rec.employee_id.id),
                    ('check_in', '>=', rec.date_from),
                    ('check_out', '<=', rec.date_to)
                ])
                # now check attendance for single date from date_from till date_to
                presence = 0
                month_absence = 0
                for date in (rec.date_from + timedelta(n) for n in range((rec.date_to - rec.date_from).days + 1)):
                    attendances_exists = [record for record in attendances if date <= record[
                        "check_in"].date() < date + timedelta(days=1)]
                    if attendances_exists:
                        presence += 1
                        total_hours += attendances_exists[0].worked_hours
                        rec.attendance_total_hours = total_hours
                        rec.leave_day_attendance = leave_day_presence
                    # check for leave
                    else:
                        rec.attendance_total_hours = total_hours
                        rec.leave_day_attendance = leave_day_presence
                        is_leave_exists = self.env['hr.leave'].search([
                            ('state', '=', 'validate'),
                            ('date_from', '<=', date),
                            ('date_to', '>=', date),
                            ('employee_id', '=', rec.employee_id.id)
                        ])
                        if is_leave_exists:
                            continue
                        else:
                            month_absence += 1
                rec.set_leaves_of_month(rec, attendance_dates)
                rec.month_absence = rec.get_absences(rec.employee_id, rec.date_from, rec.date_to, all_attendances)
                rec.month_attendance = len(all_attendances)
                rec.leave_day_attendance = rec.get_leave_day_attendance(rec.employee_id, rec.date_from, rec.date_to,
                                                                        all_attendances)

            else:
                rec.month_absence = 0
                rec.month_attendance = 0
                rec.attendance_total_hours = 0
                rec.leave_day_attendance = 0

    @staticmethod
    def set_leaves_of_month(rec=None, attendance_dates=None):
        rec.emp_month_leaves = rec.get_leave([('holiday_status_id.is_sick_leave', '=', True)], rec.date_from,
                                             rec.date_to, rec.employee_id, attendance_dates)
        rec.month_annual_leave = rec.get_leave([('holiday_status_id.is_annual_leave', '=', True)],
                                               rec.date_from,
                                               rec.date_to, rec.employee_id, attendance_dates)
        rec.month_unpaid_leaves = rec.get_leave([('holiday_status_id.is_unpaid_leave', '=', True)],
                                                rec.date_from,
                                                rec.date_to, rec.employee_id, attendance_dates)

    def get_leave_day_attendance(self, emp=None, date_from=None, date_to=None, all_attendances=None):
        all_attendances_dates = all_attendances_dates = [att.checkin_date for att in all_attendances]
        leaves_dates = self._get_leaves_dates_list(emp, date_from, date_to)

        # get the leaves date which is in attendance dates means it was present that day
        present_dates = [p_d for p_d in leaves_dates if p_d in all_attendances_dates]
        return len(present_dates)

    @staticmethod
    def _get_payslip_dates_list(date_from=None, date_to=None):
        payslip_dates = []
        p_date_from = copy.deepcopy(date_from)
        p_date_to = copy.deepcopy(date_to)

        while p_date_from <= p_date_to:
            payslip_dates.append(p_date_from)
            p_date_from += timedelta(days=1)

        return payslip_dates

    def _get_leaves_dates_list(self, emp=None, date_from=None, date_to=None):
        leaves = self.env['hr.leave'].search([
            ('state', '=', 'validate'),
            ('date_from', '>=', date_from - timedelta(days=31)),
            ('date_to', '<=', date_to + timedelta(days=31)),
            ('employee_id', '=', emp.id)
        ])

        leaves_dates = []
        for leave in leaves:
            l_date_from = copy.deepcopy(leave.request_date_from)
            l_date_to = copy.deepcopy(leave.request_date_to)
            while l_date_from <= l_date_to:
                leaves_dates.append(l_date_from)
                l_date_from += timedelta(days=1)

        ps_df_dt_list = self._get_payslip_dates_list(date_from, date_to)
        return [rec for rec in leaves_dates if rec in ps_df_dt_list]

    def get_absences(self, emp=None, date_from=None, date_to=None, all_attendances=None):

        payslip_dates = self._get_payslip_dates_list(date_from, date_to)

        all_attendances_dates = [att.checkin_date for att in all_attendances]

        leaves_dates = self._get_leaves_dates_list(emp, date_from, date_to)

        # get leave dates only between date from and date to
        filtered_leave_dates = [f_d for f_d in payslip_dates if f_d not in (all_attendances_dates + leaves_dates)]
        return len(filtered_leave_dates)

    def check_for_leave(self, date=None, rec=None):
        is_leave_exists = self.env['hr.leave'].search([
            ('state', '=', 'validate'),
            ('date_from', '<=', date),
            ('date_to', '>=', date),
            ('employee_id', '=', rec.employee_id.id)
        ])
        if is_leave_exists:
            if is_leave_exists.holiday_status_id.is_compassionate:
                rec.compassionate_leaves -= 1
            elif is_leave_exists.holiday_status_id.is_maternity:
                rec.maternity_leave -= 1
            elif is_leave_exists.holiday_status_id.is_parental:
                rec.parental_leaves -= 1
            elif is_leave_exists.holiday_status_id.is_unpaid_leave:
                rec.month_unpaid_leaves -= 1
            elif is_leave_exists.holiday_status_id.is_annual_leave:
                rec.month_annual_leave -= 1
            elif is_leave_exists.holiday_status_id.is_sick_leave:
                rec.emp_month_leaves -= 1
        return is_leave_exists

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
                  ('employee_id', '=', employee.id),
                  ('state', '=', 'validate')
                  ]
        domain += domain_for_leave
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

        comp_mach_attend = self.env['ir.config_parameter'].sudo().get_param(
            'hr_modification.compare_attendance_with_machine')
        if comp_mach_attend:
            all_leaves_date = [d for d in all_leaves_date if d not in attendance_date]
            # all leaves date is enough to get the leaves but safety purpose below line is not removed
            # but, we can simply return just the above all_leaves_date
            return len([rec for rec in df_to_dt_dates if rec in all_leaves_date])
        else:
            return len([rec for rec in all_leaves_date if rec in df_to_dt_dates])

    @api.depends("employee_id")
    def _get_total_leaves(self):
        for rec in self:
            rec.emp_total_leaves = sum(
                self.env['hr.payslip'].search(
                    [('employee_id.id', '=', rec.employee_id.id), ('state', '=', 'done')]).mapped(
                    'emp_month_leaves'))
