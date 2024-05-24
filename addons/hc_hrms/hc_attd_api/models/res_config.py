from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    api_url = fields.Char('API URL')
    api_key = fields.Char('API KEY')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ir_config = self.env['ir.config_parameter'].sudo()
        api_url = ir_config.get_param('hc_attd_api.api_url')
        api_key = ir_config.get_param('hc_attd_api.api_key')

        res.update(
            api_url=api_url,
            api_key=api_key,
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ir_config = self.env['ir.config_parameter'].sudo()
        ir_config.set_param("hc_attd_api.api_url", self.api_url or "")
        ir_config.set_param("hc_attd_api.api_key", self.api_key or "")

