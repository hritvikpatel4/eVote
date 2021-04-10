var register_footer = document.getElementById("register_footer");
var register_button = document.getElementById("register_button");
document.querySelector("#displaycode_card").style.display = "none";
document.querySelector("#displaycode_container").style.display = "none";
let api_url = "https://hritvikpatel.me/api/register";
let url_redirect = "https://hritvikpatel.me";

$(document).ready(() => {
    var today = new Date(Date.now());
    var date = ("0" + today.getDate()).slice(-2);
    var month = ("0" + (today.getMonth() + 1)).slice(-2);
    var year = today.getFullYear();
    var maxyear = year - 21;
    var minyear = year - 120;
    document.getElementById("voter_dob").setAttribute("max", `${maxyear}` + `-${month}-${date}`);
    document.getElementById("voter_dob").setAttribute("min", `${minyear}` + `-${month}-${date}`);
});

document.querySelector("#displaycode_close_button").addEventListener("click", function(e) {
    e.preventDefault();

    document.querySelector("#displaycode_card").style.display = "none";
    document.querySelector("#displaycode_container").style.display = "none";

    window.location.assign(url_redirect);
});

function showErrorMessage(message, duration) {
    var showsnack = document.getElementById("snackbar");
    showsnack.innerText = message;
    showsnack.className = "show";
    
    setTimeout(function() {
        showsnack.className = showsnack.className.replace("show", "");
    }, duration);
}

function check(year, month, day) {
	return new Date(year + 21, month - 1, day) <= new Date();
}

function register() {
    let voter_id = document.querySelector("#voter_id");
    let voter_name = document.querySelector("#voter_name");
    let voter_dob = document.querySelector("#voter_dob");

    var date = voter_dob.value.split("-");
    var checkeddate = check(parseInt(date[0]), parseInt(date[1]), parseInt(date[2]));

    if(checkeddate != true) {
        showErrorMessage("Error! You need to be over 21 years of age to register!", 5000);
        setTimeout(function() {window.location.replace("https://hritvikpatel.me/register");}, 5000);
    }

    else {
        let xhr = new XMLHttpRequest();
        
        xhr.open("POST", api_url, true);
        xhr.setRequestHeader("Content-Type", "application/json");

        xhr.onloadstart = function() {
            register_footer.innerHTML = '<div id="registering_progress" class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div>';
        }

        xhr.onload = function() {
            // document.querySelector("#registerForm").style.display = "none";
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
    }
}

$("input").keypress(function(e) {
    if(e.which == 13) {
        e.preventDefault();
        register();
    }
});

register_button.addEventListener("click", function(e) {
    e.preventDefault();
    
    register();
});