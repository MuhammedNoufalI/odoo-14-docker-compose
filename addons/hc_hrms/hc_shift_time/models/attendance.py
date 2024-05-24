# -*- coding: utf-8 -*-

from datetime import datetime, time, timedelta

import pytz
import time
from dateutil.relativedelta import relativedelta
from odoo import fields, models, api
from pytz import UTC
import pandas as pd


# calculate attendance duration
class HrAttendanceDuration(models.Model):
    _name = "hr.attendance"
    _inherit = ['hr.attendance', 'mail.thread']

    actual_mandatory_hours = fields.Float(string="Actual Mandatory Hours",
                                          tracking=True)  # ,compute='_compute_mandatory_hours'
    mandatory_hours = fields.Float(string="Shift Mandatory Hours", tracking=True)  # ,compute='_compute_mandatory_hours'
    extra_hours = fields.Float(string="Extra Hours", tracking=True)
    break_hours = fields.Float(string="Break Hours", tracking=True)
    total_worked_hours = fields.Float(string="Total Worked Hours", tracking=True)
    resource_calendar_id = fields.Many2one('resource.calendar', string="Working Time", tracking=True)
    contract_id = fields.Many2one('hr.contract', string="Contract", tracking=True)
    branch_id = fields.Many2one('hc.branch', string="Branch", tracking=True)
    date = fields.Date(string="Date", help='Date of the Checkin', tracking=True)
    actual_checkin = fields.Datetime(string="Actual Check In", tracking=True)
    actual_checkout = fields.Datetime(string="Actual Check Out", tracking=True)
    late_hour = fields.Float(string="Late Hours", tracking=True)
    early_hour = fields.Float(string="Early Hours", tracking=True)
    flexible_break_hour = fields.Float(string="Shift Flexible Break Hours",
                                       help="Flexible Break Hours Allowed in the Shift", tracking=True)
    used_flexible_break_hour = fields.Float(string="Used Flexible Break Hours", tracking=True)
    missed_effort = fields.Float(string="Missed Hours", tracking=True)
    otime_one = fields.Float(string="T1", store=True, tracking=True)
    otime_two = fields.Float(string="T2", tracking=True)
    otime_three = fields.Float(string="T3", tracking=True)
    otime_four = fields.Float(string="T4", tracking=True)
    otime_five = fields.Float(string="T5", tracking=True)
    public_holiday = fields.Boolean(string="Public Holiday", tracking=True)
    is_special_holiday = fields.Boolean(string="Special Holiday", tracking=True)
    is_weekend = fields.Boolean(string="Weekend", tracking=True)
    absent = fields.Boolean(string="Absent", tracking=True)
    time_off = fields.Boolean(string="Is Leave", tracking=True)
    leave_id = fields.Many2one('hr.leave', string="Leave", tracking=True)
    paid_leave = fields.Boolean(string="Paid Leave", tracking=True)
    unpaid_leave = fields.Boolean(string="UnPaid Leave", tracking=True)
    is_flexible_day = fields.Boolean('Is Flexible Day')
    consumed_flexible_day = fields.Boolean('Flexible Day Consumed', tracking=True, default=False)
    halfday_leave = fields.Boolean(string="Half Day Leave", tracking=True)
    net_working_days = fields.Float(string="Net Working Days", tracking=True, default=1)
    is_weekend_special_pay = fields.Boolean(string="Weekend Special Pay", tracking=True)
    annual_leave = fields.Boolean(string="Annual Leave", tracking=True)
    is_overtime_eligible = fields.Boolean(string="Is OverTime Eligible", tracking=True)
    is_missed_punch = fields.Boolean(string="Missed Punch", help='Missed the Punch and Create from the Exception',
                                     tracking=True)
    payroll_period_id = fields.Many2one('hc.payroll.period', string="Payroll Period", tracking=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('processed', 'Processed'), ('submit', 'Submitted'), ('confirmed', 'Confirmed')],
        string='State', tracking=True, copy=False,
        default='draft')
    exception_id = fields.Many2one('hc.attendance.exception', string="Exception Id", tracking=True)
    raw_attendance_id = fields.Many2one('hc.raw.attendance', string="Raw Attendance", tracking=True)

    #Initial Server action for updating
    def update_leave(self):
        for rec in self:
            leave_records = self.env['hr.leave'].search([('employee_id', '=', rec.employee_id.id),('state', '=', 'validate'),('request_date_from', '<=', rec.date),
                                                         ('request_date_to', '>=', rec.date)])
            if leave_records:
                rec.time_off = True
                for leave in leave_records:
                    if leave.holiday_status_id.is_annual_leave:
                        rec.annual_leave = True
                        rec.paid_leave = True
                    elif leave.holiday_status_id.is_unpaid_leave:
                        rec.unpaid_leave = True
                    elif leave.holiday_status_id.is_sick_leave:
                        rec.paid_leave = True
                    elif leave.holiday_status_id.is_shift_weekday_leave:
                        rec.is_weekend = True


