odoo.define('expense_portal.perform', function (require) {
    "use strict";
    var sAnimations = require('website.content.snippets.animation');
    sAnimations.registry.expenses = sAnimations.Class.extend({
        selector: '#expenses',
        read_events: {
           'change #product': '_onChangeproduct',
           'change #quantity': '_onChangeqty',
           'change #unit_price': '_onChangeunit_price',
        },
        init: function () {
            this._super.apply(this, arguments);
        },

        start: function () {
            var def = this._super.apply(this, arguments);
            return def;
        },

        _onChangeproduct:function(ev){
            var self = this;
            var product_id = ev.currentTarget.value;
            this._rpc({
                model: 'product.product',
                method: 'get_product_details',
                args: [parseInt(product_id)],
            }).then( function (res) {
                    console.log(res[0])
                    $('#unit_price').attr('value',res[0]);
                    $('#total').attr('value',res[0]*$('#quantity').val())
                });
        },
        _onChangeqty:function(ev){
            var self = this;
            var qty = ev.currentTarget.value;
            $('#total').attr('value',$('#unit_price').val()*qty)

        },
         _onChangeunit_price:function(ev){
            var self = this;
            var price = ev.currentTarget.value;
            $('#total').attr('value',$('#quantity').val()*price)

        },



    });

});
