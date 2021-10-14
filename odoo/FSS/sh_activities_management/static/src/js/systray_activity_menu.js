odoo.define('sh_activities_management.systray.ActivityMenu', function (require) {
"use strict";

var ActivityMenu = require('mail.systray.ActivityMenu');

var core = require('web.core');
var datepicker = require('web.datepicker');
var session = require('web.session');

var _t = core._t;

ActivityMenu.include({
    //-----------------------------------------
    // Handlers
    //-----------------------------------------
    /**
     * @override
     */
    _onActivityFilterClick: function (ev) {
        var $el = $(ev.currentTarget);
		var data = _.extend({}, $el.data());
		if (data.res_model === "calendar.event" && data.filter === "my") {
            this.do_action('calendar.action_calendar_event', {
                additional_context: {
                    default_mode: 'day',
                    search_default_mymeetings: 1,
                },
               clear_breadcrumbs: true,
            });
        }
		else if (data.res_model === "note.note" && data.filter === "my") {
			if (!$el.hasClass("o_note")) {
	            var data = _.extend({}, $el.data(), $(ev.target).data());
	            if (data.res_model === "note.note" && data.filter === "my") {
	                this.do_action({
	                    type: 'ir.actions.act_window',
	                    name: data.model_name,
	                    res_model:  data.res_model,
	                    views: [[false, 'kanban'], [false, 'form'], [false, 'list']]
	                }, {
	                    clear_breadcrumbs: true,
	                });
	            } else {
	                this._super.apply(this, arguments);
	            }
	        }
		}
		else{
			var data = _.extend({}, $(ev.currentTarget).data(), $(ev.target).data());
	        var context = {};
	        if (data.filter === 'my') {
	            context['search_default_activities_overdue'] = 1;
	            context['search_default_activities_today'] = 1;
	        } else {
	            context['search_default_activities_' + data.filter] = 1;
	        }
	        // Necessary because activity_ids of mail.activity.mixin has auto_join
	        // So, duplicates are faking the count and "Load more" doesn't show up
	        context['force_search_count'] = 1;
	        this.do_action({
	            type: 'ir.actions.act_window',
	            name: data.model_name,
	            res_model:  data.res_model,
	            views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
	            search_view_id: [false],
	            domain: [['activity_user_id', '=', session.uid],['activity_ids.active','=',true]],
	            context:context,
	        }, {
	            clear_breadcrumbs: true,
	        });
		}
    },
});
});
