
from email.policy import default
from pkg_resources import require
from odoo import api, fields, models,_
from odoo.exceptions import UserError, ValidationError

from datetime import date
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime, timedelta, date


class CertificateRequest(models.Model):
    _name = 'certificate.request'
    _description = 'Certificate request'


    def _compute_seq(self):
        return self.env['ir.sequence'].sudo().next_by_code('certificate_seq')

    name =fields.Char('Sequence',readonly=1)
    employee_id =fields.Many2one('hr.employee',string='Employee Id')
    certificate_type_id =fields.Many2one('certificate.type',string='Certificate Type',required=True)

    requested_date = fields.Date(string='Requested Date',readonly=True, default=fields.Datetime.now)
    reviewed_date = fields.Date(string='Reviewed Date',readonly=True)
    approved_date = fields.Date(string='Approved Date',readonly=True)
    address = fields.Text("Addressee",required=True)
    state = fields.Selection([
        ('draft', "Draft"),
        ('under_review', "Under Review"),
        ('sent_for_approval', "Sent for approval"),
        ('approved', "Approved"),
        ('canceled', "Canceled"),
    ], default='draft', string='State')

    issued_to = fields.Char('Issued To')
    travel_dest = fields.Char('Travel destination')

    def unlink(self):
        if self.state !='draft':
            raise UserError(_("Only Draft Stage record can be deleted"))

        return super(CertificateRequest, self).unlink()

    def submit_review(self):
        seq=self.env['ir.sequence'].sudo().next_by_code('certificate_seq')
        self.write({'state':'under_review','name':seq})

        return True

    def submit_approval(self):
        self.write({'state':'sent_for_approval','reviewed_date':datetime.now()})
        return True

    def submit_approval_sign(self):
        self.write({'state':'approved','approved_date':datetime.now()})
        return True

    def submit_cancel(self):
        self.write({'state':'canceled'})
        return True
