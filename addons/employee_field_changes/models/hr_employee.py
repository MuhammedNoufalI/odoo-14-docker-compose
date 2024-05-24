from odoo import api, fields, models, _
from odoo.tools.float_utils import float_round


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    payment_mode = fields.Selection([('bank', 'Bank'), ('cash', 'Cash'),
                                     ('int_trf', 'Intl. Transfer'),
                                     ('rank_c3', 'EDENRED - RAK - C3')], string="Payment Mode")
    bank_routing_code = fields.Char(string="Bank Routing Code")
    uae_payment_type = fields.Selection([('WPS', 'WPS'), ('NON_WPS', 'NON WPS')], string="UAE Payment Type")
    personal_contact_no = fields.Char(string="Personal Contact No")
    personal_email = fields.Char(string="Personal Email Address")
    contract_type = fields.Selection([('unlimited', 'Unlimited'), ('limited', 'Limited'), ('freelance', 'Freelance')],
                                     string="Contract Type")
    mol_id = fields.Char(string="MOL ID")
    mol_expiry_date = fields.Date(string="MOL ID Expiry Date")
    mol_issue_date = fields.Date(string="MOL ID Issue Date")
    emirate_id_expiry_date = fields.Date(string="Emirate ID Expiry Date")
    ohc_id = fields.Char(string="OHC No.")
    ohc_expiry_date = fields.Date(string="OHC Expiry Date")
    sponsor_id = fields.Char(string="Sponsor ID")
    hr_employee_type_id = fields.Many2one('hr.employee.type', string="Employee Type")
    bank_account_id = fields.Many2one(string='IBAN')
    marital = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married')

    ], string='Marital Status', groups="hr.group_hr_user", default='single', tracking=True)
    business_unit = fields.Char(string="Business Unit")
    registration_number = fields.Char('Employee ID Number', groups="hr.group_hr_user", copy=False)

    @api.model
    def default_get(self, fields):
        res = super(HrEmployee, self).default_get(fields)
        company_id = self.env.company.id
        branch = self.env["hc.branch"].search([('company_id', '=', company_id)])
        res.update({'branch_id': branch.id})
        return res

    @api.model
    def create(self, vals):
        res = super(HrEmployee, self).create(vals)
        emp_sequence = res['oe_emp_sequence']
        if not emp_sequence == 'New':
            if emp_sequence:
                sequence = emp_sequence.split('/')
                if len(sequence) >= 2:
                    res['registration_number'] = int(sequence[1])
                else:
                    res['registration_number'] = int(sequence[0])
        if res['registration_number']:
            number = res['registration_number']
            res['oe_emp_sequence'] = number
        return res


    @api.onchange('agent_id')
    def _onchange_agent_id(self):
        if self.agent_id:
            self.bank_routing_code = self.agent_id.routing_code

    @api.onchange('department_id')
    def _onchange_department_id(self):
        if self.department_id:
            if self.department_id.parent_id:
                self.business_unit = self.department_id.parent_id.name

    def _compute_allocation_count(self):
        data = self.env['hr.leave.allocation'].read_group([
            ('employee_id', 'in', self.ids),
            ('holiday_status_id.active', '=', True), ('holiday_status_id.is_annual_leave', '=', True),
            ('state', '=', 'validate'),
        ], ['number_of_days:sum', 'employee_id'], ['employee_id'])
        rg_results = dict((d['employee_id'][0], d['number_of_days']) for d in data)
        for employee in self:
            employee.allocation_count = float_round(rg_results.get(employee.id, 0.0), precision_digits=2)
            employee.allocation_display = "%g" % employee.allocation_count


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    @api.model
    def create(self, vals):
        if vals.get('hr_employee_type_id'):
            employee_type = self.env['hr.employee.type'].browse(int(vals.get('hr_employee_type_id')))
            if vals['registration_number']:
                vals['oe_emp_sequence'] = vals['registration_number']
            else:

                # if employee_type.sequence_code == 'rm':
                #     vals['oe_emp_sequence'] = self.env['ir.sequence'].next_by_code('regular.employee.seq') or _(
                #         'New')
                #
                # elif employee_type.sequence_code == 'fl':
                #     vals['oe_emp_sequence'] = self.env['ir.sequence'].next_by_code('free.lancer.seq') or _('New')
                # else:
                vals['oe_emp_sequence'] = self.env['ir.sequence'].next_by_code('remote.employee.seq') or _(
                    'New')
        return super(HrEmployeeBase, self).create(vals)


class HrEmployeeType(models.Model):
    _name = 'hr.employee.type'

    name = fields.Char("Name")
    sequence_code = fields.Selection(
        selection=[
            ('rm', 'RM'), ('emp', 'EMP'),
            ('fl', 'FL'),
        ], string="Sequence Code", default="emp"
    )
