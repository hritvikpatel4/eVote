let logout_url = "http://34.117.18.201:80/adminlogin";

$(document).ready(function() {
    $('#add_field_button').click(function(e) {
        e.preventDefault();
        e.stopPropagation();
        var temp_html = '<br/><div class="row formfields"><div class="col-sm form-floating"><input type="text" class="form-control" name="pn[]" required placeholder="a"><label for="party_name">Party Name</label></div><div class="col-sm"><label for="party_photo">Party Photo</label><input type="file" class="form-control" name="pp[]" required></div><div class="col-sm form-floating"><input type="text" class="form-control" name="rn[]" required placeholder="a"><label for="rep_name">Representative Name</label></div><div class="col-sm"><label for="rep_photo">Representative Photo</label><input type="file" class="form-control" name="rp[]" required></div></div>';
        $('body').find('.formfields:last').after(temp_html);    
    });
});

$(document).on("submit", "form", function(e) {
    e.preventDefault();

    $.ajax({
        url: "/api/election/create",
        type: "POST",
        data: new FormData(this),
        processData: false,
        contentType: false,
        success: function(data, status) {
            var showsnack = document.getElementById("snackbar");
            showsnack.innerText = "Success!"
            showsnack.className = "show";

            setTimeout(function() {
                showsnack.className = showsnack.className.replace("show", "");
            }, 3000);
        },
        error: function(data, status) {
            var showsnack = document.getElementById("snackbar");
            showsnack.innerText = "Error!"
            showsnack.className = "show";

            setTimeout(function() {
                showsnack.className = showsnack.className.replace("show", "");
            }, 3000);
        }
    });
});

$('#logout-button').click(function(e) {
    e.preventDefault();

    window.location.replace(logout_url);
});

$("#get_results").on('click', function(e) {
    e.preventDefault();

    $.ajax({
        url: "/api/election/complete",
        type: "GET",
        success: function(data, status) {
            console.log(data);
            var results_data = JSON.parse(data);
            document.getElementById("election-results").appendChild(document.createElement('pre')).innerHTML = JSON.stringify(results_data, undefined, 4);
        }
    })
});