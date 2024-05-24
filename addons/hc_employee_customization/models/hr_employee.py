# -*- coding:utf-8 -*-

from email.policy import default
from odoo import api, fields, models, _
from datetime import date
from odoo.exceptions import Warning, UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    _description = 'Employee'

    # att_card_number = fields.Char("Card Number", help="Card Which is Used for the Punching in the Attendance Devices")
    # employee_id = fields.Char(string='Employee ID')
    no_of_contracts = fields.Integer(string='No Of Contracts', default=0)

    # hc_private_email = fields.Char(string="Private-Email", help="HC Private Email")
    # manager_id = fields.Many2one('hr.employee', string='Manager ', tracking=True)

    # def name_get(self):
    #     result = []
    #     for employee in self:
    #         if employee.employee_id:
    #             name = employee.employee_id + " - " + employee.name
    #             result.append((employee.id, name))
    #     return result
    #
    #     cost_center_code_id = fields.Many2one('hc.cost.center.code', string="Cost Center Code")



class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    no_of_contracts = fields.Integer(string='No Of Contracts', default=0)
#
#
# class CostCenterCode(models.Model):
#     _name = 'hc.cost.center.code'
#     _description = 'Cost Center Code of the Employees'
#
#     name = fields.Char('Cost Center Code')
#     notes = fields.Text("Notes")
