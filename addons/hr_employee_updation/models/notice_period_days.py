from odoo import models, fields


class NoticePeriodDays(models.Model):
    _name = 'notice.period.days'
    _description = 'Notice Period Days'
    _order = 'id desc'

    name = fields.Char(string="Days", required=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Name must be unique!'),
    ]
