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
    custom_attendance_ids = fields.One2many('custom.resource.calendar', 'resource_calendar_id')

class CustomShifts(models.Model):
    _name = 'custom.resource.calendar'
    resource_calendar_id = fields.Many2one('resource.calendar')
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
