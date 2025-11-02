# -*- coding: utf-8 -*-
# from odoo import http


# class ProductManagment(http.Controller):
#     @http.route('/product_managment/product_managment', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/product_managment/product_managment/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('product_managment.listing', {
#             'root': '/product_managment/product_managment',
#             'objects': http.request.env['product_managment.product_managment'].search([]),
#         })

#     @http.route('/product_managment/product_managment/objects/<model("product_managment.product_managment"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('product_managment.object', {
#             'object': obj
#         })

