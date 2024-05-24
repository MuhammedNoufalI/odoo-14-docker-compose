odoo.define('loan_portal.perform', function (require) {
    "use strict";
    var sAnimations = require('website.content.snippets.animation');
    sAnimations.registry.loans = sAnimations.Class.extend({
        selector: '#loans',
        read_events: {
           'change #employee': '_onChangeemployee',
        },
        init: function () {
            this._super.apply(this, arguments);
        },

        start: function () {
            var def = this._super.apply(this, arguments);
            return def;
        },

        _onChangeemployee:function(ev){
            var self = this;
            var emp_id = ev.currentTarget.value;
            console.log('kkkkkkkk',emp_id)
            this._rpc({
                model: 'hr.employee',
                method: 'get_dept_and_job',
                args: [parseInt(emp_id)],
            }).then( function (res) {
                    console.log('jjjjjj',res)
                    $('#department').attr('value',res[0]);
                    $('#job').attr('value',res[1])
                });
        },



    });

});
