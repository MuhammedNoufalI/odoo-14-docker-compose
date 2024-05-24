# -*- coding: utf-8 -*-
from odoo import models
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime, timedelta

LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


def excel_style(row, col):
    """ Convert given row and column number to an Excel-style cell name. """
    result = []
    while col:
        col, rem = divmod(col - 1, 26)
        result[:0] = LETTERS[rem]
    return ''.join(result) + str(row)


class GeneralLedgerReport(models.AbstractModel):
    _name = "report.hc_balance_leave_report.general_ledger_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "Leave Balance XLSX Report"

    def generate_xlsx_report(self, workbook, data, wizard):
        ##FORMATS##
        heading1_format = workbook.add_format({'align': 'center', 'size': 15, 'bold': True, 'bg_color': '#89CFF0'})
        heading_format = workbook.add_format(
            {'align': 'center', 'size': 10, 'bold': True, 'bg_color': '#89CFF0'})
        heading_format.set_align('center')
        heading_format.set_align('top')
        heading_format.set_top()
        heading_format.set_bottom()
        heading_format.set_left()
        heading_format.set_right()
        sub_heading_format = workbook.add_format({'size': 10})
        text = workbook.add_format({'align': 'center', 'size': 10})
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy', 'size': 10, 'align': 'center'})
        no_format = workbook.add_format({'num_format': '#,##0.0', 'size': 10, 'align': 'center'})
        normal_num_bold = workbook.add_format({'bold': True, 'num_format': '#,##0.00'})
        ##FORMATS END##
        worksheet = workbook.add_worksheet("Balance Leave Report")
        worksheet.set_column('A:A', 14)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('C:C', 25)
        worksheet.set_column('D:D', 17)
        worksheet.set_column('E:E', 17)
        worksheet.set_column('F:F', 11)
        worksheet.set_column('G:G', 18)
        worksheet.set_column('H:H', 20)
        worksheet.set_column('I:I', 20)
        worksheet.set_column('J:J', 20)
        worksheet.set_column('K:K', 20)
        worksheet.set_column('L:L', 20)
        worksheet.set_column('M:M', 15)
        worksheet.set_column('N:N', 15)
        worksheet.set_column('O:O', 15)
        worksheet.set_column('P:P', 15)
        worksheet.set_column('Q:Q', 15)
        ending_col = excel_style(1, 9)
        worksheet.merge_range('A2:%s' % (ending_col), "Leave Balance Report", heading1_format)
        date = wizard.date
        worksheet.write(3, 1, str(date), heading_format)
        worksheet.write(3, 0, "Date", heading_format)

        row = 5
        worksheet.set_row(row, 25)

        heading_list = ['Employee code', 'Name', 'Global joining\n Date For Leave', 'Ticket Benefit Date',
                        'Probation\n End Date ', 'Service Days', 'Total Service \nYears',
                        'Entitled as\n of Date Entered\n (Accrued)', 'Annual Leave\n Taken as Date \nEntered',
                        'Unpaid & Absent Days\n as of Date', 'Total Number \nof Sick Leave',
                        'loss of AL\n accrual Days \ndue to Unpaid \nor Absent days', 'leave Balance',
                        'Ticket Entitlement',
                        'Ticket Availed', 'Ticket Accrued', 'Ticket Balance']
        col = 0
        for heading in heading_list:
            worksheet.write(row, col, heading, heading_format)
            col += 1
        row += 1
        employee_ids = wizard.employee_ids
        if employee_ids:
            employee_list = employee_ids
        else:
            employee_list = self.env['hr.employee'].search([])
        for record in employee_list:
            contract_ids = record.sudo().contract_ids.filtered(lambda c: c.state != 'cancel')
            if contract_ids:
                unpaid_leave = 0
                joining_date = record.joining_date
                unpaid_leave_days = self.env['hr.leave'].search(
                    [('create_date', '<=', date), ('create_date', '>=', joining_date),
                     ('employee_id', '=', record.id),
                     ('holiday_status_id.is_unpaid_leave', '=', True), ('state', '=', 'validate')])
                if unpaid_leave_days:
                    for days in unpaid_leave_days:
                        unpaid_leave += days.number_of_days
                total_service_period = 0
                if joining_date:
                    total_service_period = ((date - joining_date) + timedelta(days=1)).days
                service_days = int(total_service_period) - unpaid_leave
                total_service_year = service_days / 365
                total_service_year = round(total_service_year, 2)
                entitled_date_entered = total_service_year * 30
                unpaid_networking = 0
                unpaid_leave_networking_days = self.env['hr.leave'].search(
                    [('create_date', '<=', date), ('create_date', '>=', joining_date),
                     ('employee_id', '=', record.id),
                     ('holiday_status_id.is_unpaid_leave', '=', True),
                     ('holiday_status_id.include_to_net_working', '=', False), ('state', '=', 'validate')])
                for rec in unpaid_leave_networking_days:
                    unpaid_networking += rec.number_of_days
                loss_of_accrual_days = unpaid_leave - unpaid_networking
                annual_leaves = self.env['hr.leave'].search(
                    [('create_date', '<=', date), ('create_date', '>=', joining_date),
                     ('employee_id', '=', record.id),
                     ('holiday_status_id.is_annual_leave', '=', True), ('state', '=', 'validate')])
                annual_leave = 0
                if annual_leaves:
                    for leave in annual_leaves:
                        annual_leave += leave.number_of_days

                sick_leave_days = 0
                sick_leaves = self.env['hr.leave'].search(
                    [('create_date', '<=', date), ('create_date', '>=', joining_date),
                     ('employee_id', '=', record.id),
                     ('holiday_status_id.is_sick_leave', '=', True), ('state', '=', 'validate')])

                if sick_leaves:
                    for sick_leave in sick_leaves:
                        sick_leave_days += sick_leave.number_of_days

                ticket_entitlement = record.contract_id.ticket_entitlement
                ticket_accrued = 0
                if ticket_entitlement:
                    ticket_accrued = float(service_days) / int(ticket_entitlement)
                ticket_accrued = round(ticket_accrued, 1)
                # ticket_request = self.env['ticket.request'].search(
                #     [('employee_id', '=', record.id), ('state', '=', 'hr_approval'),
                #      ('create_date', '<=', date),
                #      ('create_date', '>=', joining_date)])
                ticket_availed = record.ticket_availed
                ticket_balance = ticket_accrued - ticket_availed
                leave_balance = round(entitled_date_entered) - annual_leave

                worksheet.write(row, 0, record.oe_emp_sequence, sub_heading_format)
                worksheet.write(row, 1, record.name, sub_heading_format)
                worksheet.write(row, 2, record.joining_date, date_format)
                worksheet.write(row, 3, record.joining_date or "", date_format)
                worksheet.write(row, 4, record.contract_id.trial_date_end or "", date_format)
                worksheet.write(row, 5, service_days, text)
                worksheet.write(row, 6, total_service_year, text)
                worksheet.write(row, 7, entitled_date_entered, text)
                worksheet.write(row, 8, annual_leave, text)
                worksheet.write(row, 9, unpaid_leave, text)
                worksheet.write(row, 10, sick_leave_days, text)
                worksheet.write(row, 11, loss_of_accrual_days, text)
                worksheet.write(row, 12, leave_balance, text)
                worksheet.write(row, 13, ticket_entitlement, text)
                worksheet.write(row, 14, ticket_availed or 0, text)
                worksheet.write(row, 15, ticket_accrued or 0, text)
                worksheet.write(row, 16, ticket_balance or 0, text)
                row += 1
