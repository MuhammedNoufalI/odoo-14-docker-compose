from odoo import models, fields, api, _
from datetime import date, datetime, time
from odoo.exceptions import ValidationError


class HrAttendanceReport(models.TransientModel):
    _name = 'hr.employee.attendance.report'

    employee_ids = fields.Many2many("hr.employee", string="Employees", required=True)
    date_from = fields.Date("Date From", required=True)
    date_to = fields.Date("Date to", required=True)

    def print_report(self):
        for rec in self:
            if rec.date_from > rec.date_to:
                raise ValidationError(_("Date from must be greater then date to"))
        data = {
            'employee_ids': self.employee_ids.ids,
            'date_from': self.date_from,
            'date_to': self.date_to
        }
        return self.env.ref('hr_attendance_customization.hr_emp_att_report').report_action(
            self, data=data)


class RecoverableAgeingReport(models.AbstractModel):
    _name = 'report.hr_attendance_customization.hr_emp_att_report_tmp_id'
    _description = 'HR employee Attendance Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        all_attendances = self.env['hr.attendance'].search(
            [('check_in', '>=', datetime.fromisoformat(data['date_from']).date()),
             ('check_out', '<=', datetime.fromisoformat(data['date_to']).date()),
             ('employee_id', 'in', data.get('employee_ids'))
             ])
        return {
            'docs': docids,
            'attendances': all_attendances,
            'date_from': datetime.fromisoformat(data['date_from']).date(),
            'date_to': datetime.fromisoformat(data['date_to']).date()
        }
