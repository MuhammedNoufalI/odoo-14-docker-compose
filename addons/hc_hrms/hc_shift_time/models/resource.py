# -*- coding: utf-8 -*-

from datetime import datetime

import pytz
from odoo import api, fields, models, _
# from odoo.addons.hr_payroll.models.resource_calendar import ResourceCalendar as ResourceCalendarInherit
from odoo.addons.resource.models.resource import ResourceCalendar as HcResourceCalendar
from odoo.addons.resource.models.resource import Intervals
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round
from lxml import etree
import simplejson


class HrResourceCalendarAttendance(models.Model):
    _inherit = 'resource.calendar.attendance'

    is_break = fields.Boolean(string="Is Break Time")
    is_check_out_next_day = fields.Boolean('Is Checkout Next Day')
    is_flexible_day = fields.Boolean('Is Flexible Day')
    mandatory_hour = fields.Float(string="Mandatory Hours")
    previous_day_remaining = fields.Boolean("Remaining of Previous Day")

    # flexible_break_time = fields.Float(string="Flexible Break Time")

    @api.onchange('is_break')
    def onchange_work_entry_type(self):
        work_entry_type = self.env['hr.work.entry.type'].search(
            [('is_break', '=', True)], limit=1)
        for rec in self:
            if rec.is_break and work_entry_type:
                rec.work_entry_type_id = work_entry_type.id

    @api.onchange('hour_from', 'hour_to')
    def _onchange_hours(self):
        # return
        if self.is_check_out_next_day:
            self.hour_from = abs(self.hour_from)
            self.hour_to = abs(self.hour_to)
        else:
            # avoid negative or after midnight
            self.hour_from = min(self.hour_from, 23.99)
            self.hour_from = max(self.hour_from, 0.0)
            self.hour_to = min(self.hour_to, 24)
            self.hour_to = max(self.hour_to, 0.0)

            # avoid wrong order
            self.hour_to = max(self.hour_to, self.hour_from)

            # Multiple Break Time Restriction
    # @api.model
    # def create(self, vals):
    #     attendances = self.search(
    #         [('dayofweek', '=', vals['dayofweek']), ('is_break', '=', True), ('calendar_id', '=', vals['calendar_id'])])
    #     if attendances:
    #         raise UserError(_("Break Time is Already Configured for this Day of Week.."))
    #     result = super(HrResourceCalendarAttendance, self).create(vals)
    #     return result


class HrResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    # @api.model
    # def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
    #     res = super(HrResourceCalendar, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
    #                                                      submenu=submenu)
    #     doc = etree.XML(res['arch'])
    #     if view_type == 'form':
    #         for node in doc.xpath("//field"):
    #             modifiers = simplejson.loads(node.get("modifiers"))
    #             if 'readonly' not in modifiers:
    #                 modifiers['readonly'] = [['state', '!=', 'draft']]
    #             else:
    #                 if type(modifiers['readonly']) != bool:
    #                     modifiers['readonly'].insert(0, '|')
    #                     modifiers['readonly'] += [['state', '!=', 'draft']]
    #             node.set('modifiers', simplejson.dumps(modifiers))
    #             res['arch'] = etree.tostring(doc)
    #     return res
    shift_mandatory_hours = fields.Float(string="Shift Mandatory Hours", default=8.0)
    flexible_break_time = fields.Float(string="Flexible Break Time")
    state = fields.Selection(
        [('draft', 'Draft'), ('planned', 'Planned')],
        string='State', copy=False,
        default='draft', compute='_compute_state')

    # hours_per_week = fields.Float(compute="_compute_hours_per_week_test", string="Hours per Week", store=True)

    # def write(self, values):
    #     for record in self:
    #         if record.state == 'planned':
    #             raise ValidationError(_('You are not allowed to edit the planned schedule'))
    #     result = super(HrResourceCalendar, self).write(values)
    #     return result

    def _compute_state(self):
        for rec in self:
            contracts = self.env['hr.contract'].search([('state', '!=', 'cancel')])
            flag = False
            if contracts:
                for contract in contracts:
                    if contract.resource_calendar_id:
                        if contract.resource_calendar_id.id == rec.id:
                            flag = True
            if flag:
                rec.state = 'planned'
            else:
                rec.state = 'draft'

    """ Inherited From Base. """

    def _check_overlap(self, attendance_ids):
        """ attendance_ids correspond to attendance of a week,
            will check for each day of week that there are no superimpose. """
        result = []
        for attendance in attendance_ids.filtered(lambda att: not att.date_from and not att.date_to):
            # 0.000001 is added to each start hour to avoid to detect two contiguous intervals as superimposing.
            # Indeed Intervals function will join 2 intervals with the start and stop hour corresponding.
            if attendance.is_check_out_next_day:
                result.append((int(attendance.dayofweek) * 24 + attendance.hour_from + 0.000001,
                               (bool(attendance.is_check_out_next_day) + int(
                                   attendance.dayofweek)) * 24 + attendance.hour_to, attendance))
            else:
                result.append((int(attendance.dayofweek) * 24 + attendance.hour_from + 0.000001,
                               int(attendance.dayofweek) * 24 + attendance.hour_to, attendance))

        if len(Intervals(result)) != len(result):
            raise ValidationError(_("Attendances can't overlap."))

    # @api.depends('attendance_ids.hour_from', 'attendance_ids.hour_to', 'attendance_ids.work_entry_type_id.is_leave')
    # def _compute_hours_per_week(self):
    #     for calendar in self:
    #         sum_hours = 0
    #         for attendance in calendar.attendance_ids:
    #             if not attendance.work_entry_type_id.is_leave and not attendance.is_check_out_next_day:
    #                 sum_hours = attendance.hour_to - attendance.hour_from
    #             if attendance.is_check_out_next_day and not attendance.work_entry_type_id.is_leave:
    #                 sum_hours = (attendance.hour_to - attendance.hour_from) + 24
    #         calendar.hours_per_week = sum_hours / 2 if calendar.two_weeks_calendar else sum_hours

    # ResourceCalendarInherit._compute_hours_per_week = _compute_hours_per_week

    def _compute_hours_per_day(self, attendances):
        if not attendances:
            return 0

        hour_count = 0.0
        for attendance in attendances:
            if attendance.is_check_out_next_day:
                hour_count += (attendance.hour_to - attendance.hour_from) + 24
            else:
                hour_count += attendance.hour_to - attendance.hour_from

        if self.two_weeks_calendar:
            number_of_days = len(set(attendances.filtered(lambda cal: cal.week_type == '1').mapped('dayofweek')))
            number_of_days += len(set(attendances.filtered(lambda cal: cal.week_type == '0').mapped('dayofweek')))
        else:
            number_of_days = len(set(attendances.mapped('dayofweek')))

        return float_round(hour_count / float(number_of_days), precision_digits=2)

    HcResourceCalendar._compute_hours_per_day = _compute_hours_per_day

class HrResourceCalendarLeaves(models.Model):
    _inherit = 'resource.calendar.leaves'

    date = fields.Date(string="Date")
    is_special_holiday = fields.Boolean(string="Is Special Holiday")

    @api.onchange('date')
    def _onchange_date(self):
        for rec in self:
            if rec.date:
                min_time = datetime.min.time()
                max_time = datetime.max.time()
                date_from_dt = datetime.combine(rec.date, min_time)
                date_to_dt = datetime.combine(rec.date, max_time).replace(second=59, microsecond=0)
                local = pytz.timezone("Asia/Dubai")

                date_from_dt1 = datetime.strptime(str(date_from_dt), '%Y-%m-%d %H:%M:%S')
                date_from_dt_loc = local.localize(date_from_dt1, is_dst=None)
                date_from_utc_dt = date_from_dt_loc.astimezone(pytz.utc)

                date_to_dt1 = datetime.strptime(str(date_to_dt), '%Y-%m-%d %H:%M:%S')
                date_to_dt_loc = local.localize(date_to_dt1, is_dst=None)
                date_to_utc_dt = date_to_dt_loc.astimezone(pytz.utc)

                replaced_date_from = date_from_utc_dt.strftime("%Y-%m-%d %H:%M:%S")
                rec.date_from = replaced_date_from
                replaced_date_to = date_to_utc_dt.strftime("%Y-%m-%d %H:%M:%S")
                rec.date_to = replaced_date_to
