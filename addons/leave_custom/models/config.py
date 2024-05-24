from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class Company(models.Model):
    _inherit = "res.company"

    limit_last_days = fields.Integer(string="Limit Recursive Leave Request days")
    contract_wait_period = fields.Integer(string="Contract Waiting Period")




class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    limit_last_days = fields.Integer(related='company_id.limit_last_days', readonly=False)
    contract_wait_period = fields.Integer(related='company_id.contract_wait_period', readonly=False)
