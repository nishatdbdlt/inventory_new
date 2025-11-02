from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime


class InventorySaleOrder(models.Model):
    _name = 'inventory.sale.order'
    _description = 'Inventory Sale Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_order desc'

    name = fields.Char(string='Order Reference', readonly=True, copy=False, default='New')
    customer_id = fields.Many2one('inventory.customer', string='Customer', required=True, tracking=True)
    date_order = fields.Datetime(string='Order Date', default=fields.Datetime.now, required=True, tracking=True)

    # Order Lines
    order_line_ids = fields.One2many('inventory.sale.order.line', 'order_id', string='Order Lines')

    # Amounts
    subtotal = fields.Float(string='Subtotal', compute='_compute_amounts', store=True)
    tax_amount = fields.Float(string='Tax Amount', compute='_compute_amounts', store=True)
    discount_amount = fields.Float(string='Discount', default=0.0)
    total_amount = fields.Float(string='Total Amount', compute='_compute_amounts', store=True)

    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    # Invoice
    # invoice_id = fields.Many2one('inventory.invoice', string='Invoice', readonly=True)
    # invoice_state = fields.Selection(related='invoice_id.state', string='Invoice Status')

    notes = fields.Text(string='Notes')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('inventory.sale.order') or 'SO000'
        return super(InventorySaleOrder, self).create(vals)

    @api.depends('order_line_ids.subtotal', 'discount_amount')
    def _compute_amounts(self):
        for record in self:
            record.subtotal = sum(record.order_line_ids.mapped('subtotal'))
            record.tax_amount = record.subtotal * 0.15  # 15% tax
            record.total_amount = record.subtotal + record.tax_amount - record.discount_amount

    def action_confirm(self):
        for record in self:
            # Check stock availability
            for line in record.order_line_ids:
                if line.product_id.quantity_on_hand < line.quantity:
                    raise ValidationError(
                        f'Insufficient stock for {line.product_id.name}. Available: {line.product_id.quantity_on_hand}')

            # Deduct inventory
            for line in record.order_line_ids:
                line.product_id.quantity_on_hand -= line.quantity

            record.state = 'confirmed'

            # Auto-generate invoice
            record._generate_invoice()

    def _generate_invoice(self):
        for record in self:
            if not record.invoice_id:
                invoice_vals = {
                    'customer_id': record.customer_id.id,
                    'sale_order_id': record.id,
                    'date_invoice': fields.Date.today(),
                    'due_date': fields.Date.today(),
                    'subtotal': record.subtotal,
                    'tax_amount': record.tax_amount,
                    'total_amount': record.total_amount,
                    'balance_due': record.total_amount,
                }
                invoice = self.env['inventory.invoice'].create(invoice_vals)
                record.invoice_id = invoice.id

    def action_deliver(self):
        self.write({'state': 'delivered'})

    def action_cancel(self):
        for record in self:
            # Return inventory if order was confirmed
            if record.state == 'confirmed':
                for line in record.order_line_ids:
                    line.product_id.quantity_on_hand += line.quantity
            record.state = 'cancelled'

    def action_view_invoice(self):
        return {
            'name': 'Invoice',
            'type': 'ir.actions.act_window',
            'res_model': 'inventory.invoice',
            'view_mode': 'form',
            'res_id': self.invoice_id.id,
            'target': 'current',
        }


class InventorySaleOrderLine(models.Model):
    _name = 'inventory.sale.order.line'
    _description = 'Sale Order Line'

    order_id = fields.Many2one('inventory.sale.order', string='Order', required=True, ondelete='cascade')
    product_id = fields.Many2one('inventory.product', string='Product', required=True)
    description = fields.Text(string='Description')
    quantity = fields.Float(string='Quantity', required=True, default=1.0)
    unit_price = fields.Float(string='Unit Price', required=True)
    discount = fields.Float(string='Discount (%)', default=0.0)
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.unit_price = self.product_id.selling_price
            self.description = self.product_id.description

    @api.depends('quantity', 'unit_price', 'discount')
    def _compute_subtotal(self):
        for record in self:
            price = record.unit_price * record.quantity
            discount_amount = price * (record.discount / 100)
            record.subtotal = price - discount_amount

    @api.constrains('quantity')
    def _check_quantity(self):
        for record in self:
            if record.quantity <= 0:
                raise ValidationError('Quantity must be greater than zero!')