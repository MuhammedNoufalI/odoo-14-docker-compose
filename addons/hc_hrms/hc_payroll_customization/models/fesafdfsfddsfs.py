def _action_create_account_move(self):
    ctx = self._context.get('active_employee_ids')
    precision = self.env['decimal.precision'].precision_get('Payroll')

    # Add payslip without run
    payslips_to_post = self.filtered(lambda slip: not slip.payslip_run_id)

    # Adding pay slips from a batch and deleting pay slips with a batch that is not ready for validation.
    payslip_runs = (self - payslips_to_post).mapped('payslip_run_id')
    for run in payslip_runs:
        if run._are_payslips_ready():
            payslips_to_post |= run.slip_ids

    # A payslip need to have a done state and not an accounting move.
    payslips_to_post = payslips_to_post.filtered(lambda slip: slip.state == 'done' and not slip.move_id)

    # Check that a journal exists on all the structures
    if any(not payslip.struct_id for payslip in payslips_to_post):
        raise ValidationError(_('One of the contract for these payslips has no structure type.'))
    if any(not structure.journal_id for structure in payslips_to_post.mapped('struct_id')):
        raise ValidationError(_('One of the payroll structures has no account journal defined on it.'))

    # Map all payslips by structure journal and pay slips month.
    # {'journal_id': {'month': [slip_ids]}}
    slip_mapped_data = defaultdict(lambda: defaultdict(lambda: self.env['hr.payslip']))
    for slip in payslips_to_post:
        slip_mapped_data[slip.struct_id.journal_id.id][fields.Date().end_of(slip.date_to, 'month')] |= slip
    for journal_id in slip_mapped_data: # For each journal_id.
        for slip_date in slip_mapped_data[journal_id]: # For each month.
            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            date = slip_date
            move_dict = {
                'narration': '',
                'ref': date.strftime('%B %Y'),
                'journal_id': journal_id,
                'date': date,
            }

            for slip in slip_mapped_data[journal_id][slip_date]:
                company_id = slip.company_id or slip.struct_id.journal_id.company_id
                currency = company_id.currency_id
                payroll_currency = slip.contract_id.currency_id

                move_dict['narration'] += plaintext2html(slip.number or '' + ' - ' + slip.employee_id.name or '')
                move_dict['narration'] += Markup('<br/>')
                for line in slip.line_ids.filtered(lambda line: line.category_id):
                    amount = line.total
                    if line.code == 'NET': # Check if the line is the 'Net Salary'.
                        for tmp_line in slip.line_ids.filtered(lambda line: line.category_id):
                            if tmp_line.salary_rule_id.not_computed_in_net: # Check if the rule must be computed in the 'Net Salary' or not.
                                if amount > 0:
                                    amount -= abs(tmp_line.total)
                                elif amount < 0:
                                    amount += abs(tmp_line.total)
                    if float_is_zero(amount, precision_digits=precision):
                        continue
                    amount_currency = amount
                    amount = payroll_currency._convert(amount_currency, currency, company_id, slip.date_from or fields.Date.today())
                    debit_account_id = line.salary_rule_id.account_debit.id
                    credit_account_id = line.salary
