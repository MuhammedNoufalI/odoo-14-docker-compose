from datetime import datetime

from odoo.exceptions import ValidationError
from odoo import _, api, fields, models


class SalaryRules(models.Model):
    _inherit ='hr.salary.rule'

    account_debit = fields.Many2one('account.account', 'Debit Account', company_dependent=False,
                                    domain=[('deprecated', '=', False)])
    account_credit = fields.Many2one('account.account', 'Credit Account', company_dependent=False,
                                     domain=[('deprecated', '=', False)])