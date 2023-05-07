from odoo import api, SUPERUSER_ID

def kits_multi_uom_post_install_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['product.template'].sudo().search([])._get_uom_category()