var register_button = document.getElementById("register_button");
var admin_button = document.getElementById("admin_login_button");
var auth_voter = document.getElementById("authVoter");
let url_redirect = "http://localhost:8000/";
let api_url = "http://localhost:8000/api/login";

auth_voter.addEventListener("click", function(e) {
    e.preventDefault();

    let voter_id = document.querySelector("#voter_id");
    let voter_secretkey = document.querySelector("#voter_secretkey");
    let voter_dob = document.querySelector("#voter_dob");
    let voting_url = "http://localhost:8000/api/login/ui"

    let xhr = new XMLHttpRequest();
    
    xhr.open("POST", api_url, true);
    xhr.setRequestHeader("Content-Type", "application/json");

    xhr.onreadystatechange = function() {
        if(this.readyState === 4 && this.status === 200) {
            window.location.assign(voting_url + "?id=" + voter_id.value + "&ctx=" + voter_secretkey.value);
        }

        else {
            document.body.innerText = "Error! Please login again";

            setTimeout(function() {window.location.replace(url_redirect);}, 5000);
        }
    }

    var payload = JSON.stringify({"voter_id": voter_id.value, "voter_secretkey": voter_secretkey.value, "voter_dob": voter_dob.value});

    xhr.send(payload);
});

register_button.addEventListener("click", function(e) {
    e.preventDefault();

    let register_url_redirect = "http://localhost:8000/register";

    window.location.assign(register_url_redirect);
});

admin_button.addEventListener("click", function(e) {
    e.preventDefault();

    let admin_url_redirect = "http://localhost:8000/adminlogin";

    window.location.replace(admin_url_redirect);
});