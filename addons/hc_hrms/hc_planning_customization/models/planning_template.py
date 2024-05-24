# -*- coding: utf-8 -*-

import math

from datetime import datetime, timedelta, time, date
from odoo import api, fields, models, _
from odoo.tools import format_time
from odoo.addons.resource.models.resource import float_to_time
from odoo.exceptions import ValidationError



class PlanningTemplate(models.Model):
    _inherit = "planning.slot.template"

    branch_id = fields.Many2one("hc.branch", string="Branch")
    resource_calendar_id = fields.Many2one('resource.calendar', string='Working Schedule')


