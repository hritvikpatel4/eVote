var auth_admin = document.getElementById("authAdmin");
var voter_button = document.getElementById("voter_login_button");

auth_admin.addEventListener("click", function(e) {
    e.preventDefault();

    let admin_id = document.querySelector("#admin_id");
    let admin_masterpwd = document.querySelector("#admin_masterpwd");

    let api_url = "http://34.117.18.201:80/api/admin/login";
    let adminui_url = "http://34.117.18.201:80/api/admin/ui";

    let xhr = new XMLHttpRequest();

    xhr.open("POST", api_url, true);
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
});

voter_button.addEventListener("click", function(e) {
    e.preventDefault();

    let voter_url_redirect = "http://34.117.18.201:80/";

    window.location.replace(voter_url_redirect);
});