# -*- coding: utf-8 -*-
from odoo import models, fields


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    loan_amount = fields.Float("Loan Amount", compute="_get_loan_amount")

    def _get_loan_amount(self):
        loan_amount = 0
        for rec in self:
            for line in rec.input_line_ids:
                if line.loan_line_id:
                    loan_amount += line.amount
            rec.loan_amount = loan_amount

    def action_payslip_done(self):
        for line in self.input_line_ids:
            if line.loan_line_id:
                line.loan_line_id.paid = True
                line.loan_line_id.loan_id._compute_loan_amount()
        return super(HrPayslip, self).action_payslip_paid()
