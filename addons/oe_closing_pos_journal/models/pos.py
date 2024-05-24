from odoo import models, fields, api,_
from collections import defaultdict
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
import logging
_logger = logging.getLogger(__name__)


class InheritPosSession(models.Model):
    _inherit = 'pos.session'

    def _create_account_move(self):
        """ Create account.move and account.move.line records for this session.

        Side-effects include:
            - setting self.move_id to the created account.move record
            - creating and validating account.bank.statement for cash payments
            - reconciling cash receivable lines, invoice receivable lines and stock output lines
        """
        journal = self.config_id.journal_id
        # Passing default_journal_id for the calculation of default currency of account move
        # See _get_default_currency in the account/account_move.py.
        account_move = self.env['account.move'].with_context(default_journal_id=journal.id).create({
            'journal_id': journal.id,
            'date': self.start_at,
            'ref': self.name,
        })
        self.write({'move_id': account_move.id})

        data = {}
        data = self._accumulate_amounts(data)
        data = self._create_non_reconciliable_move_lines(data)
        data = self._create_cash_statement_lines_and_cash_move_lines(data)
        data = self._create_invoice_receivable_lines(data)
        data = self._create_stock_output_lines(data)

        if account_move.line_ids:
            account_move._post()

        data = self._reconcile_account_move_lines(data)
        for move in self._get_related_account_moves():
            _logger.info("MOVE {}".format(move))
            date = self.start_at
            name_arr = str(move.name).split('/')
            name = '%s/%s/%s/%s' % (name_arr[0], self.start_at.year, self.start_at.month, self.env['ir.sequence'].next_by_code('closing.journal.seq'))
            move.write({
                'date': date,
                'name': name
            })
