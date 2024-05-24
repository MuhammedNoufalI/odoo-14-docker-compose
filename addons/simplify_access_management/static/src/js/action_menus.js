/** @odoo-module **/
odoo.define('simplify_access_management.ActionMenus', function (require) {
    "use strict";
    const Registry = require('web.Registry');
    const registry = require('web_grid.component_registry');
    const ActionMenus = require('web.ActionMenus');
    const { Component } = owl;
    var core = require('web.core');
    let registryActionId = 0;
    var rpc = require('web.rpc');
    var _t = core._t;
    var QWeb = core.qweb;

    ActionMenus.prototype._setActionItems = async function(props){
        // ************************************
        // Get restricted actions
        const RestActions = await this.rpc({
            model: 'access.management',
            method: 'get_remove_options',
            args: [1, this.env.searchModel.config.modelName]
        });

        // ************************************

        // Callback based actions
        let callbackActions = (props.items.other || []).map(
            action => Object.assign({ key: `action-${action.description}` }, action)
        );

        // Action based actions
        const actionActions = props.items.action || [];
        const relateActions = props.items.relate || [];
        const formattedActions = [...actionActions, ...relateActions].map(
            action => ({ action, description: action.name, key: action.id })
        );
        // ActionMenus action registry components
        const registryActions = [];
        const rpc = this.rpc.bind(this);
        for (const { Component, getProps } of this.constructor.registry.values()) {
            const itemProps = await getProps(props, this.env, rpc);
            if (itemProps) {
                registryActions.push({
                    Component,
                    key: `registry-action-${registryActionId++}`,
                    props: itemProps,
                });
            }
        }
        // filter restricted callback actions
        if(RestActions.length){
            callbackActions = _.filter(callbackActions,function(val){
                return !_.contains(RestActions,val.description)
            })
        }
        return [...callbackActions, ...formattedActions, ...registryActions];
    }

});
