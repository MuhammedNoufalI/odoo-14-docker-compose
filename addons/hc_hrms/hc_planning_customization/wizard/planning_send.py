# -*- coding:utf-8 -*-

from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.osv import expression


class PlanningSend(models.TransientModel):
    _inherit = 'planning.send'

    def action_publish(self):
        domain = [('employee_id', 'in', self.employee_ids.ids)]
        if self.include_unassigned:
            domain = expression.OR([[('resource_id', '=', False)], domain])
        slot_to_publish = self.slot_ids.filtered_domain(domain)
        slot_to_publish.write({
            'state': 'published',
            'publication_warning': False
        })
        if slot_to_publish:
            solt_list_to_publish = []
            for rec in slot_to_publish:
                solt_list_to_publish.append(rec)
            solt_list_to_publish = list(reversed(solt_list_to_publish))
            for slot in solt_list_to_publish:
                slot.action_update_contract()
        return True

