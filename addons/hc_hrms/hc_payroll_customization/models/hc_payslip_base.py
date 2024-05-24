# -*- coding: utf-8 -*-

from odoo.addons.hr_payroll.models.hr_payslip import HrPayslip as HcHrPayslip

""" Inherited from the base class to avoid the warnings based on the contract,
 since our integration with the attendance module, all needed contracts will be updated there"""


# def action_payslip_done(self):
#     # invalid_payslips = self.filtered(lambda p: p.contract_id and (p.contract_id.date_start > p.date_to or (p.contract_id.date_end and p.contract_id.date_end < p.date_from)))
#     # if invalid_payslips:
#     #     raise ValidationError(_('The following employees have a contract outside of the payslip period:\n%s',
#     #                             '\n'.join(invalid_payslips.mapped('employee_id.name'))))
#     # if any(slip.contract_id.state == 'cancel' for slip in self):
#     #     raise ValidationError(_('You cannot validate a payslip on which the contract is cancelled'))
#     # if any(slip.state == 'cancel' for slip in self):
#     #     raise ValidationError(_("You can't validate a cancelled payslip."))
#     self.write({'state': 'done'})
#
#     line_values = self._get_line_values(['NET'])
#
#     self.filtered(lambda p: not p.credit_note and line_values['NET'][p.id]['total'] < 0).write(
#         {'has_negative_net_to_report': True})
#     self.mapped('payslip_run_id').action_close()
#     # Validate work entries for regular payslips (exclude end of year bonus, ...)
#     regular_payslips = self.filtered(lambda p: p.struct_id.type_id.default_struct_id == p.struct_id)
#     work_entries = self.env['hr.work.entry']
#     for regular_payslip in regular_payslips:
#         work_entries |= self.env['hr.work.entry'].search([
#             ('date_start', '<=', regular_payslip.date_to),
#             ('date_stop', '>=', regular_payslip.date_from),
#             ('employee_id', '=', regular_payslip.employee_id.id),
#         ])
#     if work_entries:
#         work_entries.action_validate()
#
#     if self.env.context.get('payslip_generate_pdf'):
#         if self.env.context.get('payslip_generate_pdf_direct'):
#             self._generate_pdf()
#         else:
#             self.write({'queued_for_pdf': True})
#             payslip_cron = self.env.ref('hr_payroll.ir_cron_generate_payslip_pdfs', raise_if_not_found=False)
#             if payslip_cron:
#                 payslip_cron._trigger()
#
#
# HcHrPayslip.action_payslip_done = action_payslip_done
