from email.policy import default
from pkg_resources import require
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

from datetime import date
import logging
from datetime import datetime, timedelta, date

_logger = logging.getLogger(__name__)


class PassportRequest(models.Model):
    _name = 'passport.request'
    _description = 'Passport request'




    @api.model
    def create(self, vals):
        code = self.env['ir.sequence'].next_by_code('passport_req_seq')
        vals['name'] = code or _('New')
        return super(PassportRequest, self).create(vals)


    name = fields.Char(readonly=True, default='New')
    employee_id = fields.Many2one('hr.employee', string='Employee Name')
    employee_no = fields.Char('Employee No')
    Date = fields.Date("Request Date", default=fields.Date.today())
    department = fields.Char("Department / Site", compute='compute_employee_dep')
    reason_for_request = fields.Selection([('leave', 'Annual Leave'),
                                           ('eid', 'EID'),
                                           ('renewal', 'Passport Renewal'),
                                           ('bank_purpose', 'Bank Purposes'), ('other', 'Others')
                                           ], string='Reason for request ')
    approved_date_from = fields.Date(string='Date From')
    approved_date_to = fields.Date(string='Date To')
    passport_required_date_from = fields.Date(string='Passport Date From')
    passport_required_date_to = fields.Date(string='Passport Date To')
    signature = fields.Binary('Signature')
    mobile_number = fields.Char('Mobile No')
    approved_by = fields.Char("Approved by")
    approval_date = fields.Datetime('Approved On')
    hr_approval = fields.Char('HR Approval')
    hr_approval_date = fields.Datetime("HR Approval Date")
    state = fields.Selection([('draft', 'Draft'),
                              ('submitted', 'Submitted'),
                              ('manager_approved', 'Employee Manager Approved'),
                              ('hr_approved', 'Hr Approved'), ('canceled', 'Canceled')], default='draft')

    transmitter_name = fields.Char("Name")
    remarks = fields.Text("Remarks")

    @api.depends('employee_id')
    def compute_employee_dep(self):
        self.department = self.employee_id.department_id.name

    def unlink(self):
        if self.state != 'draft':
            raise UserError(_("Only Draft Stage record can be deleted"))

        return super(PassportRequest, self).unlink()

    def submit_request(self):
        self.write({'state': 'submitted'})
        return True

    def manager_approval(self):
        employee_manager = self.employee_id.parent_id.user_id
        user = self.env.user
        if employee_manager == user:
            self.write(
                {'state': 'manager_approved', 'approval_date': datetime.now(), 'approved_by': self.env.user.name})
        else:
            raise UserError("Only employees manager can approve the request")
        return True

    def hr_manager_approval(self):
        if self.env.user.has_group('hr.group_hr_manager'):
            self.write({'state': 'hr_approved', 'hr_approval_date': datetime.now(), 'hr_approval': self.env.user.name})
        return True

    def cancel_request(self):
        self.write({'state': 'canceled'})
        return True
