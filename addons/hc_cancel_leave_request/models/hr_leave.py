from odoo import models, fields
from odoo.exceptions import UserError, ValidationError


class HcTimeOffType(models.Model):
    _inherit = "hr.leave"

    state = fields.Selection(selection_add=[('cancel_request', 'Cancel Request Approval')])

    def cancel_leave_request(self):
        employee_manager = self.employee_id.parent_id
        user = self.env.user
        if user == employee_manager or self.employee_id:
            self.write({'state': 'cancel_request'})
        else:
            raise UserError("Only employee or his manager can cancel the request")
        return True

    def leave_cancel_approve(self):
        self.write({'state': 'cancel'})