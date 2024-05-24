# -*- coding: utf-8 -*-

import datetime
import pytz

from datetime import timedelta
from dateutil import rrule
from dateutil.relativedelta import relativedelta
from operator import itemgetter

from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare

from odoo import models, fields, api ,_
from itertools import groupby
from datetime import timedelta



class WorkingTime(models.Model):
    _inherit = 'resource.calendar'

    public_holiday_ids = fields.One2many('hr.public.holiday', 'holiday_id', string='Public Holidays')
    weekend_ids = fields.Many2many(comodel_name="weekend.days",string="WeekEnd Days")
    work_period = fields.Float(string="Work Period",compute='_get_working_hour',  required=False, )
    attendance_id = fields.Many2one(comodel_name="hr.attendance.structure", string="Attendance Rule", required=False, )



    #@api.multi
    def get_working_intervals_of_day(self, start_dt=None, end_dt=None,
                                     leaves=None, compute_leaves=False, resource_id=None,
                                     default_interval=None):
        """ Get the working intervals of the day based on calendar. This method
        handle leaves that come directly from the leaves parameter or can be computed.

        :param datetime start_dt: datetime object that is the beginning hours
                                  for the working intervals computation; any
                                  working interval beginning before start_dt
                                  will be truncated. If not set, set to end_dt
                                  or today() if no end_dt at 00.00.00.
        :param datetime end_dt: datetime object that is the ending hour
                                for the working intervals computation; any
                                working interval ending after end_dt
                                will be truncated. If not set, set to start_dt()
                                at 23.59.59.
        :param list leaves: a list of tuples(start_datetime, end_datetime) that
                            represent leaves.
        :param boolean compute_leaves: if set and if leaves is None, compute the
                                       leaves based on calendar and resource.
                                       If leaves is None and compute_leaves false
                                       no leaves are taken into account.
        :param int resource_id: the id of the resource to take into account when
                                computing the leaves. If not set, only general
                                leaves are computed. If set, generic and
                                specific leaves are computed.
        :param tuple default_interval: if no id, try to return a default working
                                       day using default_interval[0] as beginning
                                       hour, and default_interval[1] as ending hour.
                                       Example: default_interval = (8, 16).
                                       Otherwise, a void list of working intervals
                                       is returned when id is None.

        :return list intervals: a list of tuples (start_datetime, end_datetime)
                                of work intervals """

        # Computes start_dt, end_dt (with default values if not set) + off-interval work limits
        work_limits = []
        if start_dt is None and end_dt is not None:
            start_dt = end_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        elif start_dt is None:
            start_dt = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            # FORWARD-PORT UP TO SAAS-14
            # Add a strict limit when searching for intervals
            force_start_dt = self.env.context.get('force_start_dt')
            if force_start_dt and force_start_dt < start_dt:
                work_limits.append((force_start_dt.replace(hour=0, minute=0, second=0, microsecond=0), force_start_dt))
            work_limits.append((start_dt.replace(hour=0, minute=0, second=0, microsecond=0), start_dt))
        if end_dt is None:
            end_dt = start_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            work_limits.append((end_dt, end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)))
        assert start_dt.date() == end_dt.date(), 'get_working_intervals_of_day is restricted to one day'

        intervals = []
        work_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)

        # no calendar: try to use the default_interval, then return directly
        if not self:
            working_interval = []
            if default_interval:
                working_interval = (start_dt.replace(hour=default_interval[0], minute=0, second=0, microsecond=0),
                                    start_dt.replace(hour=default_interval[1], minute=0, second=0, microsecond=0))
            intervals = self.interval_remove_leaves(working_interval, work_limits)
            return intervals

        working_intervals = []
        tz_info = fields.Datetime.context_timestamp(self, work_dt).tzinfo
        for calendar_working_day in self.get_attendances_for_weekday(start_dt):
            dt_f = work_dt.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(seconds=(calendar_working_day.hour_from * 3600))
            dt_t = work_dt.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(seconds=(calendar_working_day.hour_to * 3600))

            # adapt tz
            working_interval = (
                dt_f.replace(tzinfo=tz_info).astimezone(pytz.UTC).replace(tzinfo=None),
                dt_t.replace(tzinfo=tz_info).astimezone(pytz.UTC).replace(tzinfo=None),
                calendar_working_day.id
            )

            # FORWARD-PORT UP TO SAAS-14
            # Add a strict limit when searching for intervals (yeah, once again!)
            if self.env.context.get('force_start_dt'):
                for wi in self.interval_remove_leaves(working_interval, work_limits):
                    if wi[0] >= self.env.context['force_start_dt']:
                        working_intervals += [wi]
            else:
                working_intervals += self.interval_remove_leaves(working_interval, work_limits)

        # find leave intervals
        if leaves is None and compute_leaves:
            leaves = self.get_leave_intervals(resource_id=resource_id)

        # filter according to leaves
        for interval in working_intervals:
            work_intervals = self.interval_remove_leaves(interval, leaves)
            intervals += work_intervals

        return intervals

    #@api.one
    @api.depends('attendance_ids.hour_from','attendance_ids.hour_to')
    def _get_working_hour(self):
        interval_data = []
        hours = 0.0
        working_intervals_on_day = self.get_working_intervals_of_day()
        for interval in working_intervals_on_day:
            interval_data.append(interval)
        for interval in interval_data:
            hours += (interval[1] - interval[0]).total_seconds() / 3600.0
        if not hours:
            self.work_period = 8.0
        else:
            self.work_period = hours

    @api.model
    def interval_remove_leaves(self, interval, leave_intervals):
        """ Utility method that remove leave intervals from a base interval:

         - clean the leave intervals, to have an ordered list of not-overlapping
           intervals
         - initiate the current interval to be the base interval
         - for each leave interval:

          - finishing before the current interval: skip, go to next
          - beginning after the current interval: skip and get out of the loop
            because we are outside range (leaves are ordered)
          - beginning within the current interval: close the current interval
            and begin a new current interval that begins at the end of the leave
            interval
          - ending within the current interval: update the current interval begin
            to match the leave interval ending

        :param tuple interval: a tuple (beginning datetime, ending datetime) that
                               is the base interval from which the leave intervals
                               will be removed
        :param list leave_intervals: a list of tuples (beginning datetime, ending datetime)
                                    that are intervals to remove from the base interval
        :return list intervals: a list of tuples (begin datetime, end datetime)
                                that are the remaining valid intervals """
        if not interval:
            return interval
        if leave_intervals is None:
            leave_intervals = []
        intervals = []
        leave_intervals = self.interval_clean(leave_intervals)
        current_interval = [interval[0], interval[1]]
        for leave in leave_intervals:
            if leave[1] <= current_interval[0]:
                continue
            if leave[0] >= current_interval[1]:
                break
            if current_interval[0] < leave[0] < current_interval[1]:
                current_interval[1] = leave[0]
                intervals.append((current_interval[0], current_interval[1]))
                current_interval = [leave[1], interval[1]]
            if current_interval[0] <= leave[1]:
                current_interval[0] = leave[1]
        if current_interval and current_interval[0] < interval[1]:  # remove intervals moved outside base interval due to leaves
            intervals.append((current_interval[0], current_interval[1]))
        return intervals

    def interval_clean(self, intervals):
        """ Utility method that sorts and removes overlapping inside datetime
        intervals. The intervals are sorted based on increasing starting datetime.
        Overlapping intervals are merged into a single one.

        :param list intervals: list of intervals; each interval is a tuple
                               (datetime_from, datetime_to)
        :return list cleaned: list of sorted intervals without overlap """
        intervals = sorted(intervals, key=itemgetter(0))  # sort on first datetime
        cleaned = []
        working_interval = None
        while intervals:
            current_interval = intervals.pop(0)
            if not working_interval:  # init
                working_interval = [current_interval[0], current_interval[1]]
            elif working_interval[1] < current_interval[0]:  # interval is disjoint
                cleaned.append(tuple(working_interval))
                working_interval = [current_interval[0], current_interval[1]]
            elif working_interval[1] < current_interval[1]:  # union of greater intervals
                working_interval[1] = current_interval[1]
        if working_interval:  # handle void lists
            cleaned.append(tuple(working_interval))
        return cleaned




    #@api.multi
    def get_attendances_for_weekday(self, day_dt):
        """ Given a day datetime, return matching attendances """
        self.ensure_one()
        weekday = day_dt.weekday()
        attendances = self.env['resource.calendar.attendance']

        for attendance in self.attendance_ids.filtered(
            lambda att:
                int(att.dayofweek) == weekday and
                not (att.date_from and fields.Date.from_string(att.date_from) > day_dt.date()) and
                not (att.date_to and fields.Date.from_string(att.date_to) < day_dt.date())):
            attendances |= attendance
        return attendances




class WeekEndDays(models.Model):
    _name = 'weekend.days'
    _rec_name = 'dayofweek'
    dayofweek = fields.Selection([
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday')
    ], 'Day of Week', required=True, index=True, default='Monday')
