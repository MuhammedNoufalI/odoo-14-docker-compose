from odoo import api, fields, models, _
import math
from datetime import datetime, timedelta, time, date
from odoo import api, fields, models, _
from odoo.tools import format_time
from odoo.addons.resource.models.resource import float_to_time
from odoo.exceptions import ValidationError


class PlanningTemplate(models.Model):
    _inherit = "planning.slot.template"

    shift_mandatory_hours = fields.Float(string="Shift Mandatory Hours", default=8.0)
    flexible_break_time = fields.Float(string="Flexible Break Time", default=1)
    is_check_out_next_day = fields.Boolean('Is Checkout Next Day')
    duration = fields.Float('Duration (Hours)', default=9, group_operator=None)
    is_week_day = fields.Boolean('Is Week Day')

    @api.model
    def create(self, vals):
        print('vals')
        if 'is_week_day' in vals:
            vals['name'] = vals['name'].upper()
        return super(PlanningTemplate, self).create(vals)

    def name_get(self):
        result = []
        for shift_template in self:
            if shift_template.is_week_day:
                name = "DAY OFF"
            else:
                start_time = time(hour=int(shift_template.start_time),
                                  minute=round(math.modf(shift_template.start_time)[0] / (1 / 60.0)))
                duration = shift_template._get_duration()
                end_time = datetime.combine(date.today(), start_time) + duration
                name = '%s - %s %s %s' % (
                    format_time(shift_template.env, start_time, time_format='short').replace(':00 ', ' '),
                    format_time(shift_template.env, end_time.time(), time_format='short').replace(':00 ', ' '),
                    _('(%s days span)') % (duration.days + 1) if duration.days > 0 else '',
                    shift_template.role_id.name if shift_template.role_id.name is not False else ''
                )
            result.append([shift_template.id, name])
        return result



