from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class HrClearance(models.Model):
    _name = "hr.clearance"
    _rec_name = 'employee_name'
    _description = 'Hr Clearance'

    employee_id = fields.Many2one('hr.employee', 'Employee ID')
    employee_name = fields.Char('Employee Name')
    employee_code = fields.Char('Employee Number')
    resignation_date = fields.Date('Resignation Date')
    last_working_day = fields.Date("Last working Day")
    job_title = fields.Char('Position')
    business_unit = fields.Char("Business Unit")
    contact_number = fields.Char('Mobile Number')
    resignation_id = fields.Many2one('hr.resignation', 'Resignation ID')

    company_owned = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Company Owned")
    company_issues = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Compnay Issued")
    uniforms = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Uniforms")
    attendance_sheet = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Attendance Sheet")
    final_inventory = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Final Inventory")
    department_keys = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Department Keys")
    others = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')], string="Others")

    outstanding_petty = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Outstanding Petty Cash")
    outstanding_fines = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Outstanding Fines, Deductions")
    mobile_bills = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Outstanding Mobile Bills")
    safe_master_key = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Safe Keys & Master Keys")
    company_issued_car = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Company issued Car / Petrol Card")
    other_tips = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Others (Tips/Bonus/Incentives)")

    training_material = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Training Materials/Manuals/Online Deactivation")
    training_cost = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Training Cost (Registered in the last one year)")
    training_others = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')], string="Others")

    last_day_apartment = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Last day at Apartment Name")
    last_day_apartment_name = fields.Char("Apartment Name")
    last_day_room = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Last day at Room No.")
    last_day_room_no = fields.Char("Room No")
    bed_frame_cover = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Bed Frame (1) / Bed Mattress (1) / Bed Cover (1)")
    pillow_blanket = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Pillow (1) / Blanket (1) / Bed Sheet (2)")
    apartment_key = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Apartment Key")
    locker_key = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Locker Key")
    others_accommodation = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Others (Value to be deducted for unreturned Items)")

    drivers_clearance = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Drivers (Keys, vehicles, car registration card, etc.)")
    penalty = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Penalty / Fines")

    email_deactivation = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Email Deactivation or Forwarding")
    forwarding_to = fields.Char("Email Forwarding to")
    system_login = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Software System Login (SEVENROOMS, HRIS, FINANCE SYSTEM, ETC)")
    laptop_desktop = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Laptop / Desktop / IPAD / Camera")
    charger_cpu = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="CHARGER / CPU")
    pos_micros = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="POS / Micros")
    other_system_materials = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')], string="Others")

    office_locker_keys = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Office Locker Keys (applicable for Coporate Office Employees)")
    outstanding_bank_loans = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Oustanding Bank Loans")
    exit_interview = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Exit Interview")
    company_car_parking_card = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Company issued Car Parking Card / Access")
    company_mobile = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Company issued Mobile Device / SIM")
    company_bank_account = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Company issued Bank Account Clearance (After F/S paid)")
    residency_cancel = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Residency Cancellation / Clearance (After F/S paid)")
    insurance_cancel = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Insurance Cancellation (After Visa Cancellation)")
    salary_transfer = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Salary Transfer Letter (STL) Issued")
    other_fines = fields.Selection(
        [('cleared', 'Cleared'), ('not_cleared', 'Not Cleared'), ('not_applicable', 'Not Applicable')],
        string="Others (Fines, Deductions)")

    state = fields.Selection([('draft', 'Draft'),('line_manager', 'Line Manager Section'), ('it_team', 'IT Team Section'), ('finance', 'Finance Team Section'),
                              ('confirm', 'Confirmed'), ('cancel', 'Canceled')], string="state",
                             default='draft')

    is_line_manager = fields.Boolean("Is line manger", compute='check_user')
    is_it_team_user = fields.Boolean("Is IT Team user", compute='check_user')
    is_finance_user = fields.Boolean("Is HR User", compute='check_user')

    def check_user(self):
        employee_manager = self.employee_id.parent_id.user_id
        user = self.env.user
        if employee_manager == user:
            self.is_line_manager = True
        else:
            self.is_line_manager = False
        if self.env.user.has_group('account.group_account_user'):
            self.is_finance_user = True
        else:
            self.is_finance_user = False

        if self.env.user.has_group('hc_clearance_form.group_it_team_approve'):
            self.is_it_team_user = True
        else:
            self.is_it_team_user = False


    def to_department_head(self):
        self.state = 'line_manager'
    def to_it_team(self):
        self.state = 'it_team'
    def to_finance_team(self):
        self.state = 'finance'

    def button_confirm(self):
        self.state = 'confirm'

    def button_cancel(self):
        self.state = 'cancel'

    def button_reset_to_draft(self):
        self.state = 'draft'
