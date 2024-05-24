from odoo import models, fields, api


class InheritDepartWizard(models.TransientModel):
    _inherit = 'hr.departure.wizard'

    def action_register_departure(self):
        res = super().action_register_departure()
        if self.departure_reason == 'transfer':
            employee_data = self.env['business.transfer.letter'].search([('employee_id', '=', self.employee_id.id)])
            for employee in employee_data:
                employee.unlink()
            employee_id = self.employee_id
            employee_job_position = self.employee_id.job_title
            contract_id = self.employee_id.contract_id
            total_salary = contract_id.total_salary
            salary_ids = contract_id.salary_rule_ids
            company_id = self.env.company.name
            data = {
                'employee_id': employee_id.id,
                'employee_name': employee_id.name,
                'employee_code': employee_id.oe_emp_sequence,
                'business_unit': self.business_unit,
                'company_name': company_id,
                'street': employee_id.address_home_id.street,
                'street2': employee_id.address_home_id.street2,
                'zip': employee_id.address_home_id.zip,
                'city': employee_id.address_home_id.city,
                'state_id': employee_id.address_home_id.state_id.name,
                'country_id': employee_id.address_home_id.country_id.name,
                'employee_job_position': employee_job_position,
                'total_salary': total_salary,
                'contract_id': contract_id.id,
                'old_business_unit': employee_id.business_unit,

            }
            line_ids = []
            for salary in salary_ids:
                line_ids += [(0, 0, {
                    'salary_rule_id': salary.salary_rule_id.id,
                    'amount': salary.amount,
                })]
            data.update({'salary_rule_ids': line_ids})
            view_id = self.env['business.transfer.letter'].create(data)
            return {
                'name': "Business Transfer Letter",
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'business.transfer.letter',
                'view_id': self.env.ref('hc_business_transfer_letter.business_transfer_letter_form').id,
                'target': 'current',
                'res_id': view_id.id
            }
        return res
