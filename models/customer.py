from odoo import models, fields, api


class InventoryCustomer(models.Model):
    _name = 'inventory.customer'
    _description = 'Inventory Customer'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Customer Name', required=True, tracking=True)
    code = fields.Char(string='Customer Code', readonly=True, copy=False)
    email = fields.Char(string='Email', tracking=True)
    phone = fields.Char(string='Phone', required=True, tracking=True)
    mobile = fields.Char(string='Mobile')

    # Address
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street 2')
    city = fields.Char(string='City')
    state = fields.Char(string='State')
    zip_code = fields.Char(string='ZIP Code')
    country = fields.Char(string='Country')

    # Customer Type
    customer_type = fields.Selection([
        ('individual', 'Individual'),
        ('company', 'Company')
    ], string='Customer Type', default='individual', tracking=True)

    company_name = fields.Char(string='Company Name')
    tax_id = fields.Char(string='Tax ID/VAT')

    # Financial
    credit_limit = fields.Float(string='Credit Limit', default=0.0)
    total_purchases = fields.Float(string='Total Purchases', compute='_compute_total_purchases', store=True)
    outstanding_balance = fields.Float(string='Outstanding Balance', compute='_compute_outstanding_balance', store=True)

    # Status
    active = fields.Boolean(string='Active', default=True)
    notes = fields.Text(string='Notes')

    # Relations
    # sale_order_ids = fields.One2many('inventory.sale.order', 'customer_id', string='Sale Orders')
    # invoice_ids = fields.One2many('inventory.invoice', 'customer_id', string='Invoices')

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Customer code must be unique!'),
    ]

    @api.model
    def create(self, vals):
        if not vals.get('code'):
            vals['code'] = self.env['ir.sequence'].next_by_code('inventory.customer') or 'CUST000'
        return super(InventoryCustomer, self).create(vals)

    # @api.depends('sale_order_ids.total_amount')
    # def _compute_total_purchases(self):
    #     for record in self:
    #         record.total_purchases = sum(
    #             record.sale_order_ids.filtered(lambda x: x.state == 'confirmed').mapped('total_amount'))

    # @api.depends('invoice_ids.balance_due')
    # def _compute_outstanding_balance(self):
    #     for record in self:
    #         record.outstanding_balance = sum(
    #             record.invoice_ids.filtered(lambda x: x.state != 'paid').mapped('balance_due'))