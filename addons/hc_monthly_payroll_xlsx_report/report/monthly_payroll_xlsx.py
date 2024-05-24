# -*- coding: utf-8 -*-
from odoo import models, fields
from datetime import datetime, time

LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


def excel_style(row, col):
    """ Convert given row and column number to an Excel-style cell name. """
    result = []
    while col:
        col, rem = divmod(col - 1, 26)
        result[:0] = LETTERS[rem]
    return ''.join(result) + str(row)


class MonthlyPayrollWizard(models.AbstractModel):
    _name = "report.hc_monthly_payroll_xlsx_report.payroll_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = " Non Moving Product Report"

    def generate_xlsx_report(self, workbook, data, wizard):
        ##FORMATS##
        heading1_format = workbook.add_format(
            {'align': 'center', 'size': 16, 'bold': True, 'bg_color': '#89CFF0'})
        heading_format = workbook.add_format(
            {'align': 'center', 'size': 10, 'bold': True, 'bg_color': '#89CFF0'})
        heading_format.set_align('center')
        heading_format.set_align('top')
        heading_format.set_top()
        heading_format.set_bottom()
        heading_format.set_left()
        heading_format.set_right()
        sub_heading_format = workbook.add_format({'size': 10, 'bold': True, 'bg_color': '#89CFF0'})
        text1 = workbook.add_format({'align': 'center', 'size': 10})
        text2 = workbook.add_format({'size': 10})
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy', 'size': 10, 'align': 'center'})
        no_format = workbook.add_format({'num_format': '#,##0.0', 'size': 10, 'align': 'center'})
        normal_num_bold = workbook.add_format({'bold': True, 'num_format': '#,##0.00'})
        ##FORMATS END##
        worksheet = workbook.add_worksheet("Monthly Payroll Report")
        ending_col = excel_style(1, 20)
        worksheet.merge_range('A2:%s' % (ending_col), "Monthly Payroll Report", heading1_format)
        payroll_period = wizard.payroll_period
        from_date = wizard.date_start
        to_date = wizard.date_end
        company_id = wizard.company_id
        worksheet.merge_range(3, 0, 3, 1, "Payroll Period :" + str(payroll_period.code), sub_heading_format)
        row = 5
        worksheet.set_column('A5:A5', 13)
        worksheet.set_column('B5:C5', 22)
        worksheet.set_column('D5:D5', 35)
        worksheet.set_column('E5:G5', 25)
        worksheet.set_column('H5:AF5', 15)
        worksheet.set_row(row, 35)
        worksheet.write(row, 0, 'Emp.Code', heading_format)
        worksheet.write(row, 1, 'Business Unit/\n Work Location', heading_format)
        worksheet.write(row, 2, 'visa sponsor', heading_format)
        worksheet.write(row, 3, 'Name', heading_format)
        worksheet.write(row, 4, 'Department', heading_format)
        worksheet.write(row, 5, 'Designation', heading_format)
        worksheet.write(row, 6, 'Date of\n joining', heading_format)
        worksheet.write(row, 7, 'Worked Days', heading_format)
        worksheet.write(row, 8, 'Sick Days', heading_format)
        worksheet.write(row, 9, 'Unpaid\n/Absent', heading_format)
        worksheet.write(row, 10, 'Annual/\nHoliday Leave', heading_format)
        worksheet.write(row, 11, 'Basic Actual', heading_format)
        worksheet.write(row, 12, 'Living Out \nAllowance Actual', heading_format)
        worksheet.write(row, 13, 'Other Allowance\n Actual', heading_format)
        worksheet.write(row, 14, 'Gross Actual', heading_format)
        worksheet.write(row, 15, 'Ticket Earned', heading_format)
        worksheet.write(row, 16, 'Bonus Earned', heading_format)
        worksheet.write(row, 17, 'Tips Earned', heading_format)
        worksheet.write(row, 18, 'Euro Salary\n Adjustment', heading_format)
        worksheet.write(row, 19, 'Other\n Reimbursement\n / Payments', heading_format)
        worksheet.write(row, 20, 'Temporary/\nPermanent\n Allowance\n Earned', heading_format)
        worksheet.write(row, 21, 'Last Month\n Arrears', heading_format)
        worksheet.write(row, 22, 'Part Time Pay', heading_format)
        worksheet.write(row, 23, 'Annual Leave\n Encashment', heading_format)
        worksheet.write(row, 24, 'Yearly Bonus', heading_format)
        worksheet.write(row, 25, 'Total Earned', heading_format)
        worksheet.write(row, 26, 'Gross Earned', heading_format)
        worksheet.write(row, 27, 'Loss of Pay\n(Absent)', heading_format)
        worksheet.write(row, 28, 'Loan Amount\n Deduct', heading_format)
        worksheet.write(row, 29, 'Other Deduction', heading_format)
        worksheet.write(row, 30, 'Total Deduction', heading_format)
        worksheet.write(row, 31, 'Net Salary -\n Present\n Month', heading_format)
        row += 1
        company = self.env.company.id
        payslips = self.env['hr.payslip'].search(
            [('date_from', '<=', from_date), ('date_to', '>=', to_date), ('company_id', '=', company)])
        if not payslips:
            return False
        for payslip in payslips:
            attendance = self.env['hr.attendance'].search([('date', '>=', from_date),
                                                           ('date', '<=', to_date),
                                                           ('employee_id', '=', payslip.employee_id.id)])
            leaves = self.env['hr.leave'].search(
                [('employee_id', '=', payslip.employee_id.id), ('request_date_from', '>=', from_date),
                 ('request_date_to', '<=', to_date),
                 ('state', '=', 'validate')])
            leave_days = sum(leaves.mapped('number_of_days'))
            unpaid_leaves = sum(leaves.filtered(lambda r: r.holiday_status_id.unpaid == True).mapped(
                    'number_of_days'))
            annual_leave_days = sum(leaves.filtered(lambda r: r.holiday_status_id.is_annual_leave == True).mapped(
                'number_of_days'))
            sick_leave = sum(leaves.filtered(lambda r: r.holiday_status_id.is_sick_leave == True).mapped(
                'number_of_days'))

            # annual_leave = attendance.filtered(lambda r: r.annual_leave == True)
            # annual_leave_days = len(annual_leave)
            # leave_days = attendance.filtered(lambda r: r.time_off == True)
            # unpaid_leave = leave_days.filtered(lambda r: r.unpaid_leave == True)
            # unpaid_leaves = len(unpaid_leave)
            work_days = len(attendance) - leave_days
            contract = payslip.contract_id

            living_allowance = contract.salary_rule_ids.filtered(lambda r: r.salary_rule_id.code == 'ACC')
            other_allowance = contract.salary_rule_ids.filtered(lambda r: r.salary_rule_id.code == 'TRA')

            temporary_allowance = contract.salary_rule_ids.filtered(lambda r: r.salary_rule_id.code == 'ALTEMP')
            temporary_allowance_amount = temporary_allowance.amount

            unpaid_leave_deduction = payslip.input_line_ids.filtered(lambda r: r.input_type_id.code == 'DED1')
            # total_deduction = payslip.line_ids.filtered(lambda r: r.code == 'DEDT')
            # total_deduction_amount = total_deduction.amount
            gross_amount = payslip.line_ids.filtered(lambda r: r.code == 'GROSS')
            gross_amount = gross_amount.amount
            other_allw_deduction = payslip.line_ids.filtered(lambda r: r.code == 'TRA')
            other_temp_deduction = payslip.line_ids.filtered(lambda r: r.code == 'ALTEMP')
            live_allw_deduction = payslip.line_ids.filtered(lambda r: r.code == 'ACC')
            basic_deduction = payslip.line_ids.filtered(lambda r: r.code == 'BASIC')
            total = payslip.contract_id.total_salary
            total_deduction_amount = total - (other_allw_deduction.amount +
                                                     other_temp_deduction.amount + live_allw_deduction.amount + basic_deduction.amount)

            euro_adjustment = payslip.input_line_ids.filtered(lambda r: r.input_type_id.code == 'DED2')
            euro_adjustment_amount = euro_adjustment.amount

            part_time_pay = payslip.line_ids.filtered(lambda r: r.code == 'PTPAY')
            part_time_pay = part_time_pay.amount

            al_salary = payslip.line_ids.filtered(lambda r: r.code == 'AL')
            al_salary = al_salary.amount

            tips = payslip.input_line_ids.filtered(lambda r: r.input_type_id.code == 'TIPS')
            tip_amount = tips.amount

            bonus = payslip.input_line_ids.filtered(lambda r: r.input_type_id.code == 'BNSDNC')
            bonus_amount = bonus.amount

            ticket_earned = payslip.input_line_ids.filtered(lambda r: r.input_type_id.code == 'TKT1')
            ticket_earned_amount = ticket_earned.amount

            other_reimbursement = payslip.input_line_ids.filtered(lambda r: r.input_type_id.code == 'OTHREIMB')
            other_reimbursement_amount = other_reimbursement.amount

            medical_reimbursement = payslip.line_ids.filtered(lambda r: r.code == 'MEDREIMB')
            medical_reimbursement = medical_reimbursement.amount

            yearly_bonus = payslip.input_line_ids.filtered(lambda r: r.input_type_id.code == 'BNSYRL')
            yearly_bonus = yearly_bonus.amount

            last_salary_arrears = payslip.input_line_ids.filtered(lambda r: r.input_type_id.code == 'PMSALAR')
            last_salary_arrears_amount = last_salary_arrears.amount

            living_out_adjustment = payslip.input_line_ids.filtered(lambda r: r.input_type_id.code == 'LIVADJ')
            living_out_adjustment = living_out_adjustment.amount

            salary_conversion = payslip.input_line_ids.filtered(lambda r: r.input_type_id.code == 'SALC')
            salary_conversion = salary_conversion.amount

            total_earned = last_salary_arrears_amount + yearly_bonus + medical_reimbursement + other_reimbursement_amount + ticket_earned_amount + bonus_amount + tip_amount + al_salary + part_time_pay + living_out_adjustment + salary_conversion

            loan_amount = payslip.input_line_ids.filtered(lambda r: r.input_type_id.code == 'LOANINS')
            loan_amount = loan_amount.amount
            other_deduction1 = payslip.input_line_ids.filtered(lambda r: r.input_type_id.code == 'INSD')
            other_deduction2 = payslip.input_line_ids.filtered(lambda r: r.input_type_id.code == 'TKTD')
            other_deduction3 = payslip.input_line_ids.filtered(lambda r: r.input_type_id.code == 'HRAD')
            other_deduction4 = payslip.input_line_ids.filtered(lambda r: r.input_type_id.code == 'VISA')
            other_deduction5 = payslip.input_line_ids.filtered(lambda r: r.input_type_id.code == 'GPSSA')
            other_deduction6 = payslip.input_line_ids.filtered(lambda r: r.input_type_id.code == 'RTAD')
            total_other_deduction_amount = other_deduction1.amount + other_deduction2.amount + other_deduction3.amount + other_deduction4.amount + other_deduction5.amount + other_deduction6.amount

            total_deduction = total_deduction_amount + total_other_deduction_amount + loan_amount + euro_adjustment_amount + unpaid_leave_deduction.amount

            month_net_salary = (payslip.contract_id.total_salary + total_earned) - total_deduction

            net_salary = payslip.line_ids.filtered(lambda r: r.code == 'NET')
            net_salary = net_salary.amount

            worksheet.write(row, 0, payslip.employee_id.oe_emp_sequence, text2)
            worksheet.write(row, 1, self.env.company.name, text2)
            worksheet.write(row, 2, payslip.employee_id.sponsor_id, text2)
            worksheet.write(row, 3, payslip.employee_id.name, text2)
            worksheet.write(row, 4, payslip.employee_id.department_id.name, text2)
            worksheet.write(row, 5, payslip.employee_id.job_title, text2)
            worksheet.write(row, 6, payslip.employee_id.joining_date, date_format)
            if work_days or payslip.worked_days:
                worksheet.write(row, 7,  work_days or payslip.worked_days, text1)
            else:
                worksheet.write(row, 7, 0, text1)
            if sick_leave or payslip.sick_days:
                worksheet.write(row, 8, sick_leave or payslip.sick_days, text1)
            else:
                worksheet.write(row, 8, 0, text1)
            if unpaid_leaves or payslip.unpaid_days:
                worksheet.write(row, 9, unpaid_leaves or payslip.unpaid_days, text1)
            else:
                worksheet.write(row, 9, 0, text1)
            worksheet.write(row, 10, annual_leave_days, text1)
            worksheet.write(row, 11, payslip.contract_id.basic, text2)
            worksheet.write(row, 12, living_allowance.amount, text2)
            worksheet.write(row, 13, other_allowance.amount, text2)
            worksheet.write(row, 14, payslip.contract_id.total_salary, text2)
            worksheet.write(row, 15, ticket_earned_amount, text2)
            worksheet.write(row, 16, bonus_amount, text2)
            worksheet.write(row, 17, tip_amount, text2)
            worksheet.write(row, 18, euro_adjustment_amount, text2)
            worksheet.write(row, 19, other_reimbursement_amount, text2)
            worksheet.write(row, 20, temporary_allowance_amount, text2)
            worksheet.write(row, 21, last_salary_arrears_amount, text2)
            worksheet.write(row, 22, part_time_pay, text2)
            worksheet.write(row, 23, al_salary, text2)
            worksheet.write(row, 24, yearly_bonus, text2)
            worksheet.write(row, 25, total_earned, text2)
            worksheet.write(row, 26, payslip.contract_id.total_salary, text2)
            worksheet.write(row, 27, unpaid_leave_deduction.amount, text2)
            worksheet.write(row, 28, loan_amount, text2)
            worksheet.write(row, 29, total_other_deduction_amount, text2)
            worksheet.write(row, 30, total_deduction, text2)
            worksheet.write(row, 31, round(month_net_salary), text2)
            row += 1
