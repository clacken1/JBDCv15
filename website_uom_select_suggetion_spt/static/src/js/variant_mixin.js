odoo.define('website_uom_select_suggetion_spt.VariantMixin', function(require){
    'use strict';
    
    var VariantMixin = require('sale.VariantMixin');
    var ajax = require('web.ajax');

    /**
     * @see onChangeVariant
     * @override
     * @private
     * @param {Event} ev
     * @returns {Deferred}
     */
    VariantMixin._getCombinationInfo = function (ev) {
        debugger;
        var self = this;
        if ($(ev.target).hasClass('variant_custom_value')) {
            return Promise.resolve();
        }

        var $parent = $(ev.target).closest('.js_product');
        var qty = $parent.find('input[name="add_qty"]').val();
        var combination = this.getSelectedVariantValues($parent);
        var parentCombination = $parent.find('ul[data-attribute_exclusions]').data('attribute_exclusions').parent_combination;
        var productTemplateId = parseInt($parent.find('.product_template_id').val());

        self._checkExclusions($parent, combination);
        var vals = {
            'product_template_id': productTemplateId,
            'product_id': this._getProductId($parent),
            'combination': combination,
            'add_qty': parseInt(qty),
            'pricelist_id': this.pricelistId || false,
            'parent_combination': parentCombination,
            'uom_id': $('#uom_id').find("option:selected").data("uom_id"),
        };

        return ajax.jsonRpc(this._getUri('/sale/get_combination_info'), 'call', vals).then(function (combinationData) {
            self._onChangeCombination(ev, $parent, combinationData);
        });
    };

    return VariantMixin;
});