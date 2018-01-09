# -*- coding: utf-8 -*-
from odoo import http

# class Cursos(http.Controller):
#     @http.route('/cursos/cursos/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/cursos/cursos/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('cursos.listing', {
#             'root': '/cursos/cursos',
#             'objects': http.request.env['cursos.cursos'].search([]),
#         })

#     @http.route('/cursos/cursos/objects/<model("cursos.cursos"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('cursos.object', {
#             'object': obj
#         })