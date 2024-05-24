# -*- coding: utf-8 -*-
from odoo import models, fields


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    bank_category = fields.Selection(
        selection=[
            ('cdc', 'CDC'), ('pdc', 'PDC'),
            ('lc', 'Letter of Credit(LC)'),
            ('bank_transfer', 'Bank Transfer')
        ], string="Bank Category"
    )



