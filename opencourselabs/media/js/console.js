/* CCI:U Web Console Javascript Library */

var stateClasses = {
	0: 'state-pending',
	16: 'state-running',
	32: 'state-shuttingdown',
	48: 'state-terminted',
	64: 'state-pending',
	80: 'state-rebooting',
	160: 'state-broken',
	1600: 'state-broken'
}

var stateStrings = {
	0: 'Pending...',
	16: 'Running',
	32: 'Shutting down...',
	48: 'Terminated',
	64: 'Starting',
	80: 'Rebooting...',
	160: 'Broken!',
	1600: 'Missing!'
}

function getAllIds() {
	var ids = new Array();
	$.each($('td.select :checkbox'), function(index) {
		ids.push($(this).val());
	});
	return ids;
}

function getSelectedIds() {
	var ids = new Array();
	$.each($('td.select :checkbox'), function(index) {
		if ($(this).attr('checked')) {
			ids.push($(this).val());
		}
	});
	return ids;
}

function handleFailure(response) {
	if (response.data && response.data.errors && response.data.errors.length > 0) {
		switch (response.data.errors[0][0]) {
		case 'Action.NotPermitted':
			alert('We cannot perform the request operation because some instances are not at running state.'); break;
		case 'InvalidHost.NotAvailable':
			alert('We could not create the requested number of instances. (out of resources!)'); break;
		case 'InvalidAddress.NotAvailable':
			alert('We could not allocate a new public IP. (out of resources!)'); break;
		case 'InvalidInstance.NotFound':
			alert('The instances are not found.'); break;
		default:
			alert('Sorry, your request has failed:\n' + response.data.errors[0][0] + '\n' + response.data.errors[0][1], 'Error');
		}
	} else {
		alert('Sorry, your request has failed:\n' + response.message, 'Error');
	}
}

function allocateIP(id) {
	$.getJSON('?action=allocateIP&id=' + id, function(response) {
		if (response.result == 'success')
			refresh([id]);
		else
			handleFailure(response);
	});
}

function releaseIP(id) {
	$.getJSON('?action=releaseIP&id=' + id, function(response) {
		if (response.result == 'success')
			refresh([id]);
		else
			handleFailure(response);
	});
}

function refresh(ids) {
	var query_str;
	if (ids == undefined) {
		query_str = $.param({'target': getAllIds()});
	} else {
		query_str = $.param({'target': ids});
	}
	$.getJSON('?action=describe&' + query_str, function(response) {
		if (response.result == 'success') {
			$.each(response.data, function(i, item) {
				var state = item.state[0];
				$('#state-' + item.id)
				.removeClass()
				.addClass('state ' + stateClasses[state])
				.html(stateStrings[state]);
				if (state != 1600) {
					var id = item.id;
					if (item.elastic_ip) {
						$('#dns-' + id).html('<span class="ip">' + item.dns + '</span> / <span class="ip">' + item.elastic_ip + '</span>');
						if (is_staff) {
							$('#dns-' + id).append('&nbsp;')
							.append(
								$('<a>').addClass('operation releaseIP').click(function(ev) {
									releaseIP(id);
								}).text('X').attr('title', 'Release IP')
							);
						}
					} else {
						$('#dns-' + id).html('<span class="ip">' + item.dns + '</span>');
						if (is_staff) {
							$('#dns-' + id).append('&nbsp;')
							.append(
								$('<a>').addClass('operation associateIP').click(function(ev) {
									allocateIP(id);
								}).text('Allocate IP').attr('title', 'Allocate IP')
							);
						}
					}
					$('#launchtime-' + item.id).html(item.launch_time);
				} else {
					$('#dns-' + item.id).html('-');
					$('#launchtime-' + item.id).html('-');
				}
			});
		} else {
			handleFailure(response);
		}
	});
}

function reboot() {
	var ids = getSelectedIds();
	var query = {'target':ids};
	var i;
	for (i = 0; i < ids.length; i++) {
		$('#state-' + ids[i])
		.html(stateStrings[80])
		.removeClass()
		.addClass('state ' + stateClasses[80]);
	}
	$.getJSON('?action=reboot&' + $.param(query), function(response) {
		if (response.result == 'success') {
			window.setTimeout(function() {
				refresh(ids);
			}, 2000);
		} else {
			handleFailure(response);
		}
	});
}

function deleteInstances() {
	var ids = getSelectedIds();
	var query = {'target':ids};
	var i;
	for (i = 0; i < ids.length; i++) {
		$('#state-' + ids[i])
		.html('Deleting...')
		.removeClass()
		.addClass('state deleting');
	}
	$.getJSON('?action=delete&' + $.param(query), function(response) {
		if (response.result == 'success') {
			window.location.reload();
		} else {
			handleFailure(response);
		}
	});
}

function toggleInstance(id) {
	var checked = $('#checkbox-' + id).attr('checked');
	$('#row-' + id).toggleClass('selected', checked);
}

$(document).ready(function() {
	$.registerInterval(window.setInterval(function() {
		refresh();
	}, 20000));
});
