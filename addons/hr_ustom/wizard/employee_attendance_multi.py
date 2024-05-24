# -*- coding: utf-8 -*-

from odoo import api, fields, models,exceptions


class EmpAttendanceMulti(models.TransientModel):
    _name = 'employee.attendance.multi'
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    employee_ids = fields.Many2many(comodel_name="hr.employee", string="Employees", )

    def assign_multi_emp_attendance(self):
        if not self.employee_ids:
            raise exceptions.ValidationError("Select Employee")
        for record in self.employee_ids:
            self.env['employee.attendance'].create({'employee_id':record.id,'date_from':self.date_from,'date_to':self.date_to})
