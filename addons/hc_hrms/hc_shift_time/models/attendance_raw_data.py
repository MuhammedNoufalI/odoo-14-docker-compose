# -*- coding: utf-8 -*-

from datetime import datetime, timedelta, timezone
from pytz import timezone, UTC, utc
import pytz
from dateutil.relativedelta import relativedelta
from odoo import fields, models


class HrRawAttendance(models.Model):
    _name = 'hc.raw.attendance'
    _description = 'Hr Raw Attendance'
    _rec_name = "id"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    employee_id = fields.Many2one('hr.employee', string="Employee")
    # hc_employee_id = fields.Many2one('hr.employee', string='Employee')
    punched_time = fields.Datetime('PunchDateTime', tracking=True)
    date = fields.Date("Date", compute='_compute_datetime', tracking=True)
    branch_id = fields.Many2one('hc.branch', string="Machine Location", tracking=True)
    is_checkin = fields.Boolean('Is Checkin', tracking=True, compute='_compute_punch_type_selection')
    state = fields.Selection([('draft', 'Draft'), ('fixed', 'Fixed'), ('processed', 'Processed'),
                              ('time_off', 'Time Off'),
                              ('exception', 'Exception'), ('cancel', 'Cancelled')],
                             string='State', required=True, default='draft', store=True, tracking=True)
    late_checkin_approved = fields.Boolean(string="Late Checkin", help="Is Complete Mandatory Hours Rewarded")
    exception_id = fields.Many2one('hc.attendance.exception', string="Exception")
    company_name = fields.Char(string='CompanyName')
    badge_number = fields.Char(string='BadgeNumber')
    punch_type = fields.Char(string='PunchType')
    device_Id = fields.Char(string='Device ID')

    def button_duplicate_raw_line(self):
        for rec in self:
            ctx = self._context.get('default_exception_id')
            rec.copy({'exception_id': ctx})

    def _compute_punch_type_selection(self):
        for punch in self:
            if punch.punch_type == "1":
                punch.is_checkin = False
            elif punch.punch_type == "0":
                punch.is_checkin = True
            else:
                punch.is_checkin = None

    def _compute_datetime(self):
        for rec in self:
            if rec.punched_time:
                rec.date = rec.punched_time.date()

    def button_cancel(self):
        for rec in self:
            rec.write({'state': 'cancel'})

    # def _prepare_break_hours(self, emp, ):

    def calculate_attendance(self):
        raw_attendances = self.env['hc.raw.attendance'].sudo().search([('state', 'in', ['draft', 'fixed'])],
                                                               order="employee_id asc, punched_time asc")

        raw_attendance_records = {}
        i = 0
        last_punch_date = None

        for attendance in raw_attendances.filtered(lambda att: att.employee_id):
            employee = attendance.employee_id
            punched_time_date_utc = attendance.punched_time + timedelta(hours=4)
            punched_time_date = punched_time_date_utc.date()
            add_raw_attendance = False

            if punched_time_date < fields.Date.today():
                add_raw_attendance = True
            elif punched_time_date == fields.Date.today():
                add_raw_attendance = False
                prev_date = fields.Date.today() - relativedelta(days=1)
                prev_day = prev_date.weekday()
                contract = employee.contract_ids.filtered(lambda c: c.state == 'open' or 'probation')
                # current_shift = contract.resource_calendar_id.attendance_ids.filtered(
                #     lambda x: x.dayofweek == str(prev_day))
                if last_punch_date is not None:
                    # if last_punch_date != fields.Date.today() and not attendance.is_checkin and current_shift.is_check_out_next_day:
                    if last_punch_date != fields.Date.today() and not attendance.is_checkin :
                        add_raw_attendance = True

            if add_raw_attendance:
                if employee not in raw_attendance_records.keys():
                    raw_attendance_records.update({employee: [
                        {'punched_time': attendance.punched_time, 'is_checkin': attendance.is_checkin,
                         'branch': attendance.branch_id,
                         'raw_attendance_id': attendance}]})
                else:
                    raw_attendance_records[employee].append(
                        {'punched_time': attendance.punched_time, 'is_checkin': attendance.is_checkin,
                         'branch': attendance.branch_id,
                         'raw_attendance_id': attendance})
            last_punch_date_utc = attendance.punched_time + timedelta(hours=4)
            last_punch_date = last_punch_date_utc.date()

        checkin_checkout_records = {}
        exception_raw_attendance_records = {}

        for emp, values in raw_attendance_records.items():
            raw_attendance_date_records = {}
            last_punch_date = None
            is_last_punch_checkin = False
            for punch_data in values:
                punch_date_utc = punch_data.get('punched_time') + timedelta(hours=4)
                punch_date = punch_date_utc.date()
                ischeckin = punch_data.get('is_checkin')
                if not ischeckin and is_last_punch_checkin and (last_punch_date + relativedelta(days=1)) == punch_date:
                    punch_date = last_punch_date
                if punch_date not in raw_attendance_date_records.keys():
                    raw_attendance_date_records.update({punch_date: [punch_data]})
                else:
                    raw_attendance_date_records[punch_date].append(punch_data)
                last_punch_date = punch_date
                is_last_punch_checkin = ischeckin

            exception_raw_attendance_records_values = []
            checkin_checkout_list = []

            for punch_date, punch_data_list in raw_attendance_date_records.items():
                i = 0
                checkin = False
                checkout = False
                checkin_checkout_pair = {'checkin': None, 'checkin_raw_attendance_id': 0, 'checkout': None,
                                         'checkout_raw_attendance_id': 0}

                if len(punch_data_list) % 2 == 0:

                    for punch_data in punch_data_list:
                        i += 1
                        if i % 2 != 0:
                            checkin = False
                            if punch_data.get('is_checkin'):
                                checkin_checkout_pair.update({'checkin': punch_data.get('punched_time'),
                                                              'checkin_raw_attendance_id': punch_data.get(
                                                                  'raw_attendance_id')})
                                checkin = True
                            else:
                                break
                        else:
                            checkout = False
                            if not punch_data.get('is_checkin'):
                                checkin_checkout_pair.update({'checkout': punch_data.get('punched_time'),
                                                              'checkout_raw_attendance_id': punch_data.get(
                                                                  'raw_attendance_id')})
                                checkout = True
                            else:
                                break
                            checkin_checkout_list.append(checkin_checkout_pair.copy())

                if not checkin or not checkout:
                    exception_raw_attendance_records_values.extend(raw_attendance_date_records.get(punch_date))

            if len(exception_raw_attendance_records_values) > 0:
                exception_raw_attendance_records.update({emp: exception_raw_attendance_records_values.copy()})

            if len(checkin_checkout_list) > 0:
                checkin_checkout_records.update({emp: checkin_checkout_list.copy()})

        if exception_raw_attendance_records:
            self._create_exception(exception_raw_attendance_records)
            exception_raw_attendance_records = {}

        if checkin_checkout_records:
            self._create_attendance_date_records(checkin_checkout_records)
            checkin_checkout_records = {}

    def _create_exception(self, exception_raw_attendance_records):
        """To Fetch the Exception Records """
        for emp, values in exception_raw_attendance_records.items():
            record = self.env['hc.attendance.exception'].sudo().create({'employee_id': emp.id})
            for val in values:
                record.write({
                    'raw_attendance_line_ids': [(4, val.get('raw_attendance_id').id)],
                    'datetime': val.get('punched_time')
                })
                val.get('raw_attendance_id').write({'state': 'exception'})

    def _create_attendance_date_records(self, checkin_checkout_records):
        call = 0
        for emp, checkin_checkout in checkin_checkout_records.items():
            checkin_checkout_date_records = {}
            new_key_added = False
            for check_in_out in checkin_checkout:
                checkin = check_in_out.get('checkin')
                checkout = check_in_out.get('checkout')
                checkin_date_utc = checkin + timedelta(hours=4)
                checkin_date = checkin_date_utc.date()
                checkout_date_utc = checkout + timedelta(hours=4)
                checkout_date = checkout_date_utc.date()
                # if not len(checkin_checkout_date_records) >= 2:
                if checkin_date not in checkin_checkout_date_records.keys():
                    checkin_checkout_date_records.update({checkin_date: [check_in_out]})

                elif checkin_date in checkin_checkout_date_records.keys() and not new_key_added and len(checkin_checkout_date_records[checkin_date]) >= 1:
                    checkin_checkout_date_records.update({checkout_date: [check_in_out]})
                    new_key_added = True
                else:
                    checkin_checkout_date_records[checkin_date].append(check_in_out)
            self._create_attendance(emp, checkin_checkout_date_records)

    def _create_attendance(self, emp, checkin_checkout_date_records):
        for checkin_date, checkin_checkout in checkin_checkout_date_records.items():
            checkin_date_utc_1 = checkin_checkout[0].get('checkin') + timedelta(hours=4)
            created_attendance = self.env['hr.attendance'].sudo().search([('employee_id', '=', emp.id),
                                                                   ('date', '=', checkin_date
                                                                    )])

            if created_attendance:
                i = 1
                missed_hours = 0.0
                total_hours = 0.0
                extra_hours = 0.0
                break_hours = 0.0
                # flexible_break_hours = 0.0
                used_flexible_break_hour = 0.0
                shift_flexible_hours = 0
                actual_checkin = None
                actual_checkout = None

                val = {}
                nwd = 1
                # Time Off
                if created_attendance.time_off:
                    if not created_attendance.leave_id.holiday_status_id.include_to_net_working:
                        nwd = 0
                    val = {
                        'actual_checkin': False,
                        'actual_checkout': False,
                        # 'late_hour': 0.0,
                        # 'early_hour': 0.0,
                        'missed_effort': 0.0,
                        'paid_leave': 0.0,
                        'unpaid_leave': 0.0,
                        'net_working_days': nwd,
                        'total_worked_hours': 0.0,
                        'break_hours': 0.0,
                        'extra_hours': 0.0,
                        'mandatory_hours': 0.0,
                        'actual_mandatory_hours': 0.0,
                        'state': "processed"
                    }
                    created_attendance.write(val)
                    for check_in_out in checkin_checkout:
                        check_in_out.get('checkin_raw_attendance_id').write({'state': 'time_off'})
                        check_in_out.get('checkout_raw_attendance_id').write({'state': 'time_off'})
                        continue
                # PUBLIC HOLIDAY, SPECIAL HOLIDAY OR WEEKEND
                if created_attendance.public_holiday or created_attendance.is_special_holiday or created_attendance.is_weekend:
                    i = 1
                    for check_in_out in checkin_checkout:
                        checkin = check_in_out.get('checkin')
                        checkout = check_in_out.get('checkout')
                        if created_attendance.check_in and created_attendance.check_out:
                            if i == 1:
                                actual_checkin = checkin
                            if i == len(checkin_checkout):
                                actual_checkout = checkout
                            total_hours += (checkout - checkin).total_seconds() / 3600.00
                            check_in_out.get('checkin_raw_attendance_id').write({'state': 'processed'})
                            check_in_out.get('checkout_raw_attendance_id').write({'state': 'processed'})
                            i += 1
                    val = {
                        'actual_checkin': actual_checkin,
                        'actual_checkout': actual_checkout,
                        # 'late_hour': 0.0,
                        # 'early_hour': 0.0,
                        # 'missed_effort': 0.0,
                        'paid_leave': 0.0,
                        'unpaid_leave': 0.0,
                        'net_working_days': 0.0,
                        'total_worked_hours': total_hours,
                        'break_hours': 0.0,
                        'extra_hours': total_hours,
                        'mandatory_hours': total_hours,
                        'actual_mandatory_hours': total_hours,
                        'state': "processed"
                    }
                    # self._calculate_event_overtime_type(created_attendance, val)
                else:
                    nwd = 0
                    i = 1
                    actual_mandatory_worked = 0
                    shift_mandatory = 8
                    for check_in_out in checkin_checkout:
                        checkin = check_in_out.get('checkin')
                        checkout = check_in_out.get('checkout')
                        shift_flexible_hours = created_attendance.resource_calendar_id.flexible_break_time or 0
                        break_hours = 1
                        actual_mandatory_worked = 0

                        if created_attendance.check_in and created_attendance.check_out:
                            if i == 1:
                                actual_checkin = checkin
                                shift_total_time = shift_mandatory + break_hours
                                total_mandatory_worked = (checkout - checkin).total_seconds() / 3600.00
                                actual_mandatory_worked = total_mandatory_worked - break_hours

                                if actual_mandatory_worked < shift_mandatory:
                                    missed_hours = shift_mandatory - actual_mandatory_worked
                                elif actual_mandatory_worked > shift_mandatory:
                                    extra_hours = actual_mandatory_worked - shift_mandatory
                                    actual_mandatory_worked = shift_mandatory
                            if i == len(checkin_checkout):
                                actual_checkout = checkout
                            total_hours += (checkout - checkin).total_seconds() / 3600.00
                            check_in_out.get('checkin_raw_attendance_id').write({'state': 'processed'})
                            check_in_out.get('checkout_raw_attendance_id').write({'state': 'processed'})
                            i += 1
                            # if extra_hours:
                            #     self._calculate_over_time(created_attendance, extra_hours, checkout)

                    val = {
                        # 'check_in': actual_checkin,
                        # 'check_out': actual_checkout,
                        'actual_checkin': actual_checkin,
                        'actual_checkout': actual_checkout,
                        'missed_effort': missed_hours,
                        'paid_leave': 0.0,
                        'unpaid_leave': 0.0,
                        'net_working_days': nwd,
                        'total_worked_hours': total_hours,
                        'break_hours': break_hours,
                        'extra_hours': extra_hours,
                        # 'flexible_break_hour': break_hours,
                        # 'used_flexible_break_hour': used_flexible_break_hour,
                        'mandatory_hours': shift_mandatory,
                        'actual_mandatory_hours': actual_mandatory_worked,
                        'state': "processed"
                    }
                    # if created_attendance.is_flexible_day:
                    #     created_attendance.consumed_flexible_day = 1
                created_attendance.write(val)



            # if late_hours:
            #     self._compute_attendance_policy_late(created_attendance, late_hours)
            # self._check_actual_mandatory_hours(created_attendance)

    # def _calculate_over_time(self, created_attendance, extra_hours, checkout):
    #     for rec in created_attendance:
    #         if rec.is_overtime_eligible:
    #             total_ot = extra_hours
    #             ot_types = self.env['hc.over.time.type'].search([('over_time_type', '=', 'time_based')],
    #                                                             order='from_time asc')
    #             n = 0
    #             o_time_one = ''
    #             for ot in ot_types:
    #                 if total_ot > 0:
    #                     ot_from_minutes = ot.from_time * 60
    #                     from_hours, from_minutes = divmod(ot_from_minutes, 60)
    #                     ot_to_minutes = ot.to_time * 60
    #                     to_hours, to_minutes = divmod(ot_to_minutes, 60)
    #                     ot_from = rec.check_in.replace(hour=int(from_hours), minute=int(from_minutes))
    #                     ot_to = rec.check_in.replace(hour=int(to_hours), minute=int(to_minutes))
    #
    #                     if to_hours < from_hours:
    #                         ot_to += relativedelta(days=1)
    #
    #                     ot_from_dt = datetime.strptime(str(ot_from), '%Y-%m-%d %H:%M:%S')
    #                     local = pytz.timezone("Asia/Dubai")
    #                     ot_from_dt_loc = local.localize(ot_from_dt, is_dst=None)
    #                     ot_from_dt_utc_dt = ot_from_dt_loc.astimezone(pytz.utc)
    #                     ot_from_var = ot_from_dt_utc_dt.strftime("%Y-%m-%d %H:%M:%S")
    #
    #                     ot_to_dt = datetime.strptime(str(ot_to), '%Y-%m-%d %H:%M:%S')
    #                     local = pytz.timezone("Asia/Dubai")
    #                     ot_to_dt_loc = local.localize(ot_to_dt, is_dst=None)
    #                     ot_to_dt_utc_dt = ot_to_dt_loc.astimezone(pytz.utc)
    #                     ot_to_var = ot_to_dt_utc_dt.strftime("%Y-%m-%d %H:%M:%S")
    #
    #                     # ot_from_dt = ot_from.replace(tzinfo=pytz.timezone("Asia/Dubai"))
    #                     # ot_to_dt = ot_to.replace(tzinfo=pytz.timezone("Asia/Dubai"))
    #
    #                     # checkin = checkin_dt_utc_dt.strftime("%Y-%m-%d %H:%M:%S")
    #
    #                     local = pytz.timezone("Asia/Dubai")
    #                     naive = datetime.strptime(str(checkout), '%Y-%m-%d %H:%M:%S')
    #                     local_dt = local.localize(naive, is_dst=None)
    #                     local_var = local_dt.strftime("%Y-%m-%d %H:%M:%S")
    #                     utc_dt = local_dt.astimezone(pytz.timezone("Asia/Dubai"))
    #                     utc_dt_tz = utc_dt.replace(tzinfo=UTC).astimezone(pytz.timezone("Asia/Dubai")).replace(
    #                         tzinfo=None)
    #
    #                     ot_field = self.env['ir.model.fields'].search([('id', '=', ot.over_time_id.id)])
    #                     if n == 0:
    #                         o_time_one = ot_field.name
    #                     if extra_hours:
    #                         if ot_from_var <= str(checkout) <= ot_to_var:
    #                             if str(checkout) < ot_to_var:
    #                                 if n == 0:
    #                                     rec.write({str(ot_field.name): total_ot})
    #                                     total_ot = 0
    #                                 elif n == 1:
    #                                     qty_diff = total_ot - (utc_dt_tz - ot_from_dt).total_seconds() / 3600.00
    #                                     rec.write({str(ot_field.name): total_ot - qty_diff})
    #                                     rec.write({str(o_time_one): qty_diff})
    #                                     total_ot = 0
    #                             else:
    #                                 rec.write({str(ot_field.name): (ot_to_dt - ot_from_dt).total_seconds() / 3600.00})
    #                                 total_ot = total_ot - (ot_to_dt - ot_from_dt)
    #                                 delta_total_ot = total_ot.total_seconds() / 3600.00
    #                                 # delta_total_ot = total_ot - (ot_to_dt - ot_from_dt).total_seconds() / 3600.00
    #                     n += 1

    # def _calculate_event_overtime_type(self, created_attendance, val):
    #     for rec in created_attendance:
    #         if rec.is_overtime_eligible and not rec.employee_id.company_id.is_compensatory_off:
    #             total_ot = val.get('total_worked_hours', False)
    #             ot_types = self.env['hc.over.time.type'].search([('over_time_type', '=', 'event_based')])
    #             for ot in ot_types:
    #                 if created_attendance.is_special_holiday and ot.event_type == 'special_holiday':
    #                     ot_field = self.env['ir.model.fields'].search([('id', '=', ot.over_time_id.id)])
    #                     rec.write({str(ot_field.name): total_ot})
    #                 elif created_attendance.public_holiday and ot.event_type == 'public_holiday':
    #                     ot_field = self.env['ir.model.fields'].search([('id', '=', ot.over_time_id.id)])
    #                     rec.write({str(ot_field.name): total_ot})
    #                 elif created_attendance.is_weekend and ot.event_type == 'weekend':
    #                     ot_field = self.env['ir.model.fields'].search([('id', '=', ot.over_time_id.id)])
    #                     rec.write({str(ot_field.name): total_ot})
    #         else:
    #             time_off_type = self.env['hr.leave.type'].search([('is_compensatory_timeoff_type', '=', True)], limit=1)
    #             if time_off_type:
    #                 Allocation = self.env['hr.leave.allocation']
    #                 allocation = Allocation.search(
    #                     [('employee_id', '=', rec.employee_id.id),
    #                      ('holiday_status_id', '=', time_off_type.id),
    #                      ('date_from', '<=', rec.date), ('state', '=', 'draft')])
    #
    #                 if allocation:
    #                     allocation.write({
    #                         'number_of_days': allocation.number_of_days + 1,
    #                     })
    #                 else:
    #                     Allocation.create({
    #                         'employee_id': rec.employee_id.id,
    #                         'name': 'Earned From the Overtime',
    #                         'holiday_status_id': time_off_type.id,
    #                         'allocation_type': 'accrual',
    #                         'date_from': rec.date,
    #                         'number_of_days': 1,
    #                     })

    # def _compute_attendance_policy_late(self, created_attendance, late_hours):
    #     allowed_late_time = created_attendance.branch_id.allowed_late_time
    #     allowed_checkin_from = created_attendance.branch_id.allowed_checkin_from
    #     allowed_checkin_to = created_attendance.branch_id.allowed_checkin_to
    #     checkin = created_attendance.actual_checkin
    #     shift_checkin = created_attendance.check_in
    #     shift_checkout = created_attendance.check_out
    #     checkout = created_attendance.actual_checkout
    #     if late_hours > 0:
    #         if late_hours <= allowed_late_time:
    #             created_attendance.actual_mandatory_hours += late_hours
    #             self.late_checkin_approved = True
    #         if checkin <= (shift_checkin + timedelta(hours=allowed_checkin_to)) and checkout >= (
    #                 shift_checkout + timedelta(hours=allowed_checkin_from)):
    #             created_attendance.actual_mandatory_hours += ((shift_checkin + timedelta(
    #                 hours=allowed_checkin_to)) - shift_checkin).total_seconds() / 3600.00
    #
    #     if late_hours > 0 and (shift_checkin + timedelta(hours=allowed_checkin_from)) <= checkin <= (
    #             shift_checkin + timedelta(
    #         hours=allowed_checkin_to)) and checkout >= (shift_checkout + timedelta(hours=allowed_checkin_from)):
    #         if created_attendance.extra_hours >= allowed_checkin_from:
    #             created_attendance.actual_mandatory_hours += late_hours
    #             if created_attendance.otime_one > 0:
    #                 created_attendance.otime_one = created_attendance.otime_one - allowed_checkin_from

    # def _check_actual_mandatory_hours(self, created_attendance):
    #     if created_attendance.actual_mandatory_hours > created_attendance.mandatory_hours:
    #         created_attendance.actual_mandatory_hours = created_attendance.mandatory_hours
