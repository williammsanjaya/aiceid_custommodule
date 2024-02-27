# -*- coding: utf-8 -*-
# from odoo import http


# class AiceIdFreezer(http.Controller):
#     @http.route('/aice_id_freezer/aice_id_freezer/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/aice_id_freezer/aice_id_freezer/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('aice_id_freezer.listing', {
#             'root': '/aice_id_freezer/aice_id_freezer',
#             'objects': http.request.env['aice_id_freezer.aice_id_freezer'].search([]),
#         })

#     @http.route('/aice_id_freezer/aice_id_freezer/objects/<model("aice_id_freezer.aice_id_freezer"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('aice_id_freezer.object', {
#             'object': obj
#         })
