from odoo import models, fields, api

class EFaktureSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    e_api_key = fields.Char(string='E Fakture API Key')
    e_status = fields.Selection([
        ('New', 'New'),
        ('Seen', 'Seen'),
        ('Reminded', 'Reminded'),
        ('ReNotified', 'ReNotified'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Storno', 'Storno'),],
        string='Status', default='New', help='Select the default status'
    )
    e_account_id = fields.Many2one('account.account', string='Default Account ID', store=True, required=True)

    @api.model
    def get_values(self):
        res = super(EFaktureSettings, self).get_values()
        res['e_api_key'] = self.env['ir.config_parameter'].sudo().get_param("e_fakture.e_api_key", default="")
        res['e_status'] = self.env['ir.config_parameter'].sudo().get_param("e_fakture.e_status", default="")
        id = self.env['ir.config_parameter'].sudo().get_param("e_fakture.e_account_id", default="")
        res['e_account_id'] = self.env['account.account'].search([('id', '=', id)], limit=1)
        return res

    @api.model
    def set_values(self):
       print(self.e_account_id.id)
       self.env['ir.config_parameter'].sudo().set_param('e_fakture.e_api_key', self.e_api_key or '')
       self.env['ir.config_parameter'].sudo().set_param('e_fakture.e_status', self.e_status or '')
       self.env['ir.config_parameter'].sudo().set_param('e_fakture.e_account_id', self.e_account_id.id or '')
       super(EFaktureSettings, self).set_values()