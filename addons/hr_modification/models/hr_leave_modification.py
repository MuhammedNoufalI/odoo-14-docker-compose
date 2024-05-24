from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError


class InheritHrLeave(models.Model):
    _inherit = 'hr.leave'

    attachment_ids = fields.Many2many('ir.attachment', 'requests_attachments', string="Attachments")
    is_sick_leave = fields.Boolean("Is Sick Leave")

    @api.onchange('holiday_status_id')
    def _onchange_holiday_status_id(self):
        for rec in self:
            if rec.holiday_status_id.is_sick_leave:
                rec.is_sick_leave = True
            else:
                rec.is_sick_leave = False

    @api.onchange('request_date_from', 'request_date_to')
    def _onchange_dates(self):
        for rec in self:
            if rec.request_date_from and rec.request_date_to:
                rec.number_of_days = (rec.request_date_to - rec.request_date_from).days + 1

    @api.model
    def create(self, vals_list):
        res = super().create(vals_list)
        if res.is_sick_leave and not res.attachment_ids:
            raise ValidationError(_("Kindly Upload Attachments"))
        else:
            return self.check_probation_criteria(res)

    def check_probation_criteria(self, res=None):
        if not res.holiday_status_id.is_unpaid_leave:
            yes = self.has_completed_probation(res.employee_id)
            if yes:
                return res
            else:
                raise ValidationError(_("This Employee has not complete the Probation"
                                        " Yet So it's only allowed for Unpaid Leaves"))
        return res

    def write(self, vals):
        res = super().write(vals)
        if self.is_sick_leave and not self.attachment_ids:
            raise ValidationError(_("Kindly Upload Attachments"))
        else:
            if vals.get('employee_id') and vals.get('holiday_status_id'):
                if not self.env['hr.leave.type'].browse(vals.get('holiday_status_id')).is_unpaid_leave:
                    get_emp = self.env['hr.employee'].browse(vals.get('employee_id'))
                    yes = self.has_completed_probation(get_emp)
                    if yes:
                        return res
                    else:
                        raise ValidationError(_("This Employee has not complete the Probation"
                                                " Yet So it's only allowed for Unpaid Leaves"))
            elif vals.get('employee_id') and not vals.get('holiday_status_id'):
                if self.holiday_status_is.is_unpaid_leaves:
                    return res
                else:
                    get_emp = self.env['hr.employee'].browse(vals.get('employee_id'))
                    yes = self.has_completed_probation(get_emp)
                    if yes:
                        return res
                    else:
                        raise ValidationError(_("This Employee has not complete the Probation"
                                                " Yet So it's only allowed for Unpaid Leaves"))
            elif vals.get('holiday_status_id') and not vals.get('employee_id'):
                if not self.env['hr.leave.type'].browse(vals.get('holiday_status_id')).is_unpaid_leave:
                    yes = self.has_completed_probation(self.employee_id)
                    if yes:
                        return res
                    else:
                        raise ValidationError(_("This Employee has not complete the Probation"
                                                " Yet So it's only allowed for Unpaid Leaves"))

            return res

    @staticmethod
    def has_completed_probation(employee=None):
        today = datetime.today()
        hire_date = fields.Datetime.from_string(employee.joining_date)
        if hire_date:
            return (today - hire_date) >= timedelta(days=183)
        else:
            return False
