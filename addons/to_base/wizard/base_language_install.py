from odoo import models


class BaseLanguageInstall(models.TransientModel):
    _inherit = 'base.language.install'

    def lang_install(self):
        self.ensure_one()
        modules = self.env['ir.module.module'].search([])
        modules._update_module_infos_translation(self.lang, self._cr, overwrite=self.overwrite)
        return super(BaseLanguageInstall, self).lang_install()
