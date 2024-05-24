import datetime
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrResignation(models.Model):
    _inherit = 'hr.resignation'

    exit_interview_id = fields.Many2one('exit.interview', 'Exit Interview Id')

    def cancel_resignation(self):
        for rec in self:
            if rec.clearance_id:
                rec.clearance_id.state = 'cancel'
            if rec.gratuity_id:
                rec.gratuity_id.state = 'cancel'
            if rec.exit_interview_id:
                rec.exit_interview_id.state = 'cancel'
            rec.state = 'cancel'

    def reject_resignation(self):
        for rec in self:
            rec.cancel_resignation()
            # if rec.clearance_id:
            #     rec.clearance_id.state = 'cancel'
            # if rec.gratuity_id:
            #     rec.gratuity_id.state = 'cancel'
            # if rec.exit_interview_id:
            #     rec.exit_interview_id.state = 'cancel'
            # rec.state = 'cancel'

    def create_exit_interview(self):
        for rec in self:
            employee_id = rec.employee_id
            employee_job_position = self.employee_id.job_title
            data = {
                'resignation_id': rec.id,
                'employee_name': employee_id.name,
                'employee_code': employee_id.oe_emp_sequence,
                'joining_date': rec.joined_date,
                'reporting_to': employee_id.parent_id.name,
                'department': rec.department_id.name,
                'last_working_day': rec.expected_revealing_date,
                'job_title': employee_job_position,
            }
            view_id = self.env['exit.interview'].create(data)
            rec.exit_interview_id = view_id.id
            return {
                'name': "Exit Interview Workflow<",
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'exit.interview',
                'view_id': self.env.ref('hc_exit_interview_workflow.exit_interview_form').id,
                'target': 'current',
                'res_id': view_id.id
            }
