{'name': 'Odoo Select Product UOM In Website',
'summary': 'This app allows you to configure product-wise multi-uom. and on the website users can buy products in any UOM as per the configuration.\nodoo website multi uom, odoo multi-uom,odoo select uom in website, secondary product uom, configure odoo uom, odoo website uom',
'description': 'This app allows you to configure product-wise multi-uom. and on the website users can buy products in any UOM as per the configuration.\nodoo website multi uom, odoo multi-uom,odoo select uom in website, secondary product uom, configure odoo uom, odoo website uom',
'author': 'Keypress IT Services',
'website': '',
'category': 'Website/Ecommerce',
'version': '15.0.0.2',
'depends': ['stock', 'sale_management', 'website_sale', 'website_sale_stock', 'sale'],
'data': ['views/product_template_view.xml', 'templates/templates.xml'],
'demo': [],
'qweb': ['static/src/components/warning_msg.xml'],
'installable': True,
'application': True,
'price': '30',
'currency': 'USD',
'images': ['static/description/Banner.png'],
'post_init_hook': 'kits_multi_uom_post_install_hook',
'live_test_url': 'https://www.youtube.com/watch?v=gVkMrjyisys',
'assets':{
    'web.assets_frontend': [
        'website_uom_select_suggetion_spt/static/src/js/variant_mixin.js',
        'website_uom_select_suggetion_spt/static/src/js/website_sale.js',
        'website_uom_select_suggetion_spt/static/src/js/warning_msg.js',
    ],
    # 'web.assets_backend': [
    #     '/website_uom_select_suggetion_spt/static/src/js/variant_mixin.js'
    # ],
},
}
