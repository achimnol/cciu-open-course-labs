/**
 * opt : uploadUrl, fileTypes, fileSizeLimit, removeUrl, keyFieldName
 */
(function($) {
jQuery.fn.fileUpload = function(options) {
	var settings = $.extend({
		uploadUrl: URL_BASE + "/file/json/upload.do",
		removeUrl: URL_BASE + "/file/json/remove.do",
		fileTypes: '*.*',
		fileTypesDescription: 'All Files',
		fileQueueLimit: 1, // only one file can be submitted.
		fileUploadLimit: -1,
		keyFieldName: 'file_keys',
		fileSizeLimit: "5mb",
		debug: false,
		buttonWindowMode: SWFUpload.WINDOW_MODE.TRANSPARENT,
		extraParams: {}
	}, options);
	var $key = Math.uuid();
	settings.uploadUrl += '?key=' + encodeURIComponent($key);
	
	if ($.fn.fileUploadCount) {
		$.fn.fileUploadCount++;
	} else {
		$.fn.fileUploadCount=0;
	}
	
	var buttonId = "swfupload_button_" + $.fn.fileUploadCount;
	
	this.addClass("fileUpload");
	
	var $keyInput = $("<input type='hidden'/>").attr("name", settings.keyFieldName).appendTo(this).val($key);
	var $filename = '';
	var $progress = $("<div class='file-progress-bar'><div class='file-progress'></div><div class='text'></div></div>").appendTo(this);
	var $upload = $("<div class='left'><div id='" + buttonId + "'>cancel</div></div>").appendTo(this);
	var $cancel = $("<a class='button-cancel'>&nbsp;</a>").appendTo(this).hide();
	this.append("<div class='clear'></div>");
	
	var onCancel = function() {
		$progress.children(".file-progress").css("width", "0%");
		$progress.children(".text").text("");
		$cancel.hide();
		if ($filename.length) {
			$.get(settings.removeUrl + "?key=" + encodeURIComponent($keyInput.val()) + '&filename=' + encodeURIComponent($filename));
			$filename = '';
		}
	};
	
	var onDlgComplete = function(numFilesSelected, numFilesQueued) {
		this.startUpload();
	};
	
	var onUploadStart = function(file) {
		// TODO: to allow multiple uploads, we should use better logic here.
		onCancel();
		$filename = file.name;
	};
	
	var onUploadError = function(file, error_code, message) {
		var text = error_code + ' : ' + message;
		$progress.children(".file-progress").css("width", "0%");
		$progress.children(".text").text(text);
		alert("Failed to upload: [" + error_code + "] " + message);
	};
	
	var onSuccess = function(file, server_data) {
		var data = eval("(" + server_data + ")");
		if (data.success) {
			if (settings.cancelButton) {
				$cancel.show();
			}
			
			if (settings.onSuccess) {
				settings.onSuccess(this);
			}
		} else {
			onUploadError(file);
		}
	};
	
	var onProgress = function(file, bytes_complete, bytes_total) {
		var percent = Math.ceil((bytes_complete / bytes_total) * 1000)/10;
		
		$progress.children(".file-progress").css("width", percent + "%");
		$progress.children(".text").text(file.name + " (" + percent + "%)");
	};
	
	var onQueueError = function(file, error_code, message) {
		var error_msg= "";
		switch(error_code) {
			case SWFUpload.ERROR_CODE_QUEUE_LIMIT_EXCEEDED:
				error_msg = "You have attempted to queue too many files.";
				break;
			case SWFUpload.QUEUE_ERROR.FILE_EXCEEDS_SIZE_LIMIT:
				error_msg = "File size can't exceed " + settings.fileSizeLimit;
				break;
			case SWFUpload.QUEUE_ERROR.ZERO_BYTE_FILE:
				error_msg = "Zero Byte File";
				break;
			case SWFUpload.QUEUE_ERROR.QUEUE_LIMIT_EXCEEDED:
				error_msg = "Upload limit reached";
				break;
			case SWFUpload.QUEUE_ERROR.INVALID_FILETYPE:
				error_msg = "File extension is not allowed";
				break;
			default:
				error_msg = "Unhandled error occured. Errorcode";
		}
		
		error_msg = "Failed to upload file : [" + error_code + "] " + error_msg; 
		if (file) {
			error_msg += "\r\n\r\nFile name : " + file.name + "\r\nFile size: " + file.size;
		}
		if (message) {
			error_msg += "\r\nError detail : " + message;
		}
		alert(error_msg);
	};
	
	$cancel.click(onCancel);

	this.swf = new SWFUpload({
		upload_url: settings.uploadUrl,
		post_params: settings.extraParams,
		file_types: settings.fileTypes,
		file_types_description: settings.fileTypesDescription,
		file_size_limit: settings.fileSizeLimit,
		file_upload_limit: settings.fileUploadLimit,
		file_queue_limit: settings.fileQueueLimit,
		flash_url: URL_BASE + "/js/swfupload.swf",
		button_placeholder_id: buttonId,
		button_image_url: URL_BASE + "/images/button-upload-browse.png",
		button_width: 80,
		button_height: 25,
		button_window_mode: settings.buttonWindowMode,
		file_dialog_complete_handler: onDlgComplete,
		upload_start_handler: onUploadStart,
		upload_success_handler: onSuccess,
		upload_progress_handler: onProgress,
		file_queue_error_handler: onQueueError,
		upload_error_handler: onUploadError,
		debug: settings.debug
	});
};

$.fn.fileUploadClear = function(options) {
	var $progress = this.find(".file-progress-bar");
	$progress.children(".file-progress").css("width", "0%");
	$progress.children(".text").text("");
	this.find(":input").val("");
};
})(jQuery);

/* vim: set ts=4 sts=4 sw=4 noet: */
