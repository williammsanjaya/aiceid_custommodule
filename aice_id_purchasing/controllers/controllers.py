# -*- coding: utf-8 -*-
# from odoo import http


# class AiceIdPurchasing(http.Controller):
#     @http.route('/aice_id_purchasing/aice_id_purchasing/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/aice_id_purchasing/aice_id_purchasing/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('aice_id_purchasing.listing', {
#             'root': '/aice_id_purchasing/aice_id_purchasing',
#             'objects': http.request.env['aice_id_purchasing.aice_id_purchasing'].search([]),
#         })

#     @http.route('/aice_id_purchasing/aice_id_purchasing/objects/<model("aice_id_purchasing.aice_id_purchasing"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('aice_id_purchasing.object', {
#             'object': obj
#         })
