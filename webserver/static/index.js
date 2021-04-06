var register_button = document.getElementById("register_button");
var admin_button = document.getElementById("admin_login_button");
var auth_voter = document.getElementById("authVoter");
let url_redirect = "https://hritvikpatel.me";
let api_url = "https://hritvikpatel.me/api/login";

function authorize() {
    let voter_id = document.querySelector("#voter_id");
    let voter_secretkey = document.querySelector("#voter_secretkey");
    let voter_dob = document.querySelector("#voter_dob");
    let voting_url = "https://hritvikpatel.me/api/login/ui"

    let xhr = new XMLHttpRequest();
    
    xhr.open("POST", api_url, false);
    xhr.setRequestHeader("Content-Type", "application/json");

    xhr.onreadystatechange = function() {
        if(this.readyState === 4 && this.status === 200) {
            window.location.assign(voting_url + "?id=" + voter_id.value + "&ctx=" + voter_secretkey.value);
        }

        else {
            document.body.innerText = "Error! Please login again";

            setTimeout(function() {window.location.replace(url_redirect);}, 10000);
        }
    }

    var payload = JSON.stringify({"voter_id": voter_id.value, "voter_secretkey": voter_secretkey.value, "voter_dob": voter_dob.value});

    xhr.send(payload);
}

$("input").keypress(function(e) {
    if(e.which == 13) {
        e.preventDefault();
        authorize();
    }
});

auth_voter.addEventListener("click", function(e) {
    e.preventDefault();

    authorize();
});

register_button.addEventListener("click", function(e) {
    e.preventDefault();

    let register_url_redirect = "https://hritvikpatel.me/register";

    window.location.assign(register_url_redirect);
});

admin_button.addEventListener("click", function(e) {
    e.preventDefault();

    let admin_url_redirect = "https://hritvikpatel.me/adminlogin";

    window.location.replace(admin_url_redirect);
});