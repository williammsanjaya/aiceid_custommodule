# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


# Adding the custom filter for the stock
class StockQuant(models.Model):
    _inherit = 'stock.quant'

    prod_type = fields.Selection(
        related='product_id.product_tmpl_id.type',
        string='Product Type',
        readonly=True
    )

# Class for the actual component
class FomOrder(models.Model):
    _name = "fom.order"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Freezer Order Head"

    #defining a sequence number for the name.
    @api.model
    def create(self, vals):
        if not vals.get('note'):
            vals['note'] = 'New Order Created'
        if vals.get('name', _('New Order')) == _('New Order'):
            vals['name'] = self.env['ir.sequence'].next_by_code('fom.order') or _('New Order')
        res = super(FomOrder, self).create(vals)
        return res
    
    # For canceling any invoice made from the order
    invoice_ids = fields.Many2many("account.move", string='Invoices', readonly=True, copy=False, search="_search_invoice_ids")

    # Going to the next item in the sequence
    def jump_state(self):
        self.state = 'sent'

    def CancelState(self):
        cancel_warning = self._show_cancel_wizard()
        if cancel_warning:
            return {
                'name': _('Cancel Sales Order'),
                'view_mode': 'form',
                'res_model': 'sale.order.cancel',
                'view_id': self.env.ref('sale.sale_order_cancel_view_form').id,
                'type': 'ir.actions.act_window',
                'context': {'default_order_id': self.id},
                'target': 'new'
            }
        return self._action_cancel()

    def _action_cancel(self):
        inv = self.invoice_ids.filtered(lambda inv: inv.state == 'draft')
        inv.button_cancel()
        return self.write({'state': 'cancel'})
    
    def _show_cancel_wizard(self):
        for order in self:
            if order.invoice_ids.filtered(lambda inv: inv.state == 'draft') and not order._context.get('disable_cancel_warning'):
                return True
        return False

    def toDraft(self):
        self.state = 'draft'
    
    # Name of the operation.
    name = fields.Char(string='Order ID', required=True, copy=False, readonly=True, default=lambda self: _('New Order'))

    # Order Type selector

   #ordertype = fields.Selection([
    #    ('cg', '采购 Common Purchase'),
    #    ('ycyc', '一城一策 Bonus YCYC'),
    #    ('fk', '返款 Buyback/Cashback'),
    #    ('jlg', '奖励柜 Bonus Freezer'),
    #    ('zhg', '整合柜 Integrated Freezer'),
    #    ('mfg', '免费柜 Unit Free'),
    #    ('gtjlg', '公投奖励柜 Bonus GTG'),
    #    ('bfg', '报废柜 Penghancuran'),
    #   ('mtg', '免投柜 Support Free'),
    #], string = 'Order Type',required=True, default='cg', tracking=True)

    ordertype = fields.Many2one('fom.ordertype',string="Order Type", required=True, tracking=True)
    
    
    # Gets the actual datte time from the server.
    dateorder = fields.Datetime(string='Order Date', required=True, readonly=True, index=True, copy=False, default=fields.Datetime.now)

    # Maket type selector
    markettype = fields.Selection([
        ('gt', '传统渠道 Traditional Market'),
        ('mt', '现代渠道 Modern Market'),
        ('xyw', '新业务 New Business'),
        ('sm', '特殊渠道 Special Market'),
    ], string="Market Type", required=True, default='gt', tracking=True)

    # Gets the costumer array from db res.partner
    customer_id = fields.Many2one(
        'res.partner', string='Customer',
        required=True, change_default=True, index=True, tracking=True)
    note = fields.Text(string='Description')
    
    # Array of status names.
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('freezer_order', 'Freezer Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ], string='Status', default='draft', tracking=True)
   
    # Order line page
    # it will pull a list of the items you're adding to the list.
    order_line = fields.One2many('fom.order.line', 'order_id', string='Order Lines', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True)
    t_amt = fields.Float(string='Total Amount', compute='_compute_total_amount', store=True)
    untaxed_amount = fields.Float(string='Untaxed Amount', compute='_compute_untaxed_amount', store=True)
    amount_taxed = fields.Float(string='Amount Taxed', compute='_compute_amount_taxed', store=True)

    # Archive / Unarchive
    active = fields.Boolean(string='Active', default=True, tracking=True)

    @api.depends('order_line.subtotal')
    def _compute_untaxed_amount(self):
        for ordem in self:
            ordem.untaxed_amount = sum(ordem.order_line.mapped('subtotal'))

    @api.depends('order_line.subtotal', 'order_line.tax')
    def _compute_amount_taxed(self):
        for ordem in self:
            ordem.amount_taxed = sum(ordem.order_line.mapped('tax'))
            ordem.t_amt = ordem.untaxed_amount + ordem.amount_taxed

    # calculate te total with tax
    @api.depends('order_line.subtotal', 'amount_taxed')
    def _compute_total_amount(self):
        for ordem in self:
            ordem.t_amt = ordem.untaxed_amount + ordem.amount_taxed

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    # Responsable to move the order to the inventory and creating a purchase order on the purchase module.
    def DoneState(self):
        # Responsable for changing the state of the order, once the function returns true.
        self.state = 'freezer_order'

        # Creating the purchase order parammeters.
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.customer_id.id,
            'date_order': self.dateorder,
            'picking_type_id': 1,
            'company_id': self.company_id.id,
            'origin': self.name,
            'order_line': [(0, 0, {
                'name': line.product_id.name,
                'product_id': line.product_id.id,
                'product_qty': line.product_uom_qty,
                'product_uom': line.product_id.uom_id.id,
                'price_unit': line.price_unit,
                'taxes_id': [(6, 0, line.tax_id.ids)] if line.tax_id else False,
            }) for line in self.order_line],
        })

        # Returns true if purchase order was successfully created.
        return True
    
