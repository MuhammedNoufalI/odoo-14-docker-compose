# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from email.mime import application

from odoo import fields, models, api, _
from datetime import datetime, date, time

from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class employee_doctype(models.Model):
    _name = 'employee.doctype'
    _description = 'Employee Documents type'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Document Name', required=True)
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id)
    is_expiry_applicable = fields.Boolean('Is Expiry Applicable')
    employee_ids = fields.Many2many('hr.employee', string='Document Responsible')
    # default_validity = fields.Datetime('Default Validity')
    default_validitys = fields.Float('Default Validity(Years)')
    application_fee = fields.Float(string="Application Fee")
    application_fee_express = fields.Float(string="Application  Fee (Express)")
    renewal_fee = fields.Float(string="Renewal Fee")
    max_p_time = fields.Float(string="Maximum Processing Time(Days)")
    renewal_alert = fields.Boolean("Renewal Alert")
    batch_renewal = fields.Boolean("Batch Renewal")
    alert_due = fields.Integer("Alert Due(Days)")
    is_employee_mandatory = fields.Boolean(string='Is Employee Mandatory')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            document_folder_obj = self.env['documents.folder']
            emp_doc_id = self.env.ref('hc_emp_docs.document_employees').id
            document_folder_obj.create({'name': vals['name'], 'parent_folder_id': emp_doc_id})
        res = super(employee_doctype, self).create(vals)
        return res

    # @api.model
    # def create(self, vals):
    #     employee_id = vals.get('employee_id')
    #     employee = self.env['hr.employee'].search([('id', '=', employee_id)])
    #     end_date = vals.get('date_end')
    #     start_date = vals.get('date_start')
    #     employee.no_of_contracts += 1
    #     if employee.employee_id is False:
    #         raise UserError(_("Please Update the Employee ID of the Employee."))
    #     contract = self.env['hr.contract'].search([('employee_id', '=', employee_id),
    #                                                ('state', '!=', 'cancel'), ('date_end', '=', None)], limit=1)
    #     if contract:
    #         contract.date_end = datetime.strptime(start_date, "%Y-%m-%d") - relativedelta(days=1)
    #     if vals.get('name', '') == '':
    #         vals['name'] = employee.employee_id + '/00' + str(employee.no_of_contracts)
    #     res = super(HrContract, self).create(vals)
    #     return res
