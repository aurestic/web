
odoo.define("web_listview_custom_column.main", function (require) {
    "use strict";

    var DebugManager = require("web.DebugManager");
    var session = require('web.session');

    DebugManager.include({
        customColumn: function(params, evt) {
            var view_id = params.id,
                self = this,
                context = _.extend({}, session.user_context, {
                    model_id: self._action.res_model,
                    view_id: view_id,
                });
            return this._rpc({
                model: 'list.custom.column.helper.wiz',
                method: 'create',
                args: [{}],
                context: context,
            }).then(function (wiz_id) {
                self.do_action({
                    res_model: 'list.custom.column.helper.wiz',
                    res_id: wiz_id,
                    type: 'ir.actions.act_window',
                    views: [[false, 'form']],
                    view_mode: 'form',
                    target: 'new',
                    flags: {action_buttons: true, headless: true},
                    context: context,
                });
            })
        },
    });
});
