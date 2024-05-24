# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    payment_limit = fields.Float(string="Payment Limit",  required=False, )
