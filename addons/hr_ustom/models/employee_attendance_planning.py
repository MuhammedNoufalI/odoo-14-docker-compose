# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
# import time
from pytz import timezone
from odoo import api, fields, models, _, tools
from odoo import SUPERUSER_ID
import pytz
from datetime import date, datetime, time

import logging

_logger = logging.getLogger(__name__)
import babel
from dateutil.relativedelta import relativedelta


class EmpAttendanceDetails(models.Model):
    _name = 'employee.attendance'
    _rec_name = 'employee_id'

    @api.onchange('employee_id', 'date_from')
    @api.constrains('employee_id', 'date_from')
    def onchange_employee(self):
        for rec in self:
            if not rec.date_from:
                rec.name = _('Attendance Sheet of %s') % (rec.employee_id.name)
            else:

                ttyme = datetime.combine(fields.Date.from_string(rec.date_from), time.min)
                locale = self.env.context.get('lang') or 'en_US'
                rec.name = _('Attendance Sheet of %s for %s') % (
                rec.employee_id.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)))

    name = fields.Char()
    employee_id = fields.Many2one('hr.employee', string='Employee')

    def _get_from_date(self):
        from_day = self.env['ir.config_parameter'].sudo().get_param('payroll_from_day')
        from_month = self.env['ir.config_parameter'].sudo().get_param('payroll_from_month')
        return str(datetime.now() + relativedelta(months=int(from_month), day=int(from_day)))[:10]

    def _get_to_date(self):
        to_day = self.env['ir.config_parameter'].sudo().get_param('payroll_to_day')
        to_month = self.env['ir.config_parameter'].sudo().get_param('payroll_to_month')
        return str(datetime.now() + relativedelta(months=int(to_month), day=int(to_day)))[:10]

    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id',
                                    store=True)
    date_from = fields.Date('Date From', default=_get_from_date)
    date_to = fields.Date('Date To', default=_get_to_date)

    employee_attendance_line = fields.One2many(comodel_name="employee.attendance.lines",
                                               inverse_name="emp_attendance_line_id", string="", required=False, )
    employee_absent_line = fields.One2many(comodel_name="employee.absent.lines", inverse_name="emp_attendance_line_id",
                                           string="", required=False, )
    total_late = fields.Float(strinbg='Late', compute='compute_totals', store=True)
    total_early = fields.Float(strinbg='Early', compute='compute_totals', store=True)
    total_overtime = fields.Float(strinbg='Overtime', compute='compute_totals', store=True)
    deduction = fields.Float(string='Absent Deduction', compute='compute_absent_deduction',
                             inverse="_inverse_deduction", store=True)
    late_deduction = fields.Float(string='Late Deduction', compute='compute_late_deduction',
                                  inverse="_inverse_late_deduction", store=True)
    early_deduction = fields.Float(string='Early Deduction', compute='compute_early_deduction',
                                   inverse="_inverse_early_deduction", store=True)
    bonus = fields.Float(string='Bonus', compute='compute_bonus', inverse="_inverse_bonus", store=True)
    total_absent = fields.Integer(string='Absent', compute='compute_total_absent', store=True)

    def button_allocation_request(self):
        return {
            'name': 'Allocation',
            'view_mode': 'form',
            'res_model': 'hr.leave.allocation',
            'type': 'ir.actions.act_window',
            'context': {'default_number_of_hours_display': self.bonus, 'default_emp_attendance_id': self.id,
                        'default_holiday_status_id': self.env.ref('hr_holidays.holiday_status_comp').id,
                        'employee_id': self.employee_id.id},
            'target': 'current',
        }

    def button_leave_request(self):
        return {
            'name': 'Leave',
            'view_mode': 'form',
            'res_model': 'hr.leave',
            'type': 'ir.actions.act_window',
            'context': {'default_emp_attendance_id': self.id,
                        'default_holiday_status_id': self.env.ref('hr_holidays.holiday_status_comp').id,
                        'employee_id': self.employee_id.id},
            'target': 'current',
        }

    @api.depends('employee_attendance_line', 'employee_attendance_line.late', 'employee_attendance_line.early',
                 'employee_attendance_line.over_time')
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
    def compute_absent_deduction(self):
        count = 0
        total = 0
        for att in self:
            deductions = self.env['hr.attendance.deduction'].search([('type', '=', 'absent')],
                                                                    order='absent_repeat desc')
            for rec in att.employee_absent_line:
                count += 1
                for ded in deductions:
                    if int(ded.absent_repeat) <= count:
                        total += ded.deduction
                        break
            att.deduction = total

    def _inverse_late_deduction(self):
        pass

    @api.depends('employee_attendance_line')
    def compute_late_deduction(self):
        early = 0.0
        late_early_rules = self.env['hr.attendance.deduction'].search([('type', '=', 'late')])

        for rec in self:
            if rec.total_late > 0.0:
                hour_levle = []
                f_l_h_l = s_l_h_l = t_l_h_l = fo_l_h_l = fi_l_h_l = []
                first_hour_late = []
                second_hour_late = []
                third_hour_late = []
                four_hour_late = []
                five_hour_late = []
                for line in late_early_rules:
                    if line.type == 'late':
                        if line.hour_level == '1':
                            first_hour_late.append(line.id)
                        elif line.hour_level == '2':
                            second_hour_late.append(line.id)
                        elif line.hour_level == '3':
                            third_hour_late.append(line.id)
                        elif line.hour_level == '4':
                            four_hour_late.append(line.id)
                        elif line.hour_level == '5':
                            five_hour_late.append(line.id)
                val_deduction = 0
                for attendance in rec.employee_attendance_line:
                    late_rule_exist = False
                    if attendance.late > 0.0:
                        late = attendance.late

                        if late_early_rules:
                            for rule in late_early_rules:
                                hour_levle.append(int(rule.hour_level))
                                if rule.hour_level == '1':
                                    if attendance.repeate_late == rule.repetition:
                                        time_from = rule.time_from
                                        time_to = rule.time_to
                                        if late >= time_from and late <= time_to:
                                            late_rule_exist = True
                                            if rule.id not in f_l_h_l:
                                                f_l_h_l.append(rule.id)
                                                if rule.warning:
                                                    break
                                                else:
                                                    val_deduction += rule.deduction
                                                    break
                                            else:
                                                if rule.id != int(first_hour_late[-1]):
                                                    continue
                                                else:
                                                    if rule.warning:
                                                        break
                                                    else:
                                                        val_deduction += rule.deduction
                                                        break
                                elif rule.hour_level == '2':
                                    if attendance.repeate_late == rule.repetition:
                                        time_from = rule.time_from
                                        time_to = rule.time_to
                                        if late >= time_from and late <= time_to:
                                            late_rule_exist = True
                                            if rule.id not in s_l_h_l:
                                                s_l_h_l.append(rule.id)
                                                if rule.warning:
                                                    break
                                                else:
                                                    val_deduction += rule.deduction
                                                    break
                                            else:
                                                if rule.id != int(second_hour_late[-1]):
                                                    continue
                                                else:
                                                    if rule.warning:
                                                        break
                                                    else:
                                                        val_deduction += rule.deduction
                                                        break
                                elif rule.hour_level == '3':
                                    if attendance.repeate_late == rule.repetition:

                                        time_from = rule.time_from
                                        time_to = rule.time_to
                                        if late >= time_from and late <= time_to:
                                            late_rule_exist = True
                                            if rule.id not in t_l_h_l:
                                                t_l_h_l.append(rule.id)
                                                if rule.warning:
                                                    break
                                                else:
                                                    val_deduction += rule.deduction
                                            else:
                                                if rule.id != int(third_hour_late[-1]):
                                                    continue
                                                else:
                                                    if rule.warning:
                                                        break
                                                    else:
                                                        val_deduction += rule.deduction
                                                        break
                                elif rule.hour_level == '4':
                                    if attendance.repeate_late == rule.repetition:
                                        time_from = rule.time_from
                                        time_to = rule.time_to
                                        if late >= time_from and late <= time_to:
                                            late_rule_exist = True
                                            if rule.id not in fo_l_h_l:
                                                fo_l_h_l.append(rule.id)
                                                if rule.warning:
                                                    break
                                                else:
                                                    val_deduction += rule.deduction
                                            else:
                                                if rule.id != int(four_hour_late[-1]):
                                                    continue
                                                else:
                                                    if rule.warning:
                                                        break

                                                    else:
                                                        val_deduction += rule.deduction
                                                        break
                                elif rule.hour_level == '5':
                                    if attendance.repeate_late == rule.repetition:
                                        time_from = rule.time_from
                                        time_to = rule.time_to
                                        if late >= time_from and late <= time_to:
                                            late_rule_exist = True
                                            if rule.id not in fi_l_h_l:
                                                fi_l_h_l.append(rule.id)
                                                if rule.warning:
                                                    break
                                                else:
                                                    val_deduction += rule.deduction
                                            else:
                                                if rule.id != int(second_hour_late[-1]):
                                                    continue
                                                else:
                                                    if rule.warning:
                                                        break

                                                    else:
                                                        val_deduction += rule.deduction
                                                        break
                            if not late_rule_exist:
                                max_repetition = []
                                if hour_levle:
                                    for rule12 in late_early_rules.filtered(
                                            lambda r: r.hour_level == str(max(hour_levle))):
                                        max_repetition.append(rule12.repetition)
                                    for rule2 in late_early_rules.filtered(
                                            lambda r: r.hour_level == str(max(hour_levle)) and r.repetition == max(
                                                max_repetition)):

                                        time_from = rule2.time_from
                                        time_to = rule2.time_to
                                        if late >= time_from and attendance.repeate_late >= rule2.repetition:

                                            if rule2.warning:
                                                continue
                                            else:
                                                val_deduction += rule2.deduction
                rec.late_deduction = val_deduction

            else:
                rec.late_deduction = 0

    def _inverse_early_deduction(self):
        pass

    @api.depends('employee_attendance_line')
    def compute_early_deduction(self):
        early = 0.0
        late_early_rules = self.env['hr.attendance.deduction'].search([('type', '=', 'early')])

        for rec in self:
            if rec.total_late > 0.0:
                hour_levle = []
                f_l_h_l = s_l_h_l = t_l_h_l = fo_l_h_l = fi_l_h_l = []
                first_hour_late = []
                second_hour_late = []
                third_hour_late = []
                four_hour_late = []
                five_hour_late = []
                for line in late_early_rules:
                    if line.hour_level == '1':
                        first_hour_late.append(line.id)
                    elif line.hour_level == '2':
                        second_hour_late.append(line.id)
                    elif line.hour_level == '3':
                        third_hour_late.append(line.id)
                    elif line.hour_level == '4':
                        four_hour_late.append(line.id)
                    elif line.hour_level == '5':
                        five_hour_late.append(line.id)
                val_deduction = 0
                for attendance in rec.employee_attendance_line:
                    late_rule_exist = False
                    if attendance.late > 0.0:
                        late = attendance.late

                        if late_early_rules:
                            for rule in late_early_rules:
                                hour_levle.append(int(rule.hour_level))
                                if rule.hour_level == '1':
                                    if attendance.repeate_early == rule.repetition:
                                        time_from = rule.time_from
                                        time_to = rule.time_to
                                        if late >= time_from and late <= time_to:
                                            late_rule_exist = True
                                            if rule.id not in f_l_h_l:
                                                f_l_h_l.append(rule.id)
                                                if rule.warning:
                                                    break
                                                else:
                                                    val_deduction += rule.deduction
                                                    break
                                            else:
                                                if rule.id != int(first_hour_late[-1]):
                                                    continue
                                                else:
                                                    if rule.warning:
                                                        break
                                                    else:
                                                        val_deduction += rule.deduction
                                                        break
                                elif rule.hour_level == '2':
                                    if attendance.repeate_early == rule.repetition:
                                        time_from = rule.time_from
                                        time_to = rule.time_to
                                        if late >= time_from and late <= time_to:
                                            late_rule_exist = True
                                            if rule.id not in s_l_h_l:
                                                s_l_h_l.append(rule.id)
                                                if rule.warning:
                                                    break
                                                else:
                                                    val_deduction += rule.deduction
                                                    break
                                            else:
                                                if rule.id != int(second_hour_late[-1]):
                                                    continue
                                                else:
                                                    if rule.warning:
                                                        break
                                                    else:
                                                        val_deduction += rule.deduction
                                                        break
                                elif rule.hour_level == '3':
                                    if attendance.repeate_early == rule.repetition:

                                        time_from = rule.time_from
                                        time_to = rule.time_to
                                        if late >= time_from and late <= time_to:
                                            late_rule_exist = True
                                            if rule.id not in t_l_h_l:
                                                t_l_h_l.append(rule.id)
                                                if rule.warning:
                                                    break
                                                else:
                                                    val_deduction += rule.deduction
                                            else:
                                                if rule.id != int(third_hour_late[-1]):
                                                    continue
                                                else:
                                                    if rule.warning:
                                                        break
                                                    else:
                                                        val_deduction += rule.deduction
                                                        break
                                elif rule.hour_level == '4':
                                    if attendance.repeate_early == rule.repetition:
                                        time_from = rule.time_from
                                        time_to = rule.time_to
                                        if late >= time_from and late <= time_to:
                                            late_rule_exist = True
                                            if rule.id not in fo_l_h_l:
                                                fo_l_h_l.append(rule.id)
                                                if rule.warning:
                                                    break
                                                else:
                                                    val_deduction += rule.deduction
                                            else:
                                                if rule.id != int(four_hour_late[-1]):
                                                    continue
                                                else:
                                                    if rule.warning:
                                                        break

                                                    else:
                                                        val_deduction += rule.deduction
                                                        break
                                elif rule.hour_level == '5':
                                    if attendance.repeate_early == rule.repetition:
                                        time_from = rule.time_from
                                        time_to = rule.time_to
                                        if late >= time_from and late <= time_to:
                                            late_rule_exist = True
                                            if rule.id not in fi_l_h_l:
                                                fi_l_h_l.append(rule.id)
                                                if rule.warning:
                                                    break
                                                else:
                                                    val_deduction += rule.deduction
                                            else:
                                                if rule.id != int(second_hour_late[-1]):
                                                    continue
                                                else:
                                                    if rule.warning:
                                                        break

                                                    else:
                                                        val_deduction += rule.deduction
                                                        break
                            if not late_rule_exist:
                                max_repetition = []
                                if hour_levle:
                                    for rule12 in late_early_rules.filtered(
                                            lambda r: r.hour_level == str(max(hour_levle))):
                                        max_repetition.append(rule12.repetition)
                                    for rule2 in late_early_rules.filtered(
                                            lambda r: r.hour_level == str(max(hour_levle)) and r.repetition == max(
                                                max_repetition)):

                                        time_from = rule2.time_from
                                        time_to = rule2.time_to
                                        if late >= time_from and attendance.repeate_early >= rule2.repetition:

                                            if rule2.warning:
                                                continue
                                            else:
                                                val_deduction += rule2.deduction
                rec.early_deduction = val_deduction

            else:
                rec.early_deduction = 0

    def _inverse_bonus(self):
        pass

    @api.depends('total_overtime')
    def compute_bonus(self):
        overtime_hour = 0
        for att in self:
            for rule in self.env['hr.attendance.bonus'].search([]):
                if rule.time_to >= att.total_overtime >= rule.time_from:
                    overtime_hour += rule.bonus_hours
                    break

            att.bonus = overtime_hour
            # if att.over_time > 0.0:
            #         over_time = att.over_time
            #         for rule in self.env['hr.attendance.bonus'].search([]):
            #             if attendance_datetime.strftime('%A') in weekend_days:
            #                 if rule.rest_day:
            #                     over_time_hour = over_time / 60
            #                     overtime_hour += over_time_hour * rule.bonus_hours
            #                     break
            #             else:
            #                 time_from = rule.time_from
            #                 time_to = rule.time_to
            #                 if time_to >= over_time >= time_from:
            #                     overtime_hour += rule.bonus_hours
            #                     break

    def is_public_holiday(self, date, resource_calendar_id):
        return any(x.date_from <= date and date <= x.date_to for x in resource_calendar_id.public_holiday_ids)

    def is_leave_request(self, date):
        holidays = self.env['hr.leave'].sudo().search([
            ('employee_id', '=', self.employee_id.id),
            ('date_from', '<=', fields.Datetime.now()),
            ('date_to', '>=', fields.Datetime.now()),
            ('state', 'not in', ('cancel', 'refuse'))
        ])
        return any(
            x.date_from <= date and date <= x.date_to for x in self.employee_id.resource_calendar_id.public_holiday_ids)

    def check_has_leave(self, check_in):
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
            for line in working_hours.attendance_ids:
                if int(line.dayofweek) == date_out.weekday():
                    hour = line.hour_to
        return hour

    def _compute_early(self, earl, line):
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        early = 0.0
        over_time = 0.00

        if earl.check_out and earl.check_in and earl.employee_id.resource_calendar_id:
            check_out = self._get_check_time(earl.check_out).replace(tzinfo=None)
            work_end = self._get_check_time(line.end_datetime).replace(tzinfo=None)
            # work_end = pytz.utc.localize(datetime.strptime(str(line.end_datetime), DATETIME_FORMAT)).replace(tzinfo=None)

            over_time = 0.00

            if check_out < work_end:
                dif = work_end - check_out
                early = (float(dif.seconds) / 3600)
            elif check_out > work_end:
                dif2 = check_out - work_end
                over_time = float(dif2.seconds) / 3600
            else:
                early = 0.00
                over_time = 0.00
        return early, over_time

    def get_work_from(self, date_in, working_hours_id):
        hour = 0.0
        if type(date_in) is datetime:
            working_hours = working_hours_id
            for line in working_hours.attendance_ids:
                if int(line.dayofweek) == date_in.weekday():
                    hour = line.hour_from
        return hour

    def _get_check_time(self, check_date):
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        user_id = self.env['res.users']
        user = user_id.browse(SUPERUSER_ID)
        tz = pytz.timezone((self.env.user.tz or 'UTC'))
        _logger.info("IIIIIIIII{}".format(tz))
        print(check_date)
        checkdate = pytz.utc.localize(datetime.strptime(str(check_date), DATETIME_FORMAT)).astimezone(tz)
        print(checkdate)

        return checkdate

    def check_leave_of_type_hour(self, work_start):
        res = self.env['hr.leave'].sudo().search([
            ('holiday_status_id.request_unit', '=', 'hour'),
            ('request_unit_hours', '=', True),
            ('employee_id', '=', self.employee_id.id),
            ('date_from', '<=', work_start),
            ('date_to', '>=', work_start),
            ('state', 'not in', ('cancel', 'refuse'))
        ], limit=1)
        if res:
            return res.date_to
        else:
            return work_start

    def _compute_late(self, lat, line):
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

        if lat.check_in and lat.employee_id.resource_calendar_id:
            check_in = self._get_check_time(lat.check_in).replace(tzinfo=None)
            work_start = self._get_check_time(line.start_datetime).replace(tzinfo=None)
            # self.check_leave_of_type_hour(work_start)
            if check_in > work_start:
                dif = check_in - work_start
                late = float(dif.seconds) / 3600
            else:
                late = 0.00
        else:
            late = 0.00
        return late

    def get_custom_resource_calendar_line(self, employee, start, end):
        plans = self.env['planning.slot'].search([('role_id', 'in', employee.planning_role_ids.ids)])
        plans = plans.filtered(
            lambda x: x.start_datetime.date() >= self.date_from and x.end_datetime.date() <= self.date_to)
        line = plans.filtered(lambda x: x.start_datetime.date() == start and x.end_datetime.date() == end)
        if line:
            line = line[0]
        return line

    def compute_attendance(self):
        attendance_ids = self.env['hr.attendance'].search(
            [('employee_id', '=', self.employee_id.id), ('check_in', '>=', self.date_from),
             ('check_out', '<=', self.date_to)], order='check_in')
        attendance_dates = [rec.check_in.date() for rec in attendance_ids]
        lines = []
        absent_lines = []
        # for attendance in attendance_ids:
        delta = self.date_to - self.date_from  # as timedelta
        days = [self.date_from + timedelta(days=i) for i in range(delta.days + 1)]
        if self.employee_id.is_custom_shift:
            plans = self.env['planning.slot'].search([('role_id', 'in', self.employee_id.planning_role_ids.ids)])
            plans = plans.filtered(
                lambda x: x.start_datetime.date() >= self.date_from and x.end_datetime.date() <= self.date_to)

            custom_attendance_dates = [y.start_datetime.date() for y in plans]

            for dr in days:
                attendances = attendance_ids.filtered(lambda x: x.check_in.date() == dr)
                if attendances:
                    late_attendance = attendances[0]
                    early_attendance = attendances[-1]
                    line = self.get_custom_resource_calendar_line(self.employee_id, late_attendance.check_in.date(),
                                                                  early_attendance.check_out.date())
                    if line:
                        early, over_time = self._compute_early(early_attendance, line)
                        sd = self._get_check_time(line.start_datetime).replace(tzinfo=None)
                        sd = sd.time()
                        hour_from = sd.hour + sd.minute / 60.0
                        ed = self._get_check_time(line.end_datetime).replace(tzinfo=None)
                        tim = ed.time()
                        hour_to = tim.hour + tim.minute / 60.0
                        _logger.info(">>>>>{}".format(line.end_datetime.date()))
                        vals = {
                            'date': late_attendance.check_in.date(),
                            'shift_start_day': str(line.start_datetime.date().weekday()),
                            'hour_from': hour_from,
                            'shift_end_day': str(ed.weekday()),
                            'hour_to': hour_to,
                            'check_in': late_attendance.check_in,
                            'late': self._compute_late(late_attendance, line),
                            'early': early,
                            'over_time': over_time,
                            'check_out': early_attendance.check_out,
                            'attendance_ids': [(6, 0, attendances.ids)],
                        }
                        lines.append((0, 0, vals))
                    else:
                        if late_attendance.check_in.date() not in custom_attendance_dates:
                            vals = {
                                'date': late_attendance.check_in.date(),
                                'shift_start_day': str(late_attendance.check_in.date().weekday()),
                                'hour_from': 0,
                                'shift_end_day': str(early_attendance.check_out.date().weekday()),
                                'hour_to': 0,
                                'check_in': late_attendance.check_in,
                                'late': self._compute_late(late_attendance, line),
                                'early': 0,
                                'over_time': over_time,
                                'check_out': early_attendance.check_out,
                                'attendance_ids': [(6, 0, attendances.ids)],
                            }
                            lines.append((0, 0, vals))
            for dr in days:
                if not self.check_has_leave(dr) and not self.is_public_holiday(dr,
                                                                               self.employee_id.resource_calendar_id) and dr not in attendance_dates and dr in custom_attendance_dates:
                    vals = {'date': dr}
                    absent_lines.append((0, 0, vals))
        else:
            for attendance in attendance_ids:
                vals = {
                    'date': attendance.check_in.date(),
                    'shift_start_day': str(attendance.check_in.date().weekday()),
                    'hour_from': attendance.get_work_from(attendance.check_in,
                                                          attendance.employee_id.resource_calendar_id),
                    'shift_end_day': str(attendance.check_out.date().weekday()),
                    'hour_to': attendance.get_work_to(attendance.check_out,
                                                      attendance.employee_id.resource_calendar_id),
                    'check_in': attendance.check_in,
                    'late': attendance.late,
                    'early': attendance.early,
                    'over_time': attendance.over_time,
                    'check_out': attendance.check_out,
                    'attendance_ids': [(6, 0, attendance.ids)],
                }
                lines.append((0, 0, vals))
            for dr in days:
                if not self.check_has_leave(dr) and not self.is_public_holiday(dr,
                                                                               self.employee_id.resource_calendar_id) and dr not in attendance_dates and str(
                        dr.weekday()) in self.employee_id.resource_calendar_id.attendance_ids.mapped('dayofweek'):
                    vals = {'date': dr}
                    absent_lines.append((0, 0, vals))
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
    late = fields.Float(string='Late Check In', )  # compute='_compute_late'
    early = fields.Float(string='Early Check Out', )  # compute='_compute_early'
    over_time = fields.Float(string='Over Time', )  # compute='_compute_early'

    worked_hours = fields.Float(string='Worked Hours', compute='_compute_worked_hours', store=True, readonly=True)

    @api.depends('check_in', 'check_out', 'attendance_ids')
    def _compute_worked_hours(self):
        for attendance in self:
            if attendance.check_out and attendance.check_in:
                delta = attendance.check_out - attendance.check_in
                attendance.worked_hours = sum(attendance.attendance_ids.mapped('worked_hours'))
                # attendance.worked_hours = delta.total_seconds() / 3600.0
            else:
                attendance.worked_hours = False

    repeate_late = fields.Integer(string="Repeate Late", required=False, compute='get_repeate_late')
    repeate_early = fields.Integer(string="Repeate early", required=False, compute='get_repeate_early')

    @api.depends('check_in', 'late')
    def get_repeate_late(self):
        for att in self:
            repeate_num_prev = 0
            att.repeate_late = 0
            for rec in self.search(
                    [('check_in', '<', att.check_in), ('emp_attendance_line_id', '<', att.emp_attendance_line_id.id)]):
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
            for rec in self.search([('check_out', '<', att.check_out),
                                    ('emp_attendance_line_id', '<', att.emp_attendance_line_id.id)]):
                if rec.id != att.id and rec.early > 0:
                    check_out_date = datetime.strptime(str(rec.check_out), '%Y-%m-%d %H:%M:%S').date()
                    current_check_out = datetime.strptime(str(att.check_out), '%Y-%m-%d %H:%M:%S').date()
                    if check_out_date < current_check_out and check_out_date.year == current_check_out.year and current_check_out.month == current_check_out.month:
                        repeate_num_prev += 1
            if att.early > 0:
                att.repeate_early = repeate_num_prev + 1
            else:
                att.repeate_early = 0


class EmpAbsentLines(models.Model):
    _name = 'employee.absent.lines'
    emp_attendance_line_id = fields.Many2one('employee.attendance')
    date = fields.Date('Date')
