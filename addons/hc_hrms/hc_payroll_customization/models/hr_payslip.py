# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.addons.hr_payroll.models.browsable_object import BrowsableObject
from odoo.exceptions import UserError
from odoo.tools.misc import format_date


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    payroll_period_id = fields.Many2one('hc.payroll.period', string="Payroll Period")


    @api.depends('date_to')
    def _compute_name(self):
        res = super(HrPayslip, self)._compute_name()
        for rec in self.filtered(lambda p: p.employee_id and p.date_to):
            if rec.employee_id and rec.name and rec.date_to:
                lang = rec.employee_id.sudo().address_home_id.lang or self.env.user.lang
                payslip_name = rec.struct_id.payslip_name or _('Salary Slip')
                rec.name = '%(payslip_name)s - %(employee_name)s - %(dates)s' % {
                    'payslip_name': payslip_name,
                    'employee_name': rec.employee_id.name,
                    'dates': format_date(self.env, rec.date_to, date_format="MMMM y", lang_code=lang)
                }

        return res

    @api.onchange('payroll_period_id')
    def _onchange_payroll_period_id(self):
        if self.payroll_period_id:
            self.date_from = self.payroll_period_id.date_from
            self.date_to = self.payroll_period_id.date_to

    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        if self.contract_id.struct_id:
            self.struct_id = self.contract_id.struct_id.id

    def _get_localdict(self):
        employee = self.employee_id
        period_id = self.payroll_period_id
        contracts = self.env['hr.contract'].search([('employee_id', '=', employee.id)])
        attendances = self.env['hr.attendance'].search(
            [('payroll_period_id', '=', period_id.id), ('state', '=', 'processed')])
        ot_types = self.env['hc.over.time.type'].search([])
        res = super(HrPayslip, self)._get_localdict()
        res['attendances'] = BrowsableObject(employee.id, attendances, self.env)
        res['ot_type'] = BrowsableObject(employee.id, ot_types, self.env)
        return res

    def compute_sheet(self):
        for rec in self:
            try:
                employee = rec.employee_id
                attendances = self.env['hr.attendance'].search(
                    [('employee_id', '=', employee.id),
                     # ('state', '=', 'processed'),
                     ('payroll_period_id', '=', rec.payroll_period_id.id),
                     ('is_flexible_day', '=', True)])
                worked_days = attendances.filtered(lambda x: x.consumed_flexible_day)
                worked_days_len = len(worked_days)
                max_unpaid_leave_2 = 0
                max_unpaid_leave_1 = 0
                for att in attendances.filtered(lambda x: not x.consumed_flexible_day):
                    mandatory_hour = 8
                    if worked_days_len < 2:
                        if worked_days_len == 0:
                            if not att.consumed_flexible_day:
                                if not max_unpaid_leave_2 == 2:
                                    att.write({
                                        'state': 'processed',
                                        'net_working_days': 1,
                                        'unpaid_leave': True
                                    })
                                    max_unpaid_leave_2 += 1
                                    continue
                        if worked_days_len == 1:
                            if not att.consumed_flexible_day:
                                if not max_unpaid_leave_1 == 1:
                                    att.write({
                                        'state': 'processed',
                                        'net_working_days': 0,
                                        'unpaid_leave': True
                                    })
                                    max_unpaid_leave_1 += 1
                                    continue
                    att.write({'mandatory_hours': mandatory_hour,
                               'actual_mandatory_hours': mandatory_hour,
                               'net_working_days': 0,
                               'total_worked_hours': mandatory_hour,
                               'is_weekend': True,
                               'state': 'processed'})
            except:
                return super(HrPayslip, self).compute_sheet()
        return super(HrPayslip, self).compute_sheet()

    def action_payslip_done(self):
        res = super(HrPayslip, self).action_payslip_done()
        for rec in self:
            """ Creating Compensatory Off For Friday OT """
            employee = rec.employee_id
            attendances = self.env['hr.attendance'].search(
                [('employee_id', '=', employee.id), ('state', '=', 'processed'),
                 ('payroll_period_id', '=',
                  rec.payroll_period_id.id)])  # State
            max_weekend_eligible = employee.branch_id.max_weekends_eligible
            total_weekends = len(attendances.filtered(lambda x: x.is_weekend_special_pay))
            if total_weekends > max_weekend_eligible:
                time_off_type = self.env['hr.leave.type'].sudo().search([('is_compensatory_timeoff_type', '=', True)], limit=1)
                if time_off_type:
                    Allocation = self.env['hr.leave.allocation']
                    allocation = Allocation.search(
                        [('employee_id', '=', employee.id), ('holiday_status_id', '=', time_off_type.id),
                         ('date_from', '<=', self.payroll_period_id.date_from), ('state', '=', 'draft')])
                    if allocation:
                        allocation.write({
                            'employee_id': employee.id,
                            'name': 'Accrued From the Friday Working',
                            'holiday_status_id': time_off_type.id,
                            'allocation_type': 'accrual',
                            'number_of_days': allocation.number_of_days + (total_weekends - max_weekend_eligible),
                        })
                    else:
                        Allocation.create({
                            'employee_id': employee.id,
                            'name': 'Accrued From the Friday Working',
                            'holiday_status_id': time_off_type.id,
                            'allocation_type': 'accrual',
                            'number_of_days': total_weekends - max_weekend_eligible,
                        })
                # Checking and Creating Warning Record for the Employee
            # self.missed_hour_warning(attendances, employee)
            # self.kh_late_warning(attendances, employee)
            for att in attendances:
                att.write({'state': 'submit'})
        return res

    def action_payslip_paid(self):
        for rec in self:
            attendances = self.env['hr.attendance'].search(
                [('employee_id', '=', rec.employee_id.id), ('state', '=', 'submit'),
                 ('payroll_period_id', '=', rec.payroll_period_id.id)])
            for att in attendances:
                att.write({'state': 'confirmed'})
        res = super(HrPayslip, self).action_payslip_paid()
        return res

    def action_payslip_cancel(self):
        for rec in self:
            attendances = self.env['hr.attendance'].search(
                [('employee_id', '=', rec.employee_id.id), ('state', '=', 'submit'),
                 ('payroll_period_id', '=', rec.payroll_period_id.id)])
            for att in attendances:
                att.write({'state': 'processed'})
        res = super(HrPayslip, self).action_payslip_cancel()
        return res
    #
    # def missed_hour_warning(self, attendances, employee):
    #     total_missed_hours = 0
    #     allowed_missed_hour = employee.branch_id.total_hours_absence_limit
    #     warning_count = employee.warning_count
    #     warning_level = None
    #     for att in attendances:
    #         if att.missed_effort:
    #             total_missed_hours += att.missed_effort
    #     if total_missed_hours > allowed_missed_hour:
    #         warning_count += 1
    #         if warning_count == 1:
    #             warning_level = employee.branch_id.month1
    #         elif warning_count == 2:
    #             warning_level = employee.branch_id.month2
    #         elif warning_count == 3:
    #             warning_level = employee.branch_id.month3
    #         elif warning_count == 4:
    #             warning_level = employee.branch_id.month4
    #         elif warning_count == 5:
    #             warning_level = employee.branch_id.month5
    #         elif warning_count == 6:
    #             warning_level = employee.branch_id.month6
    #
    #     if warning_count >= 1:
    #         if not warning_level:
    #             raise UserError(
    #                 _("Please Configure a Warning Level in Warning/Notices to Sent Alert/Warning to the Employee for Exceeding Total Hours of Absence Accumulated"))
    #         type = self.env['hc.warning.type'].search([('is_attendance_warning', '=', True)], limit=1)
    #         if not type:
    #             raise UserError(
    #                 _("Please Configure a Warning Type in Warning/Notices to Sent Alert/Warning to the Employee for Exceeding Total Hours of Absence Accumulated"))
    #         self.env['hc.warning'].create({
    #             'employee_id': employee.id,
    #             'department_id': employee.department_id.id,
    #             'branch_id': employee.branch_id.id,
    #             'message': warning_level.level if warning_level else '' + ' - ' + type.message,
    #             'type_id': type.id,
    #             'warning_level_ids': [
    #                 (0, 0, {
    #                     'warning_level_id': warning_level.id if warning_level else False,
    #                 })]
    #         })
    #     employee.write({'warning_count': warning_count})
    #
    # def kh_late_warning(self, attendances, employee):
    #     for att in attendances:
    #         branch_id = att.branch_id
    #         date = att.date
    #         key_holder = branch_id.key_holder_ids.filtered(
    #             lambda line: line.date_to >= date and line.date_from <= date and line.employee_id.id == employee.id)
    #         kh_warning_count = key_holder.kh_warning_count
    #         kh_allowed_late = branch_id.kh_allowed_late
    #         if att.late_hour:
    #             if key_holder:
    #                 kh_warning_count += 1
    #                 if kh_warning_count > kh_allowed_late:
    #                     type = self.env['hc.warning.type'].search([('is_kh_warning', '=', True)], limit=1)
    #                     if not type:
    #                         raise UserError(
    #                             _("Please Configure a Warning Type in Warning/Notices to Sent Alert/Warning to the Employee - Key Holder for Exceeding Allowed Late Punch"))
    #                     self.env['hc.warning'].create({
    #                         'employee_id': employee.id,
    #                         'department_id': employee.department_id.id,
    #                         'branch_id': employee.branch_id.id,
    #                         'message': 'Warning Count -' + str(int(kh_warning_count)) + ' ' + type.message,
    #                         'type_id': type.id,
    #                     })
    #             key_holder.write({'kh_warning_count': kh_warning_count})
