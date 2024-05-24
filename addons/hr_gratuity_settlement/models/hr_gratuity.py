# -*- coding: utf-8 -*-
from datetime import date
from odoo import fields, models, api, _
from odoo.exceptions import Warning, UserError
import copy
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta


class YearsInService(models.Model):
    _name = 'years.service.line'

    name = fields.Char('Name')
    years = fields.Float("Years")
    amount = fields.Float("Amount")
    gratuity_config_id = fields.Many2one('hr.gratuity.accounting.configuration', 'Configuration')
    gratuity_line_id = fields.Many2one('gratuity.configuration', 'Configuration Line')
    leaves_done = fields.Float("Leaves Done")
    gratuity_id = fields.Many2one('hr.gratuity')


class EmployeeGratuity(models.Model):
    _name = 'hr.gratuity'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Employee Gratuity"
    _rec_name = 'employee_id'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('cancel', 'Cancelled')],
        default='draft', track_visibility='onchange')
    name = fields.Char(string='Reference', copy=False,
                       default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  required=True, help="Employee")
    employee_contract_type = fields.Selection([
        ('limited', 'Limited'),
        ('unlimited', 'Unlimited')], string='Contract Type',
        store=True, help="Choose the contract type."
                         "if contract type is limited then during gratuity settlement if you have not specify the end date for contract, gratuity configration of limited type will be taken or"
                         "if contract type is Unlimited then during gratuity settlement if you have specify the end date for contract, gratuity configration of limited type will be taken.")
    employee_joining_date = fields.Date(string='Joining Date', readonly=True,
                                        store=True, help="Employee joining date")
    employee_exit_date = fields.Date(string='Exit Date', readonly=True,
                                        store=True, help="Employee joining date")
    wage_type = fields.Selection([('monthly', 'Monthly Fixed Wage'), ('hourly', 'Hourly Wage')],
                                 help="Select the wage type monthly or hourly")
    total_working_years = fields.Float(string='Total Years Worked', readonly=True, store=True,
                                       help="Total working years")
    employee_probation_years = fields.Float(string='Leaves Taken(Years)', readonly=True, store=True,
                                            help="Employee probation years")
    employee_gratuity_years = fields.Float(string='Gratuity Calculation Years',
                                           readonly=True, store=True, help="Employee gratuity years")
    employee_basic_salary = fields.Float(string='Basic Salary',
                                         readonly=True,
                                         help="Employee's basic salary.")
    employee_gratuity_duration = fields.Many2one('gratuity.configuration',
                                                 readonly=True,
                                                 string='Configuration Line')
    employee_gratuity_configuration = fields.Many2one('hr.gratuity.accounting.configuration',
                                                      readonly=True,
                                                      string='Gratuity Configuration')
    employee_gratuity_amount = fields.Float(string='Gratuity Payment', readonly=True, store=True,
                                            help="Gratuity amount for the employee. \it is calculated If the wage type is hourly then gratuity payment is calculated as employee basic salary * Employee Daily Wage Days * gratuity configration rule percentage * gratuity calculation years.orIf the wage type is monthly then gratuity payment is calculated as employee basic salary * (Working Days/Employee Daily Wage Days) * gratuity configration rule percentage * gratuity calculation years.")
    hr_gratuity_credit_account = fields.Many2one('account.account', help="Gratuity credit account")
    hr_gratuity_debit_account = fields.Many2one('account.account', help="Gratuity debit account")
    hr_gratuity_journal = fields.Many2one('account.journal', help="Gratuity journal")
    company_id = fields.Many2one('res.company', 'Company', required=False, help="Company")
    currency_id = fields.Many2one(related="company_id.currency_id",
                                  string="Currency", readonly=True, help="Currency")

    total_unpaid_leaves = fields.Char("Total Unpaid Leaves", compute="_get_unpaid_leaves")
    unpaid_leave_deduction = fields.Float("Unpaid Leave Amount", compute="_get_leave_amount")

    leaves_to_add = fields.Char("Leaves To Add", compute="_get_allocation_leaves")
    alloc_amount_to_add = fields.Float("Allocation Amount to Add", compute="_get_leave_amount")
    gratuity_line = fields.One2many('years.service.line', 'gratuity_id', string="Gratuity Calculation")
    leave_date = fields.Date('Leave Date')

    @api.depends('employee_id', 'total_working_years')
    def _get_allocation_leaves(self):
        """
            Get the total allocated leaves and subtract the used leaves
            from the allocated leaves and multiply it with daily wage and
            add that amount to the gratuity amount.
        """
        for rec in self:
            if rec.employee_id:
                hr_contract_id = self.env['hr.contract'].search(
                    [('employee_id', '=', self.employee_id.id), ('state', '=', 'open')])
                if hr_contract_id:
                    date_start = hr_contract_id[0].date_start
                    date_end = rec.employee_exit_date if rec.employee_exit_date else fields.date.today()
                    ds_to_de_dts_lst = self.get_ds_to_de_lst(date_start, date_end)
                    leaves_date_list = self._get_leaves_dates_list(rec.employee_id,
                                                                   date_start, date_end)
                    leaves_alloc_date_list = self._get_leaves_alloc_dates_lst(rec.employee_id,
                                                                              date_start, date_end)

                    # actual allocation days between contract start and contract end date
                    act_alloc_dts_lst = [rec for rec in leaves_alloc_date_list if rec in ds_to_de_dts_lst]

                    # get the dates on which leave is allocated but not taken
                    alloc_remaining = [rec for rec in act_alloc_dts_lst if rec not in leaves_date_list]
                    rec.leaves_to_add = len(alloc_remaining)
                else:
                    rec.leaves_to_add = 0
            else:
                rec.leaves_to_add = 0

    @api.depends('total_working_years')
    def _get_leave_amount(self):
        for rec in self:
            if rec.employee_id and rec.total_working_years > 0:
                employee_gratuity_amount = rec._get_employee_gratuity_amount()
                daily_wage = employee_gratuity_amount / (
                        rec.employee_gratuity_years * 12) / 30
                # daily_wage = rec.employee_basic_salary / rec.employee_gratuity_duration.employee_daily_wage_days
                rec.alloc_amount_to_add = int(rec.leaves_to_add) * daily_wage if rec.leaves_to_add else 0
                rec.unpaid_leave_deduction = int(rec.total_unpaid_leaves) * daily_wage if rec.total_unpaid_leaves else 0
                if rec.employee_id.contract_id and rec.employee_id.contract_id.state == 'open':
                    rec._onchange_employee_id()
            else:
                rec.alloc_amount_to_add = 0
                rec.unpaid_leave_deduction = 0

    def _get_leaves_alloc_dates_lst(self, emp=None, date_from=None, date_to=None):
        """
            we are expanding date_from and date_to, so
            it will not miss any allocation
        """
        leaves_allocation = self.env['hr.leave.allocation'].search([
            ('state', '=', 'validate'),
            ('date_from', '>=', date_from - timedelta(days=31)),
            ('date_to', '<=', date_to + timedelta(days=31)),
            ('employee_id', '=', emp.id)
        ])

        leaves_dates = []
        for leave in leaves_allocation:
            l_date_from = copy.deepcopy(leave.date_from)
            l_date_to = copy.deepcopy(leave.date_to)
            while l_date_from <= l_date_to:
                leaves_dates.append(l_date_from)
                l_date_from += timedelta(days=1)
        return leaves_dates

    @api.depends('employee_id', 'total_working_years')
    def _get_unpaid_leaves(self):
        """
            get the unpaid leaves that is taken by employee between his worked time period
            and will multiply that days with daily wage and will subtract that amount from
            gratuity amount.
        """
        for rec in self:
            if rec.employee_id:
                hr_contract_id = self.env['hr.contract'].search(
                    [('employee_id', '=', self.employee_id.id), ('state', '=', 'open')])
                if hr_contract_id:
                    date_start = hr_contract_id[0].date_start
                    date_end = fields.date.today()
                    ds_to_de_dts_lst = self.get_ds_to_de_lst(date_start, date_end)
                    leaves_date_list = self._get_leaves_dates_list(rec.employee_id,
                                                                   date_start, date_end)
                    dates_difference = [rec for rec in leaves_date_list if rec in ds_to_de_dts_lst]
                    rec.total_unpaid_leaves = len(dates_difference)
                else:
                    rec.total_unpaid_leaves = 0
            else:
                rec.total_unpaid_leaves = 0

    def _get_leaves_dates_list(self, emp=None, date_from=None, date_to=None):
        """
            expanding date_From and date_to, so it will
            not miss leave allocated
        """
        leaves = self.env['hr.leave'].search([
            ('state', '=', 'validate'),
            ('request_date_from', '>=', date_from - timedelta(days=31)),
            ('holiday_status_id.is_unpaid_leave', '=', True),
            ('request_date_to', '<=', date_to + timedelta(days=31)),
            ('employee_id', '=', emp.id)
        ])

        leaves_dates = []
        for leave in leaves:
            l_date_from = copy.deepcopy(leave.request_date_from)
            l_date_to = copy.deepcopy(leave.request_date_to)
            while l_date_from <= l_date_to:
                leaves_dates.append(l_date_from)
                l_date_from += timedelta(days=1)
        return leaves_dates

    @staticmethod
    def get_ds_to_de_lst(date_from=None, date_to=None):
        ds_to_de_dates = []
        p_date_from = copy.deepcopy(date_from)
        p_date_to = copy.deepcopy(date_to)

        while p_date_from <= p_date_to:
            ds_to_de_dates.append(p_date_from)
            p_date_from += timedelta(days=1)

        return ds_to_de_dates

    @api.model
    def create(self, vals):
        """ assigning the sequence for the record """
        vals['name'] = self.env['ir.sequence'].next_by_code('hr.gratuity')
        return super(EmployeeGratuity, self).create(vals)

    @api.depends('employee_id', 'employee_contract_type')
    @api.onchange('employee_id', 'employee_contract_type')
    def _onchange_employee_id(self):
        """ calculating the gratuity pay based on the contract and gratuity
        configurations """
        if self.employee_id.id:
            current_date = date.today()
            probation_ids = self.env['hr.training'].search([('employee_id', '=', self.employee_id.id)])
            contract_ids = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)])
            contract_sorted = contract_ids.sorted(lambda line: line.date_start)
            if not contract_sorted:
                raise Warning(_('No contracts found for the selected employee...!\n'
                                'Employee must have at least one contract to compute gratuity settelement.'))
            # self.employee_joining_date = joining_date = contract_sorted[0].date_start
            self.employee_joining_date = joining_date = self.employee_id.joining_date
            employee_probation_days = 0
            # find total probation days
            for probation in probation_ids:
                start_date = probation.start_date
                end_date = probation.end_date
                employee_probation_days += (end_date - start_date).days
            # get running contract
            hr_contract_id = self.env['hr.contract'].search(
                [('employee_id', '=', self.employee_id.id), ('state', '=', 'open')])
            if len(hr_contract_id) > 1 or not hr_contract_id:
                raise Warning(_('Selected employee have multiple or no running contracts!'))

            self.wage_type = hr_contract_id.wage_type
            if self.wage_type == 'hourly':
                self.employee_basic_salary = hr_contract_id.hourly_wage
            else:
                self.employee_basic_salary = hr_contract_id.basic

            if not self.employee_contract_type:
                self.employee_contract_type = self.employee_id.contract_type
            # if not hr_contract_id.date_end and not self.employee_contract_type:
            #     self.employee_contract_type = 'unlimited'

            if hr_contract_id.date_end:
                employee_working_days = (hr_contract_id.date_end - joining_date).days
            else:
                employee_working_days = (self.employee_exit_date - joining_date).days if self.employee_exit_date else (current_date - joining_date).days
            self.total_working_years = employee_working_days / 365
            self._get_unpaid_leaves()
            self.total_working_years = self.get_new_duration(self, self.total_unpaid_leaves)
            self.employee_probation_years = employee_probation_days / 365
            # employee_gratuity_years = (employee_working_days - employee_probation_days) / 365
            employee_gratuity_years = self.total_working_years - employee_probation_days
            self.employee_gratuity_years = employee_gratuity_years
            # else:
            #     employee_working_days = (current_date - joining_date).days
            #     self.total_working_years = employee_working_days / 365
            #     self._get_unpaid_leaves()
            #     self.total_working_years = self.get_new_duration(self, self.total_unpaid_leaves)
            #     self.employee_probation_years = employee_probation_days / 365
            #     # employee_gratuity_years = (employee_working_days - employee_probation_days) / 365
            #     employee_gratuity_years = self.total_working_years - employee_probation_days
            #     self.employee_gratuity_years = round(employee_gratuity_years, 2)

            gratuity_duration_id = False
            hr_accounting_configuration_id = self.env[
                'hr.gratuity.accounting.configuration'].search(
                [('active', '=', True), ('config_contract_type', '=', self.employee_contract_type),
                 '|', ('gratuity_end_date', '>=', current_date), ('gratuity_end_date', '=', False),
                 '|', ('gratuity_start_date', '<=', current_date), ('gratuity_start_date', '=', False)])
            if len(hr_accounting_configuration_id) > 1:
                raise UserError(_(
                    "There is a date conflict in Gratuity accounting configuration. "
                    "Please remove the conflict and try again!"))
            elif not hr_accounting_configuration_id:
                raise UserError(
                    _('No gratuity accounting configuration found '
                      'or please set proper start date and end date for gratuity configuration!'))
            # find configuration ids related to the gratuity accounting configuration
            self.employee_gratuity_configuration = hr_accounting_configuration_id.id
            conf_ids = hr_accounting_configuration_id.gratuity_configuration_table.mapped('id')
            hr_duration_config_ids = self.env['gratuity.configuration'].browse(conf_ids)
            for duration in hr_duration_config_ids:
                if duration.from_year and duration.to_year and duration.from_year <= self.total_working_years <= duration.to_year:
                    gratuity_duration_id = duration
                    break
                elif duration.from_year and not duration.to_year and duration.from_year <= self.total_working_years:
                    gratuity_duration_id = duration
                    break
                elif duration.to_year and not duration.from_year and self.total_working_years <= duration.to_year:
                    gratuity_duration_id = duration
                    break

            if gratuity_duration_id:
                self.employee_gratuity_duration = gratuity_duration_id.id
            else:
                raise Warning(_('No suitable gratuity durations found !'))
            # show warning when the employee's working years is less than
            # one year or no running employee found.
            if self.total_working_years < 1 and self.employee_id.id:
                raise Warning(_('Selected Employee is not eligible for Gratuity Settlement'))
            hr_accounting_gratuity = hr_accounting_configuration_id.gratuity_configuration_line.filtered(lambda line: line.company_id == self.env.company)
            if hr_accounting_gratuity:
                self.hr_gratuity_journal = hr_accounting_gratuity.gratuity_journal.id
                self.hr_gratuity_credit_account = hr_accounting_gratuity.gratuity_credit_account.id
                self.hr_gratuity_debit_account = hr_accounting_gratuity.gratuity_debit_account.id
            else:
                raise Warning(_('Pls Specify Accounts for Gratuity Settlement'))

            if self.employee_gratuity_duration and self.wage_type == 'hourly':
                if self.employee_gratuity_duration.employee_working_days != 0:
                    if self.employee_id.resource_calendar_id and self.employee_id.resource_calendar_id.hours_per_day:
                        daily_wage = self.employee_basic_salary * self.employee_id.resource_calendar_id.hours_per_day
                    else:
                        daily_wage = self.employee_basic_salary * 8
                    working_days_salary = daily_wage * self.employee_gratuity_duration.employee_working_days
                    gratuity_pay_per_year = working_days_salary * self.employee_gratuity_duration.days
                    employee_gratuity_amount = gratuity_pay_per_year * self.employee_gratuity_years
                    # self.employee_gratuity_amount = round(employee_gratuity_amount, 2)
                    # self.employee_gratuity_amount = round(
                    #     (employee_gratuity_amount + self.alloc_amount_to_add) - self.unpaid_leave_deduction, 2)
                    # self.employee_gratuity_amount = round(employee_gratuity_amount, 2)
                    self.employee_gratuity_amount = sum(self.gratuity_line.mapped('amount'))
                else:
                    raise Warning(_("Employee working days is not configured in "
                                    "the gratuity configuration..!"))
            elif self.employee_gratuity_duration and self.wage_type == 'monthly':
                if self.employee_gratuity_duration.employee_daily_wage_days != 0:
                    daily_wage = self.employee_basic_salary / self.employee_gratuity_duration.employee_daily_wage_days
                    working_days_salary = daily_wage * self.employee_gratuity_duration.employee_working_days
                    gratuity_pay_per_year = working_days_salary * self.employee_gratuity_duration.days
                    employee_gratuity_amount = gratuity_pay_per_year * self.employee_gratuity_years
                    # self.employee_gratuity_amount = round(
                    #     (employee_gratuity_amount + self.alloc_amount_to_add) - self.unpaid_leave_deduction, 2)
                    # self.employee_gratuity_amount = round(employee_gratuity_amount, 2)
                    self.employee_gratuity_amount = sum(self.gratuity_line.mapped('amount'))
                else:
                    raise Warning(_("Employee wage days is not configured in "
                                    "the gratuity configuration..!"))

    @api.onchange('employee_id', 'employee_contract_type')
    def _onchange_emp_id(self):
        for rec in self:
            if rec.employee_id:
                join_date = rec.employee_id.joining_date if rec.employee_id else date.today()
                exp_lv_date = rec.employee_exit_date if rec.employee_exit_date else date.today()
                rec.gratuity_line = None
                lev_in_5_tenure, lev_more_5_tenure = self.get_leaves(rec, join_date, exp_lv_date)
                start_date = datetime(join_date.year, join_date.month, join_date.day)
                end_date = datetime(exp_lv_date.year, exp_lv_date.month, exp_lv_date.day)
                delta = end_date - start_date
                tenure = round((delta).days / 365, 2)
                days, gratuity_id, line_id = self.gratuity_configuration_line(rec.total_working_years)
                gratuity_amount = self._get_employee_gratuity_amount()
                if gratuity_id:

                    if tenure > 5:
                        rec.gratuity_line = [(0, 0, {
                            'name': 'Gratuity more than years',
                            'gratuity_config_id': gratuity_id,
                            'gratuity_line_id': line_id,
                            'years': rec.total_working_years,
                            'leaves_done': lev_more_5_tenure,
                            'amount': ((rec.total_working_years)* gratuity_amount),
                        })]
                    else:
                        rec.gratuity_line = [(0, 0, {
                            'name': 'Gratuity for Up to 5 years',
                            'gratuity_config_id': gratuity_id,
                            'gratuity_line_id': line_id.id,
                            'years': rec.total_working_years,
                            'leaves_done': lev_in_5_tenure,
                            'amount': round(gratuity_amount,2),
                        })]

            # get gratuity days less than 5 years tenure and greater than 5 years of tenure
            # gr_days_in_5_tenure, gr_more_5_tenure = self.get_gratuity_days(rec, join_date, exp_lv_date)
            # if 1 < rec.total_working_years > 3:
            #     if 5 >= rec.total_working_years >= 3:
            #         # get leaves in less than 5 and greater than 5 tenure logic started here
            #         days, gratuity_id, line_id = self.gratuity_configuration_line(rec.total_working_years)
            #         rec.gratuity_line = [(0, 0, {
            #             'name': 'Gratuity for Up to 5 years',
            #             'gratuity_config_id': gratuity_id,
            #             'gratuity_line_id': line_id,
            #             'leaves_done': lev_in_5_tenure,
            #             'years': rec.total_working_years,
            #             'amount': ((rec.total_working_years - (
            #                 lev_in_5_tenure / 365 if lev_in_5_tenure > 0 else 0)) * days) * rec.employee_id.contract_id.basic / 30,
            #         })]
            #     elif 5 <= rec.total_working_years < 6:
            #         days, gratuity_id, line_id = self.gratuity_configuration_line(rec.total_working_years)
            #         rec.gratuity_line = [(0, 0, {
            #             'name': 'Gratuity for Up to 6 years',
            #             'gratuity_config_id': gratuity_id,
            #             'gratuity_line_id': line_id,
            #             'years': rec.total_working_years,
            #             'amount': ((rec.total_working_years - lev_in_5_tenure / 365)
            #                        * days) * rec.employee_id.contract_id.basic / 30,
            #         })]
            #     elif rec.total_working_years >= 5 and rec.total_working_years >= 6:
            #         five_yrs_comp_date = self.five_years_com_date(rec.employee_id.joining_date, 5)
            #         less_5_y_days = five_yrs_comp_date - rec.employee_id.joining_date
            #         more_5_y_days = rec.leave_date - five_yrs_comp_date + timedelta(days=1)
            #         in_5, gratuity_id, line_id = self.gratuity_configuration_line(less_5_y_days.days / 365)
            #         more_5, m_gratuity_id, m_line_id = self.gratuity_configuration_line(more_5_y_days.days / 365)
            #
            #         # get leaves in less than 5 and greater than 5 tenure logic started here
            #         lev_in_5_tenure, lev_more_5_tenure = self.get_leaves(rec, join_date, exp_lv_date)
            #
            #         l_5_years = (less_5_y_days.days - lev_in_5_tenure) / 365
            #         m_5_years = (more_5_y_days.days - lev_more_5_tenure) / 365
            #
            #         rec.gratuity_line = [(0, 0, {
            #             'name': 'Gratuity up to 5 years',
            #             'gratuity_config_id': gratuity_id,
            #             'gratuity_line_id': line_id,
            #             'years': l_5_years,
            #             'leaves_done': lev_in_5_tenure,
            #             'amount': (l_5_years * in_5) * rec.employee_id.contract_id.basic / 30,
            #         }), (0, 0, {
            #             'name': 'Gratuity for more than 5 years',
            #             'gratuity_config_id': m_gratuity_id,
            #             'gratuity_line_id': m_line_id,
            #             'leaves_done': lev_more_5_tenure,
            #             'years': m_5_years,
            #             'amount': (m_5_years * more_5) * rec.employee_id.contract_id.basic / 30,
            #         })]
            # else:
            #     days, gratuity_id, line_id = self.gratuity_configuration_line(rec.total_working_years)
            #     rec.gratuity_line = [(0, 0, {
            #         'name': 'Gratuity for Up to 3 years',
            #         'gratuity_config_id': gratuity_id,
            #         'gratuity_line_id': line_id,
            #         'years': rec.total_working_years,
            #         'leaves_done': lev_in_5_tenure,
            #         'amount': ((rec.total_working_years - (lev_in_5_tenure / 365)) * days)
            #                   * rec.employee_id.contract_id.basic / 30,
            #     })]

    def get_gratuity_days(self, rec=None, join_date=None, exp_lv_date=None):
        tenure = self.calculate_tenure(join_date, exp_lv_date)
        tenure = round(tenure.days / 365, 2) if tenure else 0
        if tenure < 5:
            return tenure * 365, 0
        elif tenure > 5:
            five_yrs_comp_date = self.five_years_com_date(join_date, 5)
            less_5_y_days = five_yrs_comp_date - join_date
            more_5_y_days = exp_lv_date - five_yrs_comp_date + timedelta(days=1)
            return less_5_y_days.days, more_5_y_days.days

    def calculat_gratuity_days(self,years_in_service, total_worked_days_lt, total_worked_days_gt):
        if years_in_service < 5:
            grat_lt_days = 105 * total_worked_days_lt / 1825
            grat_gt_days = 0.00
        else:
            grat_gt_days = (total_worked_days_gt * (30 * (years_in_service - 5))) / (365 * (years_in_service - 5))
            grat_lt_days = 0.00
        return grat_gt_days, grat_lt_days



    @staticmethod
    def calculate_tenure(join_date, lve_date):
        if join_date and lve_date:
            return lve_date - join_date
        else:
            return 0

    def get_leaves(self, rec=None, join_date=None, exp_lv_date=None):
        tenure = self.calculate_tenure(join_date, exp_lv_date)
        tenure = round(tenure.days / 365, 2) if tenure else 0
        if tenure < 5:
            less_t_5 = sum(self.env['hr.leave'].search([
                ('state', '=', 'validate'), ('holiday_status_id.is_unpaid_leave', '=', True),
                ('employee_id', '=', rec.employee_id.id), ('request_date_from', '>=', join_date),
                ('request_date_to', '<=', exp_lv_date)]).mapped('number_of_days'))
            return less_t_5, 0
        elif tenure > 5:
            five_yrs_comp_date = self.five_years_com_date(join_date, 5)
            five_leaves = sum(self.env['hr.leave'].search(
                [('employee_id', '=', rec.employee_id.id),
                 ('state', '=', 'validate'), ('holiday_status_id.is_unpaid_leave', '=', True),
                 ('request_date_from', '>=', join_date),
                 ('request_date_to', '<=', five_yrs_comp_date)
                 ]).mapped('number_of_days'))

            five_more_leaves = sum(self.env['hr.leave'].search(
                [('employee_id', '=', rec.employee_id.id),
                 ('state', '=', 'validate'), ('holiday_status_id.is_unpaid_leave', '=', True),
                 ('request_date_from', '>=', five_yrs_comp_date + timedelta(days=1)),
                 ('request_date_to', '<=', exp_lv_date)
                 ]).mapped('number_of_days'))
            return five_leaves, five_more_leaves

    @staticmethod
    def five_years_com_date(hire_date, years):
        tenure_completion_date = hire_date + timedelta(days=years * 365)
        return tenure_completion_date

    def gratuity_configuration_line(self, years_in_service):
        gratuity_config = self.env['hr.gratuity.accounting.configuration'].search(
            [('config_contract_type', '=', self.employee_contract_type),
             ('gratuity_start_date', '<=', fields.Datetime.now().date())
             ])
        if gratuity_config and gratuity_config.gratuity_end_date:
            gratuity_config = gratuity_config.filtered(
                lambda rec: rec.gratuity_end_date >= fields.Datetime.now().date())
        line = gratuity_config.gratuity_configuration_table.filtered(
            lambda rec: rec.from_year <= years_in_service <= rec.to_year)
        if line:
            gratuity_days = line[0].days
            return gratuity_days, gratuity_config.id, line[0]
        return 0, None, None

    def get_new_duration(self, rec=None, date_len=None):
        # leave_days = int(date_len) if date_len else 0
        # work_years_in_months = rec.total_working_years * 12
        # work_years_in_days = work_years_in_months * 30
        # days_after_lve_deduct = work_years_in_days - leave_days
        # convert_back_to_month = days_after_lve_deduct / 12
        # convert_back_to_years = convert_back_to_month / 30
        # return convert_back_to_years
        join_date = rec.employee_id.joining_date
        if not join_date:
            raise UserError(_(
                "Pls Set Join Date For Employee"))
        if rec.leave_date:
            exp_lv_date = rec.leave_date
        elif rec.employee_exit_date:
            exp_lv_date = rec.employee_exit_date
        else:
            exp_lv_date = fields.Datetime.now().date()
        # exp_lv_date = rec.leave_date if rec.leave_date else rec.employee_exit_date
        start_date = datetime(join_date.year, join_date.month, join_date.day)
        end_date = datetime(exp_lv_date.year, exp_lv_date.month, exp_lv_date.day)
        delta = end_date - start_date
        years_in_service = delta.days / 365
        return years_in_service

    def _get_employee_gratuity_amount(self):
        # daily_wage = self.employee_basic_salary / self.employee_gratuity_duration.employee_daily_wage_days
        gratuity_per_day = (self.employee_id.contract_id.basic * 12) / 365
        # working_days_salary = daily_wage * self.employee_gratuity_duration.employee_working_days
        gratuity_pay_per_year = gratuity_per_day * self.employee_gratuity_duration.days
        employee_gratuity_amount = gratuity_pay_per_year * self.employee_gratuity_years
        return employee_gratuity_amount

    # Changing state to submit
    def submit_request(self):
        self.write({'state': 'submit'})

    # Canceling the gratuity request
    def cancel_request(self):
        self.write({'state': 'cancel'})

    # Set the canceled request to draft
    def set_to_draft(self):
        self.write({'state': 'draft'})

    # function for creating the account move with gratuity amount and
    # account credentials
    def approved_request(self):
        for hr_gratuity_id in self:
            debit_vals = {
                'name': hr_gratuity_id.employee_id.name,
                'account_id': hr_gratuity_id.hr_gratuity_debit_account.id,
                'partner_id': hr_gratuity_id.employee_id.address_home_id.id or False,
                'journal_id': hr_gratuity_id.hr_gratuity_journal.id,
                'date': date.today(),
                'debit': hr_gratuity_id.employee_gratuity_amount > 0.0 and hr_gratuity_id.employee_gratuity_amount or 0.0,
                'credit': hr_gratuity_id.employee_gratuity_amount < 0.0 and -hr_gratuity_id.employee_gratuity_amount or 0.0,
            }
            credit_vals = {
                'name': hr_gratuity_id.employee_id.name,
                'account_id': hr_gratuity_id.hr_gratuity_credit_account.id,
                'partner_id': hr_gratuity_id.employee_id.address_home_id.id or False,
                'journal_id': hr_gratuity_id.hr_gratuity_journal.id,
                'date': date.today(),
                'debit': hr_gratuity_id.employee_gratuity_amount < 0.0 and -hr_gratuity_id.employee_gratuity_amount or 0.0,
                'credit': hr_gratuity_id.employee_gratuity_amount > 0.0 and hr_gratuity_id.employee_gratuity_amount or 0.0,
            }
            vals = {

                'name': 'Gratuity for' + ' ' + hr_gratuity_id.employee_id.name,
                'narration': hr_gratuity_id.employee_id.name,
                'ref': hr_gratuity_id.name,
                'partner_id': hr_gratuity_id.employee_id.address_home_id.id or False,
                'journal_id': hr_gratuity_id.hr_gratuity_journal.id,
                'date': date.today(),
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)],
            }
            move = hr_gratuity_id.env['account.move'].create(vals)
            move.post()
        self.write({'state': 'approve'})


class EmployeeContractWage(models.Model):
    _inherit = 'hr.contract'

    # structure_type_id = fields.Many2one('hr.payroll.structure.type', string="Salary Structure Type")
    company_country_id = fields.Many2one('res.country', string="Company country", related='company_id.country_id',
                                         readonly=True)
    wage_type = fields.Selection([('monthly', 'Monthly Fixed Wage'), ('hourly', 'Hourly Wage')])
    hourly_wage = fields.Monetary('Hourly Wage', digits=(16, 2), default=0, required=True, tracking=True,
                                  help="Employee's hourly gross wage.")
