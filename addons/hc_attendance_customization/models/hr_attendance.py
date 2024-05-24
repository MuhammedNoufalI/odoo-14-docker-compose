from datetime import datetime, time, timedelta

import pytz
import time
from odoo import fields, models, api


# calculate attendance duration
class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    def approve_shift_time(self):
        for rec in self:
            if rec.mandatory_hours:
                rec.actual_mandatory_hours = rec.mandatory_hours


class HcRawAttendance(models.Model):
    _inherit = "hc.raw.attendance"

    def open_exception(self):
        [action] = self.env.ref('hc_shift_time.action_hc_attendance_exceptions').read()
        action['domain'] = [('id', '=', self.exception_id.id)]
        return action
