from odoo import models, fields, api, exceptions
from odoo import tools, _


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    condition_select = fields.Selection(selection_add=[('date_based', 'Date Based')],ondelete={'date_based': 'set default'})

    def _satisfy_condition(self, localdict):
        res = super()._satisfy_condition(localdict)
        if self.condition_select == 'date_based':
            if self.start_date and self.end_date:
                print('self.start_date=',self.start_date,'fields.Date.today()=',fields.Date.today(),'self.end_date=',self.end_date)
                if self.start_date < fields.Date.today() < self.end_date:
                    return True
                else:
                    return False
            else:
                return False


        return res
