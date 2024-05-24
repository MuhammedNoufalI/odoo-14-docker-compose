# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class Employee(models.Model):
    _inherit = 'hr.employee'

    labour_card_number = fields.Char(
        string="Internal Reference",
        help="Labour Card Number Of Employee"
    )
    employee_type = fields.Selection([
        ('regular_employee', 'Regular Employee'),
        ('freelance', 'Free Lancer')
        ], string="Employee Type")
    agent_id = fields.Many2one('res.bank', string="Bank", help="Agent ID or bank ID of Employee")
    # oe_employee_seq = fields.Char(
    #     string='Employee Reference', required=True, copy=False, readonly=True,
    #     index=True, default=lambda self: _('New')
    # )
    medical_insurance = fields.Char(string="Medical Insurance Number")
    medical_insurance_categ = fields.Many2one('medical.insurance.category', string="Medical Insurance Category")
    oe_certificate_file = fields.Binary('Certificate')
    oe_certificate_file_name = fields.Char('File Name')
    salary_card_number = fields.Char(
        string="Salary Card Number/Account Number",
        help="Salary card number or account number of employee"
    )

    # def write(self, vals):
    #     if 'labour_card_number' in vals.keys() and vals['labour_card_number']:
    #         if len(vals['labour_card_number']) < 14:
    #             vals['labour_card_number'] = vals['labour_card_number'].zfill(14)
    #     return super(Employee, self).write(vals)

    # @api.model
    # def create(self, vals):
    #     if vals.get('oe_employee_seq', _('New')) == _('New'):
    #         vals['oe_employee_seq'] = self.env['ir.sequence'].next_by_code('hr.employee.seq') or _('New')
    #
    #     # if 'labour_card_number' in vals.keys() and vals['labour_card_number']:
    #     #     if len(vals['labour_card_number']) < 14:
    #     #         vals['labour_card_number'] = vals['labour_card_number'].zfill(14)
    #     return super(Employee, self).create(vals)


class Bank(models.Model):
    _inherit = 'res.bank'

    routing_code = fields.Char(string="Routing Code", size=9, required=True, help="Bank Route Code")

    def write(self, vals):
        if 'routing_code' in vals.keys():
            vals['routing_code'] = vals['routing_code'].zfill(9)
        return super(Bank, self).write(vals)

    @api.model
    def create(self, vals):
        vals['routing_code'] = vals['routing_code'].zfill(9)
        return super(Bank, self).create(vals)


class Company(models.Model):
    _inherit = 'res.company'

    employer_id = fields.Char(string="Employer ID", help="Company Employer ID")

    def write(self, vals):
        if 'company_registry' in vals:
            vals['company_registry'] = vals['company_registry'].zfill(13) if vals['company_registry'] else False
        if 'employer_id' in vals:
            vals['employer_id'] = vals['employer_id'].zfill(13) if vals['employer_id'] else False
        return super(Company, self).write(vals)

    @api.model
    def create(self, vals):
        vals['company_registry'] = vals['company_registry'].zfill(13) if vals['company_registry'] else False
        if 'employer_id' in vals:
            vals['employer_id'] = vals['employer_id'].zfill(13) if vals['employer_id'] else False
        return super(Company, self).create(vals)


