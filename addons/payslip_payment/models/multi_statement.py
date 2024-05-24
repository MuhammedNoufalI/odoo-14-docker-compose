# -*- coding: utf-8 -*-
from datetime import datetime,date
from odoo import fields, models, api, exceptions, _
from odoo.exceptions import ValidationError,UserError

class HrEmployeePayslip(models.Model):
    _inherit = 'hr.employee'

    journal_id = fields.Many2one(comodel_name="account.journal",domain=[('type','in',['cash','bank'])] ,string="Journal", required=False, )


class MultiStatement(models.TransientModel):
    _name = 'payment.payslip.statement'

    def create_Statements(self):
        payslips = self.env['hr.payslip'].browse(self._context.get('active_ids', []))
        map_payslips_journals = payslips.mapped('employee_id.journal_id')
        print (map_payslips_journals,'map_payslips_journals')
        for journal in map_payslips_journals:
            statement_lines = []
            for pay in payslips.search([('state','=','done')]):
                if pay.employee_id.journal_id.id == journal.id:
                    statement_lines.append((0,0,{
                        'date':date.today(),
                        'name':str('Payslip Payment For ') + str(pay.employee_id.name),
                        'partner_id':pay.employee_id.address_home_id.id,
                        'ref':str(pay.number),
                        'amount':-pay.total_net_salary,
                        'payslip_id':pay.id,
                    }))
                    pay.state = 'paid'
            if statement_lines:
                self.env['account.bank.statement'].create({
                    'name':str('Payslip Payment For ') + str(journal.name),
                    'journal_id':journal.id,
                    'date':date.today(),
                    'line_ids':statement_lines,


                })




class AccountBankSettelmentInhrit(models.Model):
    _inherit = 'account.bank.statement.line'

    payslip_id = fields.Many2one(comodel_name="hr.payslip", string="", required=False, )