# Call the function to execute when the server action is triggered

    @api.model_create_multi
    def create(self, vals):
        for rec in vals:
            payroll_period = self.env['hc.payroll.period'].search([('date_to', '>=', rec['date']),
                                                                   ('date_from', '<=', rec['date'])], limit=1)
            if payroll_period:
                rec['payroll_period_id'] = payroll_period.id
        return super(HrAttendanceDuration, self).create(vals)

    @api.onchange('date')
    def _onchange_date_payroll_period(self):
        for rec in self:
            payroll_period = self.env['hc.payroll.period'].search([('date_to', '>=', rec.date),
                                                                   ('date_from', '<=', rec.date)], limit=1)
            if payroll_period:
                rec.payroll_period_id = payroll_period.id
            else:
                rec.payroll_period_id = False

    def create_daily_attendance(self):
        """
             Creates the Attendances For Each Employee For a Day. (Schedule Action).

             """
        employees = self.env['hr.employee'].sudo().search([])
        day = fields.Datetime.now() + timedelta(hours=4)
        date = day.date()
        created_attendance_ids = self.env['hr.attendance'].sudo().search([('employee_id', 'in', [x.id for x in employees]),
                                                                   ('date', '=', date)])
        today = fields.Datetime.today()

        day = today.weekday()
        is_flexible = False
        is_week_day = False
        shifts = {emp.id: {'id': emp.id, 'shift': [], 'contract_id': '', 'calendar_id': '', 'date': today,
                           'is_ot_eligible': False, 'is_flexible_day': is_flexible, 'is_week_day': is_week_day,
                           'branch_id': emp.branch_id.id}
                  for emp in employees}
        new_shifts = []
        contracts = self.env['hr.contract'].sudo().search([('state', 'in', ['open', 'probation'])],order="id desc")
        print('contracts', contracts)

        for contract in contracts:
            if contract.employee_id.active == True and contract.struct_id.is_attendance_based:
                print('adadfasfasd', contract.name, contract.employee_id.name)
                # for contract in employees.contract_ids.filtered(lambda emp: emp.state == 'open' or 'probation'):
                res_calendar_id = contract.resource_calendar_id
                min_time = datetime.min.time()
                max_time = datetime.max.time()
                date_from_dt = datetime.combine(today, datetime.min.time())
                date_to_dt = datetime.combine(today, datetime.max.time()).replace(second=59, microsecond=0)
                slot_id = self.env['planning.slot'].search([
                    ('employee_id', '=', contract.employee_id.id),
                    ('start_datetime', '>=', date_from_dt),  # Start of today
                    ('end_datetime', '<=', date_to_dt)  # End of today
                ])  # is_published
                is_week_day = False
                list_1 = []
                if slot_id:
                    if slot_id.template_id.is_week_day:
                        is_week_day = True
                    shift_from = slot_id.start_datetime + timedelta(hours=4)
                    shift_to = slot_id.start_datetime + timedelta(hours=int(slot_id.template_id.duration)) + timedelta(hours=4)
                    # if slot_id.template_id.is_check_out_next_day:
                    #     shift_to += relativedelta(days=1)
                    list_1.append((str(shift_from), str(shift_to)))
                else:
                    for shift in contract.resource_calendar_id.attendance_ids:
                        dow = int(shift.dayofweek)
                        if dow == day:
                            shift_from_minutes = shift.hour_from * 60
                            from_hours, from_minutes = divmod(shift_from_minutes, 60)
                            shift_from = today.replace(hour=int(from_hours), minute=int(from_minutes))
                            shift_to_minutes = shift.hour_to * 60
                            to_hours, to_minutes = divmod(shift_to_minutes, 60)
                            shift_to = today.replace(hour=int(to_hours), minute=int(to_minutes))
                            if shift.hour_to < shift.hour_from and shift.is_check_out_next_day:
                                shift_to += relativedelta(days=1)
                            list_1.append((str(shift_from), str(shift_to)))
                            if shift.is_flexible_day:
                                is_flexible = True
                shifts[contract.employee_id.id]['id'] = contract.employee_id.id
                shifts[contract.employee_id.id]['shift'] = list_1
                shifts[contract.employee_id.id]['contract_id'] = contract.id or False
                shifts[contract.employee_id.id]['calendar_id'] = res_calendar_id.id or False
                shifts[contract.employee_id.id]['is_ot_eligible'] = contract.is_overtime_eligible
                shifts[contract.employee_id.id]['is_flexible'] = is_flexible
                shifts[contract.employee_id.id]['is_week_day'] = is_week_day
                shifts[contract.employee_id.id]['branch_id'] = contract.employee_id.branch_id.id or False
                new_shifts.append(shifts[contract.employee_id.id])
                print('new shif231231223t', new_shifts)

            else:
                print('new shift2', new_shifts)


        'Creating Attendance With the Fetched Employee and His Shifts.'
        print('new shift', new_shifts)
        for shift in new_shifts:
            hr_attendance = self.env['hr.attendance']
            public_holiday = False
            special_holiday = False
            weekend = False
            time_off = False
            leave = False
            annual_leave = False
            weekend_special_pay = False
            unpaid_leave = 0
            actual_mandatory_hours = 0
            total_worked_hour = 0
            state = 'draft'
            nwd = 0
            if shift and not shift['id'] in [attendance.employee_id.id for attendance in created_attendance_ids]:
                if shift.get('shift'):
                    checkin_dt = datetime.strptime(shift.get('shift')[0][0], "%Y-%m-%d %H:%M:%S") or None
                    checkout_dt = datetime.strptime(shift.get('shift')[-1][-1], "%Y-%m-%d %H:%M:%S") or None
                    local = pytz.timezone("Asia/Dubai")
                    checkin_dt_loc = local.localize(checkin_dt, is_dst=None)
                    checkin_dt_utc_dt = checkin_dt_loc.astimezone(pytz.utc)
                    checkin = checkin_dt_utc_dt.strftime("%Y-%m-%d %H:%M:%S")

                    checkout_dt_loc = local.localize(checkout_dt, is_dst=None)
                    checkout_dt_utc_dt = checkout_dt_loc.astimezone(pytz.utc)
                    checkout = checkout_dt_utc_dt.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    actual_mandatory_hours = 8
                    total_worked_hour = 8
                    weekend = True
                    state = 'processed'
                    # checkin = datetime(0)
                    # checkout = 0
                    checkin = pytz.timezone("Asia/Dubai").localize(
                        datetime.combine(fields.Date.today(), datetime.min.time())).astimezone(UTC).replace(tzinfo=None)
                    checkout = pytz.timezone("Asia/Dubai").localize(
                        datetime.combine(fields.Date.today(), datetime.min.time())).astimezone(UTC).replace(tzinfo=None)
                public_holidays = self.env['resource.calendar.leaves'].search([('date', '=', fields.Date.today())])
                leaves = self.env['hr.leave'].search(
                    [('request_date_to', '>=', fields.Date.today()), ('request_date_from', '<=', fields.Date.today()),
                     ('employee_id', '=', shift.get('id')), ('state', '=', 'validate')], limit=1)
                for leave_id in leaves:
                    if leave_id:
                        leave = leave_id.id
                    if not leave_id.holiday_status_id.include_to_net_working:
                        nwd = 1
                    if leave_id.holiday_status_id.is_annual_leave:
                        annual_leave = True
                        # unpaid_leave = True
                    # if leave_id.holiday_status_id.is_shift_weekday_leave:
                    #     weekend = True
                    else:
                        time_off = True
                for holiday in public_holidays:
                    if holiday:
                        weekend = False
                        public_holiday = True
                    if holiday.is_special_holiday:
                        special_holiday = True
                        public_holiday = False
                branch = self.env['hc.branch'].browse(shift.get('branch_id'))
                if branch.is_weekend_special_pay:
                    if shift.get('date').weekday() == 4:
                        weekend_special_pay = True
                attendance = hr_attendance.create({
                    'employee_id': shift.get('id'),
                    'contract_id': shift.get('contract_id'),
                    'resource_calendar_id': shift.get('calendar_id'),
                    'branch_id': shift.get('branch_id') or False,
                    'date': shift.get('date'),
                    'is_overtime_eligible': shift.get('is_ot_eligible'),
                    'is_flexible_day': shift.get('is_flexible'),
                    'check_in': checkin,
                    'check_out': checkout,
                    'public_holiday': public_holiday,
                    'is_special_holiday': special_holiday,
                    'is_weekend': weekend,
                    'annual_leave': annual_leave,
                    'unpaid_leave': unpaid_leave,
                    'time_off': time_off,
                    'leave_id': leave,
                    'net_working_days': nwd,
                    'is_weekend_special_pay': weekend_special_pay,
                    'mandatory_hours': 8,
                    'actual_mandatory_hours': actual_mandatory_hours,
                    'state': state,
                })
                # if shift.get('is_week_day'):
                #     self.update_weekend_mandatory_hour(attendance)
                for leave_id in leaves:
                    if leave_id.state == 'validate':
                        self.update_mandatory_hour_on_leave(leave_id, attendance)
        return
    def create_period_attendance(self):
        """
             Creates the Attendances For Each Employee For a Day. (Schedule Action).

             """
        employees = self.env['hr.employee'].sudo().search([])
        start_date = datetime(2023, 12, 14)
        end_date = datetime(2024, 1, 1)
        # date_format = "%Y-%m-%d"
        # start_date = datetime.strptime(start_date,date_format)
        # end_date = datetime.strptime(end_date,date_format)
        # Iterate through each day in the range:
        for date in pd.date_range(start_date, end_date):
            created_attendance_ids = self.env['hr.attendance'].sudo().search([('employee_id', 'in', [x.id for x in employees]),
                                                                   ('date', '=', date)])
            today = date

            day = today.weekday()
            is_flexible = False
            is_week_day = False
            shifts = {emp.id: {'id': emp.id, 'shift': [], 'contract_id': '', 'calendar_id': '', 'date': today,
                               'is_ot_eligible': False, 'is_flexible_day': is_flexible, 'is_week_day': is_week_day,
                               'branch_id': emp.branch_id.id}
                      for emp in employees}
            new_shifts = []
            contracts = self.env['hr.contract'].sudo().search([('state', 'in', ['open', 'probation'])],order="id desc")
            print('contracts', contracts)

            for contract in contracts:
                if contract.employee_id.active == True and contract.struct_id.is_attendance_based:
                    print('adadfasfasd', contract.name, contract.employee_id.name)
                    # for contract in employees.contract_ids.filtered(lambda emp: emp.state == 'open' or 'probation'):
                    res_calendar_id = contract.resource_calendar_id
                    min_time = datetime.min.time()
                    max_time = datetime.max.time()
                    date_from_dt = datetime.combine(today, datetime.min.time())
                    date_to_dt = datetime.combine(today, datetime.max.time()).replace(second=59, microsecond=0)
                    slot_id = self.env['planning.slot'].search([
                        ('employee_id', '=', contract.employee_id.id),
                        ('start_datetime', '>=', date_from_dt),  # Start of today
                        ('end_datetime', '<=', date_to_dt)  # End of today
                    ])  # is_published
                    is_week_day = False
                    list_1 = []
                    if slot_id:
                        if slot_id.template_id.is_week_day:
                            is_week_day = True
                        shift_from = slot_id.start_datetime + timedelta(hours=4)
                        shift_to = slot_id.start_datetime + timedelta(hours=int(slot_id.template_id.duration)) + timedelta(hours=4)
                        # if slot_id.template_id.is_check_out_next_day:
                        #     shift_to += relativedelta(days=1)
                        list_1.append((str(shift_from), str(shift_to)))
                    else:
                        for shift in contract.resource_calendar_id.attendance_ids:
                            dow = int(shift.dayofweek)
                            if dow == day:
                                shift_from_minutes = shift.hour_from * 60
                                from_hours, from_minutes = divmod(shift_from_minutes, 60)
                                shift_from = today.replace(hour=int(from_hours), minute=int(from_minutes))
                                shift_to_minutes = shift.hour_to * 60
                                to_hours, to_minutes = divmod(shift_to_minutes, 60)
                                shift_to = today.replace(hour=int(to_hours), minute=int(to_minutes))
                                if shift.hour_to < shift.hour_from and shift.is_check_out_next_day:
                                    shift_to += relativedelta(days=1)
                                list_1.append((str(shift_from), str(shift_to)))
                                if shift.is_flexible_day:
                                    is_flexible = True
                    shifts[contract.employee_id.id]['id'] = contract.employee_id.id
                    shifts[contract.employee_id.id]['shift'] = list_1
                    shifts[contract.employee_id.id]['contract_id'] = contract.id or False
                    shifts[contract.employee_id.id]['calendar_id'] = res_calendar_id.id or False
                    shifts[contract.employee_id.id]['is_ot_eligible'] = contract.is_overtime_eligible
                    shifts[contract.employee_id.id]['is_flexible'] = is_flexible
                    shifts[contract.employee_id.id]['is_week_day'] = is_week_day
                    shifts[contract.employee_id.id]['branch_id'] = contract.employee_id.branch_id.id or False
                    new_shifts.append(shifts[contract.employee_id.id])
                    print('new shif231231223t', new_shifts)

                else:
                    print('new shift2', new_shifts)


            'Creating Attendance With the Fetched Employee and His Shifts.'
            print('new shift', new_shifts)
            for shift in new_shifts:
                hr_attendance = self.env['hr.attendance']
                public_holiday = False
                special_holiday = False
                weekend = False
                time_off = False
                leave = False
                annual_leave = False
                weekend_special_pay = False
                unpaid_leave = 0
                actual_mandatory_hours = 0
                total_worked_hour = 0
                state = 'draft'
                nwd = 0
                if shift and not shift['id'] in [attendance.employee_id.id for attendance in created_attendance_ids]:
                    if shift.get('shift'):
                        checkin_dt = datetime.strptime(shift.get('shift')[0][0], "%Y-%m-%d %H:%M:%S") or None
                        checkout_dt = datetime.strptime(shift.get('shift')[-1][-1], "%Y-%m-%d %H:%M:%S") or None
                        local = pytz.timezone("Asia/Dubai")
                        checkin_dt_loc = local.localize(checkin_dt, is_dst=None)
                        checkin_dt_utc_dt = checkin_dt_loc.astimezone(pytz.utc)
                        checkin = checkin_dt_utc_dt.strftime("%Y-%m-%d %H:%M:%S")

                        checkout_dt_loc = local.localize(checkout_dt, is_dst=None)
                        checkout_dt_utc_dt = checkout_dt_loc.astimezone(pytz.utc)
                        checkout = checkout_dt_utc_dt.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        actual_mandatory_hours = 8
                        total_worked_hour = 8
                        weekend = True
                        state = 'processed'
                        # checkin = datetime(0)
                        # checkout = 0
                        checkin = pytz.timezone("Asia/Dubai").localize(
                            datetime.combine(date, datetime.min.time())).astimezone(UTC).replace(tzinfo=None)
                        checkout = pytz.timezone("Asia/Dubai").localize(
                            datetime.combine(date, datetime.min.time())).astimezone(UTC).replace(tzinfo=None)
                    public_holidays = self.env['resource.calendar.leaves'].search([('date', '=', date)])
                    leaves = self.env['hr.leave'].search(
                        [('request_date_to', '>=', date), ('request_date_from', '<=', date),
                         ('employee_id', '=', shift.get('id')), ('state', '=', 'validate')], limit=1)
                    for leave_id in leaves:
                        if leave_id:
                            leave = leave_id.id
                        if not leave_id.holiday_status_id.include_to_net_working:
                            nwd = 1
                        if leave_id.holiday_status_id.is_annual_leave:
                            annual_leave = True
                            # unpaid_leave = True
                        # if leave_id.holiday_status_id.is_shift_weekday_leave:
                        #     weekend = True
                        else:
                            time_off = True
                    for holiday in public_holidays:
                        if holiday:
                            weekend = False
                            public_holiday = True
                        if holiday.is_special_holiday:
                            special_holiday = True
                            public_holiday = False
                    branch = self.env['hc.branch'].browse(shift.get('branch_id'))
                    if branch.is_weekend_special_pay:
                        if shift.get('date').weekday() == 4:
                            weekend_special_pay = True
                    attendance = hr_attendance.create({
                        'employee_id': shift.get('id'),
                        'contract_id': shift.get('contract_id'),
                        'resource_calendar_id': shift.get('calendar_id'),
                        'branch_id': shift.get('branch_id') or False,
                        'date': shift.get('date'),
                        'is_overtime_eligible': shift.get('is_ot_eligible'),
                        'is_flexible_day': shift.get('is_flexible'),
                        'check_in': checkin,
                        'check_out': checkout,
                        'public_holiday': public_holiday,
                        'is_special_holiday': special_holiday,
                        'is_weekend': weekend,
                        'annual_leave': annual_leave,
                        'unpaid_leave': unpaid_leave,
                        'time_off': time_off,
                        'leave_id': leave,
                        'net_working_days': nwd,
                        'is_weekend_special_pay': weekend_special_pay,
                        'mandatory_hours': 8,
                        'actual_mandatory_hours': actual_mandatory_hours,
                        'state': state,
                    })
                    # if shift.get('is_week_day'):
                    #     self.update_weekend_mandatory_hour(attendance)
                    for leave_id in leaves:
                        if leave_id.state == 'validate':
                            self.update_mandatory_hour_on_leave(leave_id, attendance)
        return

    def update_weekend_mandatory_hour(self):
        self.write({'mandatory_hours': 8,
                          'actual_mandatory_hours': 8,
                          'is_weekend': True,
                          'paid_leave': True,
                          'state': 'processed'})
        return
    def update_weekend_mandatory_hour_action(self):
        for rec in self:
            if (rec.state == 'draft' and
                    not(rec.public_holiday or rec.is_special_holiday or rec.is_weekend or rec.time_off or rec.paid_leave or rec.unpaid_leave)):
                rec.write({'mandatory_hours': 8,
                                  'actual_mandatory_hours': 8,
                                  'is_weekend': True,
                                  'paid_leave': True,
                                  'state': 'processed'})
        return
    def update_mandatory_hour_on_leave(self, leave_id, attendance):
        mandatory_hour = 8
        paid_leave = False
        halfday_leave = False
        unpaid_leave = False
        if leave_id.holiday_status_id.pay_type == 'paid':
            mandatory_hour = mandatory_hour
            paid_leave = True
        elif leave_id.holiday_status_id.pay_type == 'half_paid':
            mandatory_hour = mandatory_hour / 2
            halfday_leave = True
        elif leave_id.holiday_status_id.pay_type == 'unpaid':
            mandatory_hour = 8
            unpaid_leave = True
        attendance.write({'mandatory_hours': mandatory_hour,
                          'actual_mandatory_hours': mandatory_hour,
                          'paid_leave': paid_leave,
                          'halfday_leave': halfday_leave,
                          'unpaid_leave': unpaid_leave,
                          'state': 'processed'})
        return 

    # def compute_mandatory_hours(self, created_attendance):
    #     shift_break_hours = 0
    #     shift_mandatory_hours = 0
    #     shift_flexible_hours = created_attendance.resource_calendar_id.flexible_break_time
    #     break_time = created_attendance.resource_calendar_id.attendance_ids.filtered(
    #         lambda x: x.is_break and x.dayofweek == str(created_attendance.date.weekday()))
    #     break_from_times = []
    #     break_to_times = []
    #     if created_attendance.check_in and created_attendance.check_out:
    #         if break_time:
    #             for bt in break_time:
    #                 dow = int(bt.dayofweek)
    #                 day = created_attendance.check_in.date().weekday()
    #                 if dow == day:
    #                     break_time_from_minutes = bt.hour_from * 60
    #                     break_from_hours, break_from_minutes = divmod(break_time_from_minutes, 60)
    #                     break_time_to_minutes = bt.hour_to * 60
    #                     break_to_hours, break_to_minutes = divmod(break_time_to_minutes, 60)
    #                     shift_break_from = created_attendance.check_in.replace(hour=int(break_from_hours),
    #                                                                            minute=int(
    #                                                                                break_from_minutes)) - timedelta(
    #                         hours=4)
    #                     shift_break_to = created_attendance.check_in.replace(hour=int(break_to_hours),
    #                                                                          minute=int(
    #                                                                              break_to_minutes)) - timedelta(
    #                         hours=4)
    #
    #                     if shift_break_hours == 0:
    #                         shift_break_hours = shift_break_to - shift_break_from
    #                     else:
    #                         shift_break_hours += (shift_break_to - shift_break_from)
    #
    #                     break_from_times.append(shift_break_from)
    #                     break_to_times.append(shift_break_to)
    #
    #     if shift_break_hours:
    #         shift_mandatory_hours = (created_attendance.check_out - created_attendance.check_in - shift_break_hours).total_seconds() / 3600.00 - shift_flexible_hours
    #     else:
    #         shift_mandatory_hours = (created_attendance.check_out - created_attendance.check_in).total_seconds() / 3600.00 - shift_flexible_hours
    #
    #     return shift_mandatory_hours
