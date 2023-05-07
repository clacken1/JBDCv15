odoo.define('website_uom_select_suggetion_spt.WarningMessage', function (require) {
    'use strict';

    const { Markup } = require('web.utils');
    var VariantMixin = require('sale.VariantMixin');
    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var QWeb = core.qweb;

    const loadXml = async () => {
        return ajax.loadXML('/website_uom_select_suggetion_spt/static/src/components/warning_msg.xml', QWeb);
    };

    require('website_sale.website_sale');

    /**
     * Addition to the variant_mixin._onChangeCombination
     *
     * This will prevent the user from selecting a quantity that is not available in the
     * stock for that product.
     *
     * It will also display various info/warning messages regarding the select product's stock.
     *
     * This behavior is only applied for the web shop (and not on the SO form)
     * and only for the main product.
     *
     * @param {MouseEvent} ev
     * @param {$.Element} $parent
     * @param {Array} combination
     */
    VariantMixin._onChangeCombinationStock = function (ev, $parent, combination) {
        let product_id = 0;
        // needed for list view of variants
        if ($parent.find('input.product_id:checked').length) {
            product_id = $parent.find('input.product_id:checked').val();
        } else {
            product_id = $parent.find('.product_id').val();
        }
        const isMainProduct = combination.product_id &&
            ($parent.is('.js_main_product') || $parent.is('.main_product')) &&
            combination.product_id === parseInt(product_id);

        if (!this.isWebsite || !isMainProduct) {
            return;
        }
        debugger;
        const $addQtyInput = $parent.find('input[name="add_qty"]');
        let qty = $addQtyInput.val();

        $parent.find('#add_to_cart').removeClass('out_of_stock');
        $parent.find('.o_we_buy_now').removeClass('out_of_stock');
        if (combination.product_type === 'product' && !combination.allow_out_of_stock_order) {
            combination.free_qty -= parseInt(combination.cart_qty);
            $addQtyInput.data('max', combination.uom_free_qty || 1);
            if (combination.uom_free_qty < 0) {
                combination.uom_free_qty = 0;
            }
            if (qty > combination.uom_free_qty) {
                qty = combination.uom_free_qty || 1;
                $addQtyInput.val(qty);
            }
            if (qty > combination.uom_free_qty || combination.uom_free_qty < 1 || qty < 1 || qty > combination.uom_factor_inv) {
                $parent.find('#add_to_cart').addClass('disabled out_of_stock');
                $parent.find('.o_we_buy_now').addClass('disabled out_of_stock');
            }
        }

        debugger;
        ajax.jsonRpc('/sale-order', 'call', combination)
            .then(function (val) {
                var uom = val['uom']
                var qty = val['qty']
                var product_uom = val['product_uom']
                combination['selected_uom'] = uom;
                combination['ordered_qty'] = qty
                combination['product_uom'] = product_uom

                loadXml().then(function () {
                    $('.oe_website_sale')
                        .find('.availability_message_' + combination.product_template)
                        .remove();

                    var $message = $(QWeb.render(
                        'website_uom_select_suggetion_spt.product_availability_',
                        combination
                    ));
                    $('div.availability_messages').html($message);
                });

            })
    };

});
