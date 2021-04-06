var auth_admin = document.getElementById("authAdmin");
var voter_button = document.getElementById("voter_login_button");

function authorize_admin() {
    let admin_id = document.querySelector("#admin_id");
    let admin_masterpwd = document.querySelector("#admin_masterpwd");

    let api_url = "https://hritvikpatel.me/api/admin/login";
    let adminui_url = "https://hritvikpatel.me/api/admin/ui";

    let xhr = new XMLHttpRequest();

    xhr.open("POST", api_url, false);
    xhr.setRequestHeader("Content-Type", "application/json");

    xhr.onreadystatechange = function() {
        if(this.readyState === 4 && this.status === 200) {
            window.location.assign(adminui_url + "?id=" + admin_id.value + "&ctx=" + admin_masterpwd.value);
        }

        else {
            document.body.innerHTML = this.responseText;
        }
    }

    var payload = JSON.stringify({ "admin_id": admin_id.value, "admin_masterpwd": admin_masterpwd.value});

    xhr.send(payload);
}

auth_admin.addEventListener("click", function(e) {
    e.preventDefault();

    authorize_admin();
});

$("input").keypress(function(e) {
    if(e.which == 13) {
        e.preventDefault();
        authorize_admin();
    }
});

voter_button.addEventListener("click", function(e) {
    e.preventDefault();

    let voter_url_redirect = "https://hritvikpatel.me";

    window.location.replace(voter_url_redirect);
});