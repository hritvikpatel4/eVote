var register_footer = document.getElementById("register_footer");
document.querySelector("#displaycode_card").style.display = "none";
document.querySelector("#displaycode_container").style.display = "none";
let api_url = "http://localhost:8000/api/register";
let url_redirect = "http://localhost:8000/";

document.querySelector("#displaycode_close_button").addEventListener("click", function(e) {
    e.preventDefault();

    document.querySelector("#displaycode_card").style.display = "none";
    document.querySelector("#displaycode_container").style.display = "none";

    window.location.assign(url_redirect);
});

var register_button = document.getElementById("register_button");
register_button.addEventListener("click", function(e) {
    e.preventDefault();
    
    let voter_id = document.querySelector("#voter_id");
    let voter_name = document.querySelector("#voter_name");
    let voter_dob = document.querySelector("#voter_dob");

    let xhr = new XMLHttpRequest();
    
    xhr.open("POST", api_url, true);
    xhr.setRequestHeader("Content-Type", "application/json");

    xhr.onloadstart = function() {
        register_footer.innerHTML = '<div id="registering_progress" class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div>';
    }

    xhr.onload = function() {
        document.querySelector("#displaycode_container").style.display = "block";
        document.querySelector("#displaycode_card").style.display = "block";
        document.querySelector("#displaycode_card").innerHTML = this.responseText;
        register_footer.innerHTML = '<button id="register_button" type="button" class="btn btn-primary" disabled>Register</button>';

        if(this.readyState === 4 && this.status === 400) {
            document.body.innerText = "Error! Voter already exists!";

            setTimeout(function() {window.location.replace(url_redirect);}, 5000);
        }
    }

    var payload = JSON.stringify({ "voter_id": voter_id.value, "voter_name": voter_name.value, "voter_dob": voter_dob.value});

    xhr.send(payload);
});