# -*- coding: utf-8 -*-

from collections import namedtuple
import json
import time

from odoo.fields import Date, Datetime
from itertools import groupby
from odoo import api, fields, models, _
from datetime import datetime,date
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError
from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES

class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'
    is_bank_count = fields.Boolean(string='Bank')
    bank_journal_id = fields.Many2one('account.journal',
                                      string='Bank Journal',
                                      domain=[('type', '=', 'bank')],
                                      ondelete='restrict',
                                      help='The payment method is of type bank. A bank statement will be automatically generated.')

    commission_percent = fields.Float('Commission Percent(%)')
    commission_account = fields.Many2one('account.account','Commission Account')
    activate_commission = fields.Boolean('Activate Commission')
    @api.onchange('is_bank_count')
    def _onchange_is_bank_count(self):
        if not self.is_bank_count:
            self.bank_journal_id = False
            self.activate_commission = False
        else:
            if self.is_cash_count:
                self.is_bank_count = False
                warning = {
                    'message': "You Can't Choose Bank and Cash Selection at same time"
                }
                return {'warning': warning}
    @api.onchange('is_cash_count')
    def _onchange_cash_count(self):
        if self.is_cash_count:
            if self.is_bank_count:
                self.is_cash_count = False
                warning = {
                    'message': "You Can't Choose Bank and Cash Selection at same time"
                }
                return {'warning': warning}