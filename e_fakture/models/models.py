# -*- coding: utf-8 -*-

from odoo import models, fields, api
import requests

class AccountMove(models.Model):
    _inherit = 'account.move'

    e_fakture_id = fields.Many2one('e_fakture.e_fakture', string='E Fakture')
    e_fakture_purchase_id = fields.Char(string='E fakture ID')


    def action_post(self):
        res = super(AccountMove, self).action_post()
        params = self.env['ir.config_parameter'].sudo()
        api_key = params.get_param('e_fakture.e_api_key')
        xml_url = f"https://efaktura.mfin.gov.rs/api/publicApi/purchase-invoice/acceptRejectPurchaseInvoice"
        headers = {
            "accept": "application/json",
            "ApiKey": api_key,
        }
        params = {
            "invoiceId": self.e_fakture_purchase_id,
            "accepted": True,
        }
        post = requests.post(xml_url, headers=headers, json=params)
        print(post.text)

        return res


class ResPartner(models.Model):
    _inherit = 'res.partner'

    account_id_e = fields.Many2one('account.account', string='Account ID for Default Product E fakture')








