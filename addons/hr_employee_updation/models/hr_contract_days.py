from odoo.exceptions import Warning
from odoo import models, fields, api, _


class HrEmployeeContract(models.Model):
    _inherit = 'hr.contract'

    notice_days = fields.Many2one('notice.period.days', string="Notice Period")
