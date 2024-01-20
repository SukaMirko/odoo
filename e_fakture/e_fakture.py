# e_fakture.py
from odoo import models, fields, api, _
from odoo.tools import date_utils
import requests
from odoo.exceptions import UserError
import xmltodict
import json

class EFakture(models.Model):
    _name = 'e_fakture.e_fakture'
    _description = 'E Fakture'

    name = fields.Char(string='Name')
    date_from = fields.Date(string='From', default=date_utils.subtract(fields.Date.today(), days=1))
    date_to = fields.Date(string='To', default=fields.Date.today())
    vendor_bill_ids = fields.One2many('account.move', 'e_fakture_id', string='Vendor Bills')


    def import_vendor_bills(self):

        params = self.env['ir.config_parameter'].sudo()

        date_from = self.date_from
        date_to = self.date_to
        api_key = params.get_param('e_fakture.e_api_key')
        status = params.get_param('e_fakture.e_status')

        url = "https://efaktura.mfin.gov.rs/api/publicApi/purchase-invoice/ids"
        headers = {
            "accept": "application/json",
            "ApiKey": api_key,
        }
        params = {
            "status": status,
            "dateFrom": date_from,
            "dateTo": date_to,
        }


        response = requests.post(url, headers=headers, params=params)
        if response.status_code == 200:
            try:
                response_data = response.json()
                purchase_invoice_ids = response_data.get('PurchaseInvoiceIds', [])
            except ValueError as e:
                raise UserError(_("Error decoding JSON response: %s" % e))

                # Process the purchase invoice IDs
            for invoice_id in purchase_invoice_ids:
                invoice_details = self.fetch_invoice_details(invoice_id)
                try:
                    print(invoice_details)
                    partner_details = invoice_details.get('env:DocumentEnvelope').get('env:DocumentBody').get('CreditNote')
                    bill = invoice_details.get('env:DocumentEnvelope').get('env:DocumentBody').get('CreditNote')
                    lines = invoice_details.get('env:DocumentEnvelope').get('env:DocumentBody').get('CreditNote').get('cac:CreditNoteLine')
                except:
                    print(invoice_details)
                    partner_details = invoice_details.get('env:DocumentEnvelope').get('env:DocumentBody').get('Invoice')
                    bill = invoice_details.get('env:DocumentEnvelope').get('env:DocumentBody').get('Invoice')
                    lines = invoice_details.get('env:DocumentEnvelope').get('env:DocumentBody').get('Invoice').get('cac:InvoiceLine')

                if partner_details:
                    partner_details = partner_details.get('cac:AccountingSupplierParty').get('cac:Party')
                    party_name = partner_details.get('cac:PartyName').get('cbc:Name')
                    legal_name = partner_details.get('cac:PartyLegalEntity').get('cbc:RegistrationName')
                    adress = partner_details.get('cac:PostalAddress')
                    street_name = adress.get('cbc:StreetName')
                    city_name = adress.get('cbc:CityName')
                    postal_zone = adress.get('cbc:PostalZone')
                    country_subentity_code = adress.get('cbc:CountrySubentityCode')
                    country_code = adress.get('cac:Country').get('cbc:IdentificationCode')
                    company_id = partner_details.get('cac:PartyTaxScheme').get('cbc:CompanyID')
                    if partner_details.get('cac:Contact'):
                        electronic_mail = partner_details.get('cac:Contact').get('cbc:ElectronicMail')
                    else:
                        electronic_mail = None
                    country = self.env['res.country'].search([('code', '=', country_code)], limit=1)

                    partner_details = {
                        'name': party_name,
                        'company_type': 'company',
                        'company_name': legal_name,
                        'street': street_name,
                        'city': city_name,
                        'zip': postal_zone,
                        'country_id': country.id,
                        'vat': company_id,
                        'email': electronic_mail,}

                    partner = self.create_or_update_partner(partner_details)
                    print(invoice_details)

                    currency = self.env['res.currency'].search([('name', '=', bill.get('cbc:DocumentCurrencyCode'))], limit=1)
                    if not currency:
                        currency = 147

                    bill_details = {
                        'partner_id': partner,
                        'ref': bill.get('cbc:ID'),
                        'invoice_date': bill.get('cbc:IssueDate'),
                        'invoice_date_due': bill.get('cbc:DueDate'),
                        'currency_id': currency.id,
                        'e_fakture_purchase_id': invoice_id,
                        'move_type': 'in_invoice',
                    }
                    vendor_bill = self.create_or_update_vendor_bill(bill_details)
                    attachment = {
                        'type': 'binary',
                        'name': 'invoice_id',
                        'datas': invoice_details.get('env:DocumentEnvelope').get('env:DocumentHeader').get('env:DocumentPdf').get('#text'),
                        'mimetype': invoice_details.get('env:DocumentEnvelope').get('env:DocumentHeader').get('env:DocumentPdf').get('@mimeCode'),
                        'res_model': 'account.move',
                        'res_id': vendor_bill,

                    }
                    self.env['ir.attachment'].create(attachment)
                    if type(lines) is list:
                        continue
                    else:
                        lines = [lines]
                    for line in lines:
                        print(line)
                        percent = line.get('cac:Item').get('cac:ClassifiedTaxCategory').get('cbc:Percent')

                        vat = self.env['account.tax'].search([('amount', '=', percent)], limit=1)
                        print(vat)
                        account_lines = {
                            'name': line.get('cac:Item').get('cbc:Name'),
                            'quantity': line.get('cbc:InvoicedQuantity').get('#text'),
                            'price_unit': line.get('cbc:LineExtensionAmount').get('#text'),
                            'tax_ids': vat,
                            'account_id': vendor_bill,
                            'move_id':vendor_bill,
                        }
                        self.env['account.move.line'].create(account_lines)

    def fetch_invoice_details(self, invoice_id):
        # Make a request to another API endpoint to get details based on the invoice ID
        # Modify this function based on the actual API and response structure
        # Example: https://efaktura.mfin.gov.rs/api/publicApi/purchase-invoice/details/{invoice_id}
        params = self.env['ir.config_parameter'].sudo()

        api_key = params.get_param('e_fakture.e_api_key')

        xml_url = f"https://efaktura.mfin.gov.rs/api/publicApi/purchase-invoice/xml"
        headers = {
            "accept": "application/json",
            "ApiKey": api_key,
        }
        params = {
            "invoiceId": invoice_id,
        }
        details_response = requests.get(xml_url, headers=headers,params=params)
        if details_response.status_code == 200:
            # Parse XML response
            try:
                xml_data = xmltodict.parse(details_response.content)
                # Process xml_data as needed
                return xml_data
            except:
                raise UserError(_("Error parsing XML response: %s"))
        else:
            raise UserError(_("Error fetching invoice details: %s" % details_response.text))

    def create_or_update_vendor_bill(self, bill_details):
        existing_bill = self.env['account.move'].search([('e_fakture_purchase_id', '=', bill_details.get('e_fakture_purchase_id')),], limit=1)
        if existing_bill:
            print('356565656565656565656565656565656565656565656565656')
            print(existing_bill.name)
            return existing_bill.id
        else:
            print('sddddddddddddddddddddddddddddddddd')
            new_bill = self.env['account.move'].create(bill_details)
            self.vendor_bill_ids = new_bill
            print(new_bill.name)
            return new_bill.id

    def create_or_update_partner(self, partner_details):
        existing_partner = self.env['res.partner'].search([('vat', '=', partner_details.get('vat')),], limit=1)
        if existing_partner:
            # Partner already exists, return the existing partner's ID
            return existing_partner.id
        else:
            # Partner does not exist, create a new partner
            new_partner = self.env['res.partner'].create(partner_details)
            return new_partner.id
