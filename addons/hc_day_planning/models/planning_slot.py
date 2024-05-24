from odoo import api, fields, models, _
from datetime import date, datetime

class Planning(models.Model):
    _inherit = "planning.slot"

    day_of_week = fields.Selection([('0', 'Monday'),
                                   ('1', 'Tuesday'),
                                   ('2', 'Wednesday'),
                                   ('3', 'Thursday'),
                                   ('4', 'Friday'),
                                   ('5', 'Saturday'),
                                   ('6', 'Sunday')], string='Day of Week',compute="compute_day_of_week")
    template_id = fields.Many2one('planning.slot.template', string='Shift Templates', compute='_compute_template_id', readonly=False, store=True,required=True)


    @api.depends('start_datetime')
    def compute_day_of_week(self):
        for rec in self:
            days = ['0','1', '2', '3', '4', '5', '6']
            weekday = rec.end_datetime.weekday()
            rec.day_of_week = str(days[weekday])

    def create_employees(self):
        contracts = self.env['hr.contract'].search([('state', '=', 'open')])
        today = fields.Date.today()
        template = self.env['planning.slot.template'].search([], limit=1)
        if contracts:
            for contract in contracts:
                self.create({'template_id': template.id,
                             'company_id': contract.company_id.id,
                             'employee_id': contract.employee_id.id,
                             'start_datetime': datetime(today.year, today.month, 1, 8, 0),
                             'end_datetime': datetime(today.year, today.month, 1, 17, 0),
                             })
        else:
            return







