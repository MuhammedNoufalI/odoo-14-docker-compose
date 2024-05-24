# Part of Odoo. See LICENSE file for full copyright and licensing details.

from dataclasses import field
from email.mime import application
from numpy import rec
from dateutil.relativedelta import relativedelta

from pkg_resources import require
from odoo import fields, models, api, _
import logging
from datetime import date
from datetime import datetime, timedelta, date

import uuid
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class EmployeeDocuments(models.Model):
    _name = 'employee.documents'
    _description = 'Employee Documents'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    employee_id = fields.Many2one('hr.employee', 'Employee ID')
    name = fields.Char('Document Number', required=True)
    doc_type = fields.Many2one('employee.doctype', 'Employee Doctype', required=True)
    valid_from = fields.Datetime('Valid From')
    valid_till_date = fields.Datetime('Valid Till Date')
    upload_file = fields.Binary("Upload File")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id)
    access_token = fields.Char(required=True, default=lambda x: str(uuid.uuid4()),
                               groups="documents.group_documents_user")
    document_state = fields.Selection([
        ('valid', 'Valid'),
        ('expired', 'Expired')], default='valid', string="Document State")
    tracking = fields.Char('Tracking')
    renewals = fields.Float('Renewal(Years)')
    link = fields.Char("Link", compute='_compute_link')
    is_mail_sent = fields.Boolean('Is Mail Sent?')
    state = fields.Selection([('active', "Active"), ('due_for_renewal', "Due for Renewal"), ('expired', "Expired")],
                             string='State', compute='_compute_state', store=True)

    @api.depends('valid_till_date')
    def _compute_state(self):
        for record in self:
            record.state = ''
            if record.doc_type.is_expiry_applicable:
                if record.valid_till_date:
                    days = (record.valid_till_date - datetime.now()).days
                    if (days > 0) and (days <= record.doc_type.alert_due):
                        record.state = 'due_for_renewal'
                    elif (days > 0) and (days > record.doc_type.alert_due):
                        record.state = 'active'
                    else:
                        record.state = 'expired'

    def send_mail_for_document_renew(self):
        to_alert = self.env['employee.documents'].search([('state', '=', 'due_for_renewal')])
        doc_details_list=[]
        doc_details_lists=[]
        for rec in to_alert:
            if to_alert:
                ctx = self.env.context.copy()
                ctx.update({'alerts': to_alert})
                template_id = self.env.ref('hc_emp_docs.email_template_due_renewal')
                employee_template_id = self.env.ref('hc_emp_docs.email_template_due_renewal_for_employee')
                emails = set(employee.work_email for employee in rec.doc_type.employee_ids)
                original_passport_number = rec.name
                masked_doc_number = original_passport_number[:3] + '*' * (len(original_passport_number) - 3)
                document_number = masked_doc_number
                if rec.doc_type.is_employee_mandatory:
                    doc_details = {}
                    doc_details['doc_type'] = rec.doc_type.name
                    doc_details['doc_num'] = document_number
                    doc_details['expiry'] = rec.valid_till_date
                    doc_details_list.append(doc_details)
                    employee_template_id.with_context({'doc_details_list': doc_details_list,
                                                       'email_to': rec.employee_id.work_email,
                                                       'email_from': self.env.user.company_id.email}).send_mail(rec.id,
                                                                                                                force_send=True)

                if emails:
                    doc_list_details = {}
                    doc_list_details['doc_type'] = rec.doc_type.name
                    doc_list_details['employee'] = rec.employee_id.name
                    # doc_list_details['employee_id'] = rec.employee_id.employee_id
                    doc_list_details['doc_num'] = document_number
                    doc_list_details['expiry'] = rec.valid_till_date
                    doc_details_lists.append(doc_list_details)
                    template_id.with_context({'doc_details_lists': doc_details_lists,
                                              'email_to': ','.join(emails),
                                              'email_from': self.env.user.company_id.email}).send_mail(rec.id,
                                                                                                       force_send=True)
                    rec.is_mail_sent = True

    @api.depends('upload_file')
    def _compute_link(self):
        for record in self:
            if record.upload_file:
                folder_id = self.env['documents.document'].search([('name', '=', record.name)])
                if len(folder_id):
                    logging.info("-------------------------------folder_id---------%s")
                    record.link = "%s/document/share/%s/%s" % (
                        record.get_base_url(), folder_id[0].id, self.access_token)
                else:
                    record.link = ''

            else:
                record.link = ''

    def write(self, vals):
        att_id = False
        if vals.get('upload_file'):
            att_id = self.env['ir.attachment'].create({
                'name': str(self.id) + '_document',
                'type': 'binary',
                'datas': vals.get('upload_file'),
                # 'datas_fname': str(self.id)+'_document',
                'store_fname': str(self.id) + '_document',
                'res_model': self._name,
                'res_id': self.id,
                # 'mimetype': 'application/x-pdf'
            })

            vals['message_main_attachment_id'] = att_id.id
        res = super(EmployeeDocuments, self).write(vals)

        folder_id = self.env['documents.folder'].search([('name', '=', self.doc_type.name)])

        if self.doc_type.is_expiry_applicable:
            if not self.valid_till_date:
                raise UserError(_("Expiry Date (Valid Till Date) Is Mandatory For this Document"))
        if self.doc_type.is_employee_mandatory:
            if not self.employee_id:
                raise UserError(_("Employee Is Mandatory For This Document"))

        if len(folder_id) and att_id:
            self.env['documents.document'].create(
                {'partner_id': self.employee_id.address_home_id.id, 'folder_id': folder_id[0].id, 'name': self.name,
                 'attachment_id': att_id.id if att_id else False})

        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:

            att_id = False
            if vals.get('upload_file'):
                att_id = self.env['ir.attachment'].create({
                    'name': str(self.id) + '_document',
                    'type': 'binary',
                    'datas': vals.get('upload_file'),
                    # 'datas_fname': str(res.id)+'_document',
                    'store_fname': str(self.id) + '_document',
                    'res_model': self._name,
                    'res_id': self.id,
                    # 'mimetype': 'application/x-pdf'
                })
                vals['message_main_attachment_id'] = att_id.id
            res = super(EmployeeDocuments, self).create(vals_list)
            if res.doc_type.is_expiry_applicable:
                if not res.valid_till_date:
                    raise UserError(_("Expiry Date(Valid Till Date) Is Mandatory"))
            if res.upload_file and not res.employee_id.address_home_id:
                raise UserError(_("Please add private contact address for employee"))
            folder_id = self.env['documents.folder'].search([('name', '=', res.doc_type.name)])

            if len(folder_id) and att_id:
                self.env['documents.document'].create(
                    {'partner_id': res.employee_id.address_home_id.id, 'folder_id': folder_id[0].id, 'name': res.name,
                     'attachment_id': att_id.id if att_id else False})
        return res
