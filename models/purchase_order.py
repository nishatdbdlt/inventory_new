from odoo import models, fields, api
from odoo.exceptions import ValidationError


class InventoryPurchaseOrder(models.Model):
    _name = 'inventory.purchase.order'
    _description = 'Inventory Purchase Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_order desc'

    name = fields.Char(string='Purchase Reference', readonly=True, copy=False, default='New')
    supplier_name = fields.Char(string='Supplier Name', required=True, tracking=True)
    supplier_contact = fields.Char(string='Supplier Contact')
    date_order = fields.Datetime(string='Order Date', default=fields.Datetime.now, required=True, tracking=True)
    expected_date = fields.Date(string='Expected Delivery Date')

    # Order Lines
    order_line_ids = fields.One2many('inventory.purchase.order.line', 'order_id', string='Order Lines')

    # Amounts
    subtotal = fields.Float(string='Subtotal', compute='_compute_amounts', store=True)
    tax_amount = fields.Float(string='Tax Amount', compute='_compute_amounts', store=True)
    total_amount = fields.Float(string='Total Amount', compute='_compute_amounts', store=True)

    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    notes = fields.Text(string='Notes')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('inventory.purchase.order') or 'PO000'
        return super(InventoryPurchaseOrder, self).create(vals)

    @api.depends('order_line_ids.subtotal')
    def _compute_amounts(self):
        for record in self:
            record.subtotal = sum(record.order_line_ids.mapped('subtotal'))
            record.tax_amount = record.subtotal * 0.15  # 15% tax
            record.total_amount = record.subtotal + record.tax_amount

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_receive(self):
        for record in self:
            # Add inventory
            for line in record.order_line_ids:
                line.product_id.quantity_on_hand += line.quantity

            record.state = 'received'
            record.message_post(body=f'Purchase order received. Stock updated.')

    def action_cancel(self):
        self.write({'state': 'cancelled'})


class InventoryPurchaseOrderLine(models.Model):
    _name = 'inventory.purchase.order.line'
    _description = 'Purchase Order Line'

    order_id = fields.Many2one('inventory.purchase.order', string='Order', required=True, ondelete='cascade')
    product_id = fields.Many2one('inventory.product', string='Product', required=True)
    description = fields.Text(string='Description')
    quantity = fields.Float(string='Quantity', required=True, default=1.0)
    unit_price = fields.Float(string='Unit Price', required=True)
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.unit_price = self.product_id.cost_price
            self.description = self.product_id.description

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for record in self:
            record.subtotal = record.quantity * record.unit_price

    @api.constrains('quantity')
    def _check_quantity(self):
        for record in self:
            if record.quantity <= 0:
                raise ValidationError('Quantity must be greater than zero!')