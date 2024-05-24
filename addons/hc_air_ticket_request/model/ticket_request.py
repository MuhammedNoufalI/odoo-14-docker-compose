from odoo import models, fields, api, exceptions, _
from datetime import datetime, date, time
from odoo.exceptions import UserError


class TicketRequestForm(models.Model):
    _name = "ticket.request"
    _description = "Air Ticket Request Form"
    _rec_name = 'employee_id'

    leave_id = fields.Many2one("hr.leave", 'Leave ID')
    employee_id = fields.Many2one('hr.employee', 'Employee ID')
    employee_code = fields.Char(string='Employee Code')
    request_date = fields.Date("Request Date", default=fields.Date.today())
    ticket_type = fields.Selection([('fixed', 'Fixed'),
                                    ('flexible', 'Flexible')], string='Ticket Type')

    ticket_policy = fields.Selection([('annual', 'Annual'),
                                      ('biennial', 'Biennial')], string='Ticket Policy')

    ticket_amount = fields.Float("Ticket amount")
    payroll_period = fields.Many2one('hc.payroll.period', string="Payroll Period")
    country_from = fields.Many2one("res.country", 'Country From')
    country_to = fields.Many2one("res.country", 'Country To')
    amount_to_payslip = fields.Boolean("Amount to Payslip", default=False)
    state = fields.Selection([('draft', 'Draft'),
                              ('submit', 'Submit'),
                              ('line_manager', 'Employees Manager Approval'),
                              ('hr_approval', 'Hr Approved')
                              ], string='State')

    ticket_entitlement = fields.Selection([('365', '365'),
                                           ('730', '730')], string='Ticket Entitlement')

    ticket_availed = fields.Char("Ticket Availed", compute="calculate_ticket_availed")
    ticket_accrued = fields.Char("Ticket Accrued", compute='compute_ticket_accrued')
    ticket_balance = fields.Char("Ticket Balance", compute="calculate_ticket_availed")
    service_days = fields.Char("Service Days", compute="calculate_service_days")

    @api.model_create_multi
    def create(self, vals_list):
        res = super(TicketRequestForm, self).create(vals_list)
        if not res['ticket_entitlement']:
            raise UserError(_("You must select Ticket Entitlement on employee's Contract."))
        return res

    @api.onchange('employee_id')
    def contract_ticket_entitlement(self):
        if self.employee_id.contract_id:
            self.ticket_entitlement = self.employee_id.contract_id.ticket_entitlement

    @api.depends('employee_id')
    def calculate_service_days(self):
        if self.employee_id:
            number_of_days = 0.0
            today = date.today()
            global_joining_date = self.employee_id.joining_date
            unpaid_leave_days = self.env['hr.leave'].search(
                [('create_date', '<=', today), ('create_date', '>=', global_joining_date),
                 ('employee_id', '=', self.employee_id.id),
                 ('holiday_status_id.is_unpaid_leave', '=', True), ('state', '=', 'validate')])
            if unpaid_leave_days:
                for days in unpaid_leave_days:
                    number_of_days += days.number_of_days

            total_service_period = (today - global_joining_date).days
            self.service_days = int(total_service_period) - number_of_days
        else:
            self.service_days = 0

    @api.depends('ticket_entitlement')
    def compute_ticket_accrued(self):
        if not self.ticket_entitlement == 0 and not self.service_days == 0:
            ticket_accrued = float(self.service_days) / int(self.ticket_entitlement)
            self.ticket_accrued = round(ticket_accrued, 2)
        else:
            self.ticket_accrued = 0

    @api.depends('employee_id')
    def calculate_ticket_availed(self):
        today = date.today()
        no_request = 0
        if self.employee_id:
            no_request = self.employee_id.ticket_availed
        # global_joining_date = self.employee_id.joining_date
        # ticket_request = self.env['ticket.request'].search(
        #     [('id', '!=', self.id), ('employee_id', '=', self.employee_id.id), ('state', '=', 'hr_approval'),
        #      ('create_date', '<=', today),
        #      ('create_date', '>=', global_joining_date)])
        # for request in ticket_request:
        #     no_request += 1

        self.ticket_availed = no_request
        self.ticket_balance = float(self.ticket_accrued) - int(self.ticket_availed)

    def to_submit_request(self):
        self.state = 'submit'

    def employee_manager_approval_state(self):
        self.state = 'line_manager'

    def hr_approval_state(self):
        self.state = 'hr_approval'
        self.employee_id.last_ticket_availed_date = datetime.now()
        self.employee_id.ticket_availed = self.employee_id.ticket_availed + 1

    def hr_reset_to_draft(self):
        self.state = 'draft'

    @api.onchange("ticket_type")
    def onchange_ticket_type(self):
        for rec in self:
            if rec.ticket_type == 'fixed':
                contract_id = rec.employee_id.contract_id
                ticket_rule = contract_id.salary_rule_ids.filtered(lambda x: x.salary_rule_id.code == 'TKTR')
                if ticket_rule:
                    rec.ticket_amount = ticket_rule.amount
                else:
                    rec.ticket_amount = 0.0

    def apply_to_payslip(self):
        for rec in self:
            rec.amount_to_payslip = True
