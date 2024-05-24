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

# class AccountPayment(models.Model):
#     _inherit = 'account.payment'
#
#     def _prepare_payment_moves(self):
#         res = super(AccountPayment, self)._prepare_payment_moves()
#         if self.env.context.get('acc_id'):
#             if res:
#                 for x in res[0].get('line_ids'):
#                     dic = x[2]
#                     if dic.get('credit')>0:
#                         x[2].update({'account_id':self.env.context.get('acc_id')})
#         return res


class Accountbanks(models.Model):
    _inherit = 'account.bank.statement.line'
    @api.model
    def create(self,vals):
        new_record = super(Accountbanks, self).create(vals)
        return new_record


class PosSession(models.Model):
    _inherit = 'pos.session'

    bank_move = fields.Many2one('account.move')
    bank_move_ids = fields.Many2many('account.move')

    def _create_account_move(self):
        super(PosSession, self)._create_account_move()
        bank_payments = self.order_ids.payment_ids.filtered(lambda x:x.payment_method_id.is_bank_count==True)
        bank_methods = bank_payments.mapped('payment_method_id')
        aml2 = self.env['account.move.line']

        if bank_payments:
            if not self.bank_move_ids:
                for bank_method in bank_methods:
                    bank_journal = bank_method.bank_journal_id
                    amount = sum(bank_payments.filtered(lambda x:x.payment_method_id == bank_method).mapped('amount'))
                    payment = self.env['account.payment'].create({'payment_type':'inbound',
                                                        'partner_type':'customer',
                                                        'journal_id':bank_journal.id,
                                                        'amount':amount,
                                                        'currency_id':bank_payments[0].currency_id.id,
                                                        'payment_method_id':self.env.ref('account.account_payment_method_manual_in').id})
                    for line in payment.move_id.line_ids:
                        if line.account_id.internal_type =='receivable':
                            line.account_id = bank_method.receivable_account_id.id
                    payment.with_context(acc_id=bank_method.receivable_account_id.id).action_post()
                    if payment.move_id:
                        self.bank_move_ids |=  payment.move_id
                        print(self.bank_move_ids)
                    aml2 |=self.move_id.line_ids.filtered(lambda x:x.account_id == bank_method.receivable_account_id and x.debit==amount and not x.reconciled )
                    if bank_method.activate_commission and bank_method.commission_percent:

                        debit_vals={
                            'name':'Commission',
                            'account_id': bank_method.commission_account.id,
                            'debit': amount*bank_method.commission_percent/100,
                            'credit': 0,
                        }
                        credit_vals = {
                            'name': 'Commission',
                            'account_id': bank_method.bank_journal_id.payment_credit_account_id.id,
                            'credit': amount * bank_method.commission_percent / 100,

                            'debit': 0,
                        }
                        lines=[]
                        lines.append((0,0,debit_vals))
                        lines.append((0,0,credit_vals))
                        move = self.env['account.move'].create({
                            'ref':self.name,
                            'move_type':'entry',
                            'date': self.start_at,
                            'journal_id':bank_method.bank_journal_id.id,
                            'line_ids':lines
                        })
                        move.action_post()
                if self.bank_move_ids:
                    aml = self.bank_move_ids.mapped('line_ids').filtered(lambda line: not line.reconciled and line.credit > 0.0)

                    aml3 = aml +aml2
                    aml3.reconcile()
                    payment.write({'state':'posted'})
                for b_move in self.bank_move_ids:
                    date = self.start_at
                    name_arr = str(b_move.name).split('/')
                    name = '%s/%s/%s/%s' % (name_arr[0], self.start_at.year, self.start_at.month,
                                            self.env['ir.sequence'].next_by_code('closing.journal.seq'))
                    b_move.write({
                        'date': date,
                        'name': name
                    })


    def _get_related_account_moves(self):
        res = super(PosSession, self)._get_related_account_moves()
        res |= self.bank_move_ids
        return res




