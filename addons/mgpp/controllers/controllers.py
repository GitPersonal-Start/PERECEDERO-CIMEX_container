# -*- coding: utf-8 -*-
# from odoo import http


# class Mgpp(http.Controller):
#     @http.route('/mgpp/mgpp', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mgpp/mgpp/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('mgpp.listing', {
#             'root': '/mgpp/mgpp',
#             'objects': http.request.env['mgpp.mgpp'].search([]),
#         })

#     @http.route('/mgpp/mgpp/objects/<model("mgpp.mgpp"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mgpp.object', {
#             'object': obj
#         })
