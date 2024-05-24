
from odoo import api, fields, models


class HrContract(models.Model):
    _inherit = 'hr.contract'

    ticket_entitlement = fields.Selection([('365', '365'),
                                           ('730', '730'),('na', 'NA')], default='365', string='Ticket Entitlement')
