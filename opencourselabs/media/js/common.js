/* CCI:U Common Javascript Library */
var suppressAjaxErrors = false;

var LoadingIndicator = {
	show: function() {
		Notifier.clear();
		$('.ajax-loading-indicator').show();
	},
	hide: function() {
		$('.ajax-loading-indicator').fadeOut(250);
	},
	msg: function(text) {
		$('.ajax-message').text(text);
	},
	inject: function(target) {
		var me = this;
		if ($(target).length == 0)
			return;
		$(target).append('<div class="ajax-loader"><div class="ajax-loading-indicator" style="display:none"></div><div class="ajax-message"></div></div>');
		$('.ajax-loading-indicator').ajaxStart(function(ev, request, options, error) {
			me.show();
		});
		$('.ajax-loading-indicator').ajaxComplete(function(ev, request, options, error) {
			me.hide();
		});
		$('.ajax-message').ajaxError(function(ev, request, options, error) {
			if (suppressAjaxErrors)
				return;
			var msg, i;
			if (request.status == 200 && request.getResponseHeader('X-Reason-For-Redirect') == 'login') {
				$.clearIntervals();
				alert('You have logged out!');
				return;
			}
			switch (request.status) {
				case 400: msg = 'Server could not understand your request. Confirm your action is valid.'; break;
				case 403: msg = 'Permission denied.'; break;
				case 500: msg = 'Error in the server, we will fix this problem as soon as possible.'; break;
				default:
					if (error == undefined)
						msg = 'We cannot connect to the server.';
					else
						msg = error;
			}
			alert('Sorry, we have a problem:\n' + msg, 'Ajax Erorr');
		});
	}
};

var Notifier = {
	notify: function(type, obj) {
		if (obj instanceof String) {
			var html = '<div class="notify-container"><div class="notify '+ type + '" style="display:none;">' + obj + '</div></div>';
			document.write(html);
		} else {
			// Better accessibility.
			$(obj).hide().addClass(type);
		}
		$(document).ready(function() {
			window.setTimeout(function () {
				$('.notify').css('opacity', '0').css('display', 'inline-block').animate({
					opacity: 1.0,
					duration: 400
				});
			}, 200);
		});
	},
	clear: function() {
		$('.notify').fadeOut(220);
	}
};

var intervals = [];

$.registerInterval = function(intervalId) {
	intervals.push(intervalId);
};
$.clearIntervals = function() {
	for (i = 0; i < intervals.length; i++) {
		window.clearInterval(intervals[i]);
	}
}

$(document).ready(function() {
	$.ajaxSetup({cache: false});
	LoadingIndicator.inject('.submit-area');
	$('form').submit(function(ev) {
		$('[type=submit]', this).disable();
		window.setTimeout(function() { LoadingIndicator.show(); }, 10);
	});
});
$(window).bind('beforeunload', function() {
	suppressAjaxErrors = true;
});

$.fn.disable = function(options) {
	var defaults = {
		className: 'ui-state-disabled'
	};
	var settings = $.extend({}, defaults, options);
	return this.each(function() {
		if (this.tagName == 'button' || this.tagName == 'input')
			$(this).attr('disabled', 'disabled').addClass(settings.className);
		else {
			var $elem = $(this);
			var current_events = $elem.data('events');
			var removed_events = []; // store all existing click events bound via jQuery
			if (!$elem.data('disabled')) {
				if (current_events) {
					$.each(current_events.click, function(index, item) {
						removed_events.push(item);
					});
				}
				$elem.unbind('click') // unbind all click events
				.bind('click', function(ev) { ev.preventDefault(); })
				.data('removed_events', removed_events)
				.data('disabled', true)
				.addClass(settings.className);
			}
		}
	});
};
$.fn.enable = function(options) {
	var defaults = {
		className: 'ui-state-disabled'
	};
	var settings = $.extend({}, defaults, options);
	return this.each(function() {
		if (this.tagName == 'button' || this.tagName == 'input')
			$(this).removeAttr('disabled').removeClass(settings.className);
		else {
			var $elem= $(this);
			var removed_events = $elem.data('removed_events');
			if ($elem.data('disabled')) {// restore saved click events
				$elem.unbind('click')
				.removeData('removed_events')
				.data('disabled', false)
				.removeClass(settings.className);
				if (removed_events) {
					$.each(removed_events, function(index, item) {
						$elem.bind('click', item);
					});
				}
			}
		}
	});
};

