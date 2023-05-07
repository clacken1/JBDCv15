odoo.define('website_uom_select_suggetion_spt.MultiUomWebsiteSale', function(require){
    "use strict";

    var publicWidget = require('web.public.widget');
    var KitsWebsiteSale = new publicWidget.registry.WebsiteSale();
    require('website_sale.website_sale');
    
    publicWidget.registry.WebsiteSale.include({
        /**
         * Initializes the optional products modal
         * and add handlers to the modal events (confirm, back, ...)
         * @override
         * @private
         * @param {$.Element} $form the related webshop form
         */
        _handleAdd: function ($form) {
            var self = this;
            this.$form = $form;
            var productSelector = [
                'input[type="hidden"][name="product_id"]',
                'input[type="radio"][name="product_id"]:checked'
            ];
            var productReady = this.selectOrCreateProduct(
                $form,
                parseInt($form.find(productSelector.join(', ')).first().val(), 10),
                $form.find('.product_template_id').val(),
                false
            );
            
            return productReady.then(function (productId) {
                $form.find(productSelector.join(', ')).val(productId);
                self.rootProduct = {
                    product_id: productId,
                    quantity: parseFloat($form.find('input[name="add_qty"]').val() || 1),
                    uom_id: parseInt($form.find('#uom_id').find(':selected').data('uom_id')),
                    product_custom_attribute_values: self.getCustomVariantValues($form.find('.js_product')),
                    variant_values: self.getSelectedVariantValues($form.find('.js_product')),
                    no_variant_attribute_values: self.getNoVariantAttributeValues($form.find('.js_product'))
                };
                return self._onProductReady();
            });
        },

        /**
         * Sets the url hash from the selected product options.
         * @override
         * @private
         */
        _setUrlHash: function ($parent) {
            var $attributes = $parent.find('input.js_variant_change:checked, select.js_variant_change option:selected');
            var $uom = $parent.find('select.js_uom_change option:selected');
            var attributeIds = _.map($attributes, function (elem) {
                return $(elem).data('value_id');
            });
            var uomId = $uom.data('uom_id')
            history.replaceState(undefined, undefined, '#attr=' + attributeIds.join(',') + '&uom=' + uomId);
        },

        _onChangeCombination: function (ev, $parent, combination) {
            var res = this._super.apply(this, arguments);
            $('#uom_name').text(combination.uom_name);
            return res;
        },
    });
    publicWidget.registry.MultiUOMWebsiteSale = publicWidget.Widget.extend(KitsWebsiteSale, {
        events:{
            'change #uom_id': 'onChangeUOM',
        },
        onChangeUOM:function(ev){
            KitsWebsiteSale.onChangeVariant(ev);
        }
    });
});