from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'hr.resignation'

    clearance_id = fields.Many2one('hr.clearance', 'Clearance Id')

    def create_clearance_form(self):
        for rec in self:
            employee_id = rec.employee_id
            employee_job_position = self.employee_id.job_title
            contact_number =employee_id.personal_contact_no
            data = {
                'employee_id':employee_id.id,
                'resignation_id': rec.id,
                'employee_name': employee_id.name,
                'employee_code': employee_id.oe_emp_sequence,
                'last_working_day': rec.expected_revealing_date,
                'job_title': employee_job_position,
                'resignation_date':rec.resign_date,
                'business_unit':employee_id.business_unit,
                'contact_number':contact_number
            }
            view_id = self.env['hr.clearance'].create(data)
            rec.clearance_id = view_id.id
            return {
                'name': "Hr Clearance Form",
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'hr.clearance',
                'view_id': self.env.ref('hc_clearance_form.hr_clearance_form_view').id,
                'target': 'current',
                'res_id': view_id.id
            }
