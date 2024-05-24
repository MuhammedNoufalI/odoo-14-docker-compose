from odoo import models, fields, api, exceptions, _


class BusinessTransferLetter(models.Model):
    _name = "exit.interview"
    _rec_name = 'employee_name'
    _description = "Exit Interview Workflow"

    resignation_id = fields.Many2one("Resignation")
    employee_name = fields.Char('Employee Name')
    employee_code = fields.Char('Employee Number')
    joining_date = fields.Date('Joining Date')
    date = fields.Date("Date", default=fields.Date.today())
    reporting_to = fields.Char('Reporting To')
    department = fields.Char("Department")
    last_working_day = fields.Date("Last working Day")
    job_title = fields.Char('Designation')

    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed'), ('cancel', 'Canceled')], string="state",
                             default='draft')

    remuneration_scale = fields.Selection([
        ('satisfied', 'Satisfied'),
        ('not_satisfied', 'Not Satisfied'),
        ('NA', 'Not Applicable')], string="Remuneration")
    remuneration_remarks = fields.Text("Remuneration Remarks")

    accommodation = fields.Selection([
        ('satisfied', 'Satisfied'),
        ('not_satisfied', 'Not Satisfied'),('NA', 'Not Applicable')], string="Accommodation")
    accommodation_remarks = fields.Text("Accommodation Remarks")
    transportation = fields.Selection([
        ('satisfied', 'Satisfied'),
        ('not_satisfied', 'Not Satisfied'),('NA', 'Not Applicable')], string="Transportation")
    transportation_remarks = fields.Text("Transportation Remarks")
    medical_insurance = fields.Selection([
        ('satisfied', 'Satisfied'),
        ('not_satisfied', 'Not Satisfied'),('NA', 'Not Applicable')], string="Medical Insurance")
    medical_insurance_remarks = fields.Text("Medical Insurance Remarks")
    bonus = fields.Selection([
        ('satisfied', 'Satisfied'),
        ('not_satisfied', 'Not Satisfied'),('NA', 'Not Applicable')], string="Bonus")
    bonus_remarks = fields.Text("Bonus Remarks")

    tips = fields.Selection([
        ('satisfied', 'Satisfied'),
        ('not_satisfied', 'Not Satisfied'),('NA', 'Not Applicable')], string="Tips")
    tips_remarks = fields.Text("Tips Remarks")

    line_manager = fields.Selection([
        ('satisfied', 'Satisfied'),
        ('not_satisfied', 'Not Satisfied'),('NA', 'Not Applicable')], string="Line Manager")
    line_manager_remarks = fields.Text("Line Manager Remarks")
    career_development = fields.Selection([
        ('satisfied', 'Satisfied'),
        ('not_satisfied', 'Not Satisfied'),('NA', 'Not Applicable')], string="Career Development")
    career_development_remarks = fields.Text("Career Development Remarks")
    discipline_policies = fields.Selection([
        ('satisfied', 'Satisfied'),
        ('not_satisfied', 'Not Satisfied'),('NA', 'Not Applicable')], string="Discipline Policies")
    discipline_policies_remarks = fields.Text("Discipline Policies Remarks")
    training = fields.Selection([
        ('satisfied', 'Satisfied'),
        ('not_satisfied', 'Not Satisfied'),('NA', 'Not Applicable')], string="Training")
    training_remarks = fields.Text("Training Remarks")

    performance = fields.Selection([
        ('satisfied', 'Satisfied'),
        ('not_satisfied', 'Not Satisfied'),('NA', 'Not Applicable')], string="Performance")
    performance_remarks = fields.Text("Performance Remarks")

    management_support = fields.Selection([
        ('satisfied', 'Satisfied'),
        ('not_satisfied', 'Not Satisfied'),('NA', 'Not Applicable')], string="Management Support")
    management_support_remarks = fields.Text("Management Support Remarks")

    working_hr = fields.Selection([
        ('satisfied', 'Satisfied'),
        ('not_satisfied', 'Not Satisfied'),('NA', 'Not Applicable')], string="Working Hr")
    working_hr_remarks = fields.Text("Working Hr Remarks")

    working_evr = fields.Selection([
        ('satisfied', 'Satisfied'),
        ('not_satisfied', 'Not Satisfied'),('NA', 'Not Applicable')], string="Working Env")
    working_evr_remarks = fields.Text("Working Env Remarks")

    physical_working_condition = fields.Selection([
        ('satisfied', 'Satisfied'),
        ('not_satisfied', 'Not Satisfied'),('NA', 'Not Applicable')], string="Physical working Condition")
    physical_working_condition_remarks = fields.Text("Physical working Condition Remarks")

    remarks1 = fields.Text("Remark1")
    remarks2 = fields.Text("Remark2")
    remarks3 = fields.Text("Remark3")
    remarks4 = fields.Text("Remark4")
    remarks5 = fields.Text("Remark5")
    remarks6 = fields.Text("Remark6")

    def button_confirm(self):
        self.state = 'confirm'

    def button_cancel(self):
        self.state = 'cancel'

    def button_reset_to_draft(self):
        self.state = 'draft'

    def get_benefits_totals(self):
        for rec in self:
            benefit_satisfied = 0
            benefit_not_satisfied = 0

            if rec.remuneration_scale == 'satisfied':
                benefit_satisfied += 1
            if rec.remuneration_scale=='not_satisfied':
                benefit_not_satisfied += 1

            if rec.accommodation == 'satisfied':
                benefit_satisfied += 1
            if rec.accommodation == 'not_satisfied':
                benefit_not_satisfied += 1
            if rec.transportation == 'satisfied':
                benefit_satisfied += 1
            if rec.transportation == 'not_satisfied':
                benefit_not_satisfied += 1
            if rec.medical_insurance == 'satisfied':
                benefit_satisfied += 1
            if rec.medical_insurance == 'not_satisfied':
                benefit_not_satisfied += 1
            if rec.bonus == 'satisfied':
                benefit_satisfied += 1
            if rec.bonus == 'not_satisfied':
                benefit_not_satisfied += 1
            if rec.tips == 'satisfied':
                benefit_satisfied += 1
            if rec.tips == 'not_satisfied':
                benefit_not_satisfied += 1

            dict_lines = {
                'benefit_satisfied': benefit_satisfied,
                'benefit_not_satisfied': benefit_not_satisfied
            }
            data = [dict_lines]
            return data

    def compute_job_satisfaction_count(self):
        for rec in self:
            job_satisfaction = 0
            job_not_satisfied = 0
            if rec.line_manager == 'satisfied':
                job_satisfaction += 1
            if rec.line_manager == 'not_satisfied':
                job_not_satisfied += 1

            if rec.career_development == 'satisfied':
                job_satisfaction += 1
            if rec.career_development == 'not_satisfied':
                job_not_satisfied += 1

            if rec.training == 'satisfied':
                job_satisfaction += 1
            if rec.training == 'not_satisfied':
                job_not_satisfied += 1

            if rec.performance == 'satisfied':
                job_satisfaction += 1
            if rec.performance == 'not_satisfied':
                job_not_satisfied += 1

            if rec.management_support == 'satisfied':
                job_satisfaction += 1
            if rec.management_support == 'not_satisfied':
                job_not_satisfied += 1

            dict_lines = {
                'job_satisfaction': job_satisfaction,
                'job_not_satisfied': job_not_satisfied
            }
            data = [dict_lines]
            return data

    def compute_other_satisfaction_count(self):
        for rec in self:
            other_satisfaction = 0
            other_not_satisfied = 0
            if rec.working_hr == 'satisfied':
                other_satisfaction += 1
            if rec.working_hr == 'not_satisfied':
                other_not_satisfied += 1

            if rec.working_evr == 'satisfied':
                other_satisfaction += 1
            if rec.working_evr == 'not_satisfied':
                other_not_satisfied += 1

            if rec.discipline_policies == 'satisfied':
                other_satisfaction += 1
            if rec.discipline_policies == 'not_satisfied':
                other_not_satisfied += 1

            if rec.physical_working_condition == 'satisfied':
                other_satisfaction += 1
            if rec.physical_working_condition == 'not_satisfied':
                other_not_satisfied += 1

            dict_lines = {
                'other_satisfaction': other_satisfaction,
                'other_not_satisfied': other_not_satisfied
            }
            data = [dict_lines]
            return data
