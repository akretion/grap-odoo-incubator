# Copyright 2013 - Today: GRAP (http://www.grap.coop)
# Copyright 2015-2019 Akretion France (http://www.akretion.com)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import models, fields, api
import odoo.addons.decimal_precision as dp


class StockInventoryLine(models.Model):
    _inherit = 'stock.inventory.line'

    @api.depends('standard_price', 'product_qty', 'product_uom_id')
    def _compute_valuation(self):
        for line in self:
            qty_product_uom = line.product_uom_id._compute_quantity(
                line.product_qty, line.product_id.uom_id)
            line.valuation = line.company_id.currency_id.round(
                line.standard_price * qty_product_uom)

    standard_price = fields.Float(
        string='Cost Price',
        digits=dp.get_precision('Product Price'),
        help='Cost Price in the unit of measure of the product')
    company_currency_id = fields.Many2one(
        related='company_id.currency_id', store=True)
    valuation = fields.Monetary(
        compute='_compute_valuation', currency_field='company_currency_id',
        readonly=True, string='Valuation', store=True)

    @api.onchange('product_id')
    def _onchange_product(self):
        res = super(StockInventoryLine, self)._onchange_product()
        if self.product_id:
            self.standard_price = self.product_id.standard_price
        return res

    @api.model
    def create(self, vals):
        if vals.get('product_id') and not vals.get('standard_price'):
            product = self.env['product.product'].browse(vals['product_id'])
            vals['standard_price'] = product.standard_price
        return super(StockInventoryLine, self).create(vals)


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    @api.depends('line_ids.valuation')
    def _compute_valuation(self):
        res = self.env['stock.inventory.line'].read_group(
            [('inventory_id', 'in', self.ids)],
            ['inventory_id', 'valuation'], ['inventory_id'])
        for re in res:
            if re['inventory_id']:
                inv = self.browse(re['inventory_id'][0])
                inv.valuation = inv.company_id.currency_id.round(
                    re['valuation'])

    company_currency_id = fields.Many2one(
        related='company_id.currency_id', store=True)
    valuation = fields.Monetary(
        compute='_compute_valuation', currency_field='company_currency_id',
        readonly=True, string='Valuation')
