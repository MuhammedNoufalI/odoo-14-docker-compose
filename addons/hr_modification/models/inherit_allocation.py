from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class InheritLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    is_annual_sick_leave = fields.Boolean("Is Annual Sick Leave")

    @api.onchange('date_from', 'date_to')
    def _onchange_date_from_date_to(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.employee_id:
                rec.number_of_days_display = (rec.date_to - rec.date_from).days + 1

    # def action_validate(self):
    #     current_employee = self.env.user.employee_id
    #     for holiday in self:
    #         if holiday.state not in ['confirm', 'validate1']:
    #             raise UserError(_('Allocation request must be confirmed in order to approve it.'))
    #         holiday.write({'state': 'validate'})
    #         if holiday.validation_type == 'both':
    #             holiday.write({'second_approver_id': current_employee.id})
    #         else:
    #             holiday.write({'first_approver_id': current_employee.id})
    #         # if holiday.holiday_status_id.is_sick_leave and holiday.holiday_type == 'employee' and \
    #         #         holiday.number_of_days_display == 45.0 and holiday.is_annual_sick_leave:
    #         #     holiday.employee_id.full_paid_allowed = 15
    #         #     holiday.employee_id.half_paid_allowed = 30
    #         #     holiday.employee_id.allocation_from_date = holiday.date_from
    #         #     holiday.employee_id.allocation_to_date = holiday.date_to
    #         if holiday.allocation_type == 'accrual':
    #             is_year_completed = self.has_completed_year(holiday.employee_id)
    #             holiday.number_per_interval = 2.5 if is_year_completed else 2
    #         holiday._action_validate_create_childs()
    #     self.activity_update()
    #     return True
    #
    # def has_completed_year(self, employee=None):
    #     today = datetime.today()
    #     hire_date = fields.Datetime.from_string(employee.first_contract_date)
    #     if hire_date:
    #         return (today - hire_date) >= timedelta(days=365)
    #     else:
    #         return False
