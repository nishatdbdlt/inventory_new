from odoo import models, fields, api
from odoo.exceptions import ValidationError


class InventoryProduct(models.Model):
    _name = 'inventory.product'
    _description = 'Inventory Product'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Product Name', required=True, tracking=True)
    code = fields.Char(string='Product Code', required=True, tracking=True)
    description = fields.Text(string='Description')
    category = fields.Selection([
        ('electronics', 'Electronics'),
        ('clothing', 'Clothing'),
        ('food', 'Food & Beverages'),
        ('furniture', 'Furniture'),
        ('other', 'Other')
    ], string='Category', default='other', tracking=True)

    # Pricing
    cost_price = fields.Float(string='Cost Price', required=True, tracking=True)
    selling_price = fields.Float(string='Selling Price', required=True, tracking=True)
    profit_margin = fields.Float(string='Profit Margin (%)', compute='_compute_profit_margin', store=True)

    # Inventory
    quantity_on_hand = fields.Float(string='Quantity On Hand', default=0.0, tracking=True)
    minimum_quantity = fields.Float(string='Minimum Quantity', default=10.0)
    maximum_quantity = fields.Float(string='Maximum Quantity', default=1000.0)

    # Status
    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection([
        ('available', 'Available'),
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock')
    ], string='Stock Status', compute='_compute_stock_status', store=True)

    # Relations
    # sale_order_line_ids = fields.One2many('inventory.sale.order.line', 'product_id', string='Sale Order Lines')
    # purchase_order_line_ids = fields.One2many('inventory.purchase.order.line', 'product_id',
    #                                           string='Purchase Order Lines')

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Product code must be unique!'),
    ]

    @api.depends('cost_price', 'selling_price')
    def _compute_profit_margin(self):
        for record in self:
            if record.cost_price > 0:
                record.profit_margin = ((record.selling_price - record.cost_price) / record.cost_price) * 100
            else:
                record.profit_margin = 0.0

    @api.depends('quantity_on_hand', 'minimum_quantity')
    def _compute_stock_status(self):
        for record in self:
            if record.quantity_on_hand <= 0:
                record.state = 'out_of_stock'
            elif record.quantity_on_hand <= record.minimum_quantity:
                record.state = 'low_stock'
            else:
                record.state = 'available'

    @api.constrains('selling_price', 'cost_price')
    def _check_prices(self):
        for record in self:
            if record.selling_price < 0 or record.cost_price < 0:
                raise ValidationError('Prices cannot be negative!')

    def action_adjust_stock(self):
        return {
            'name': 'Adjust Stock',
            'type': 'ir.actions.act_window',
            'res_model': 'inventory.stock.adjustment',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_product_id': self.id}
        }