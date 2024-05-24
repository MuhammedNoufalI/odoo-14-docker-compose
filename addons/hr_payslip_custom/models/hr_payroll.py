# -*- coding: utf-8 -*-

from __future__ import division

from odoo import api, fields, models,_

class PS(models.Model):
    _name = "hr.payslip"
    _inherit = ['hr.payslip',  'portal.mixin']

class hr_payroll(models.Model):
    _inherit = 'hr.payslip'
    user_id = fields.Many2one('res.users', string='Responsible', required=False, default=lambda self: self.env.user)
    hold = fields.Boolean(compute='compute_hold')
    @api.depends('attend_date_from','attend_date_to')
    def compute_hold(self):
        for rec in self:
            rec.hold = False
            if rec.employee_id:
                rec.hold = True if len(self.env['hr.resignation'].search([('state','!=','cancel'),('employee_id','=',rec.employee_id.id),('expected_revealing_date','>=',rec.attend_date_from),('expected_revealing_date','<=',rec.attend_date_to)])) >=1 else False

    def action_payslip_send(self):
        '''
        This function opens a window to compose an email, with the edi Payslip template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('hr_payslip_custom', 'email_template_edi_payslip')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'hr.payslip',
            'active_model': 'hr.payslip',
            'active_id': self.ids[0],
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'custom_layout': "mail.mail_notification_paynow",
            'force_email': True,
            'mark_ps_as_sent': True,

        })

        lang = self.env.context.get('lang')
        if {'default_template_id', 'default_model', 'default_res_id'} <= ctx.keys():
            template = self.env['mail.template'].browse(ctx['default_template_id'])
            if template and template.lang:
                lang = template._render_lang([ctx['default_res_id']])[ctx['default_res_id']]

        self = self.with_context(lang=lang)
        ctx['model_description'] = _('Payslip')

        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
