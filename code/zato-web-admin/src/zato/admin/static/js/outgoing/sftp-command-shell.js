$(document).ready(function() {

    _.each(['data'], function(name) {
        $.fn.zato.data_table.set_field_required('#' + name);
    });

    $('#command_shell_form').bValidator();

    var _callback = function(data, status, xhr){

        console.log('QQQ ' + data);
        console.log('WWW ' + status);

        var success = status == 'success';
        var msg = success ? data.msg : data.responseText;
        $.fn.zato.user_message(success, msg);

        if(success) {
            if(data.stdout) {
                $('#id_stdout').text(data.stdout);
            };
            if(data.stderr) {
                $('#id_stderr').text(data.stderr);
            }
        }
    }

    var options = {
        success: _callback,
        error:  _callback,
        resetForm: false,
        'dataType': 'json',
    };

    $('#command_shell_form').submit(function() {
        $(this).ajaxSubmit(options);
        return false;
    });
});
