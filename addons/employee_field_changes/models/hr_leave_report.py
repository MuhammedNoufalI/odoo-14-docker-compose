from odoo import api, fields, models, tools, exceptions, _
from odoo.osv import expression


class LeaveReport(models.Model):
    _inherit = "hr.leave.report"

    def action_time_off_analysis_for_employee(self):
        domain = [('holiday_type', '=', 'employee')]

        if self.env.context.get('active_ids'):
            domain = expression.AND([
                domain,
                [('employee_id', 'in', self.env.context.get('active_ids', []))]
            ])

        return {
            'name': _('Time Off Analysis'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.leave.report',
            'view_mode': 'tree,pivot,form',
            'search_view_id': self.env.ref('hr_holidays.view_hr_holidays_filter_report').id,
            'domain': domain,
            'context': {
                'search_default_group_type': True,
                'search_default_year': True,
                'search_default_validated': True,
                'search_default_annual_leave': True,
            }
        }