# Class responsable for The item list itself.
class FomOrderLine(models.Model):
    _name = 'fom.order.line'
    _description = 'Freezer Order Line'
    _check_company_auto = True

    #
    #qtytype = fields.Many2one('fom.qtytype',string="Qty Type", required=True, tracking=True)
    
    
    qtytype = fields.Selection([
        ('dg', '代购 Purchased behalf of Aice'),
        ('gtg', '公投柜 Aice-provided'),
        ('pp', '匹配 Aice-support'),
        ('mf', '免费 Free'),
        ('bf', '报废 Freezer Scrap'),
        ('mt', '免投 Aice-invested'),
    ], string="Qty Type", required=True, default='dg', tracking=True)

    # Product field
    product_id = fields.Many2one('product.product', string='Product', domain=[('purchase_ok', '=', True)], change_default=True)
    # Quantity field
    product_uom_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True, default=1.0)
    # Price field
    price_unit = fields.Float('Unit Price', required=True, digits='Product Price', default=0.0)
    # the id of the order
    order_id = fields.Many2one('fom.order', string='Order Reference', required=True, ondelete='cascade', index=True, copy=False)
    # Subtotal
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store = True)
    
    tax_id = fields.Many2one('account.tax', string='Tax')
    tax = fields.Float(string='Tax', compute='_compute_tax', store=True)

    @api.depends('tax_id', 'subtotal')
    def _compute_tax(self):
        for linha_pedido in self:
            linha_pedido.tax = linha_pedido.subtotal * (linha_pedido.tax_id.amount / 100) if linha_pedido.tax_id else 0.0
   
    # Getting the dependency
    @api.depends('product_uom_qty', 'price_unit', 'tax_id')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal =  line.product_uom_qty * line.price_unit 




# Class for products
class FomProducts(models.Model):
    _name = "fom.products"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Freezer Product"
    
    #defining a sequence number for the name.
    name = fields.Char(string='Product Name', required=True)
    reference = fields.Char(string='Product Reference', readonly=True, default=lambda self: _('New Product'))

    @api.model
    def create(self, vals):
        if not vals.get('reference') or vals['reference'] == _('New Product'):
            sequence = self.env['ir.sequence'].next_by_code('fom.products') or _('New Product')
            vals['reference'] = sequence
        res = super(FomProducts, self).create(vals)
        return res
    order = fields.Integer(string="Order")

    # Going to the next item in the sequence
    def can_sell(self):
        self.state = 'sell'

    def cant_sell(self):
        self.state = 'not_sell'

    # Product name
    prod_name = fields.Char(string="Product Reference", required=True, copy=False, readonly=True, default=lambda self: _('New Product'))
    # Internal Reference
    vis_name = fields.Char(string="Product Name", required=True)
    # Price
    price = fields.Float(string="Sell Price", required=True)
    # Quantity
    qty_in_hands = fields.Integer(string="Quantity In Stock", required=True)
    # Created when ?
    created_when = fields.Datetime(string="Created When", readonly=True, default=fields.Datetime.now)

    # Array of status names.
    state = fields.Selection([
        ('sell', 'Can Sell'),
        ('not_sell', 'Cant Sell'),
        ], string='Status', default='sell', tracking=True)
 