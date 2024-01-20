# -*- coding: utf-8 -*-
# from odoo import http


# class EFakture(http.Controller):
#     @http.route('/e_fakture/e_fakture', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/e_fakture/e_fakture/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('e_fakture.listing', {
#             'root': '/e_fakture/e_fakture',
#             'objects': http.request.env['e_fakture.e_fakture'].search([]),
#         })

#     @http.route('/e_fakture/e_fakture/objects/<model("e_fakture.e_fakture"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('e_fakture.object', {
#             'object': obj
#         })
