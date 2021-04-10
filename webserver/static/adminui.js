let logout_url = "https://hritvikpatel.me/adminlogin";

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
        success: function(data, textStatus, jqXHR) {
            var showsnack = document.getElementById("snackbar");
            showsnack.innerText = "Success!"
            showsnack.className = "show";

            setTimeout(function() {
                showsnack.className = showsnack.className.replace("show", "");
            }, 3000);
        },
        error: function(jqXHR, textStatus, errorThrown) {
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

$("#election_results").on('click', function(e) {
    e.preventDefault();

    console.log("Fetch Election Results event fired!");
    
    $.ajax({
        url: "https://hritvikpatel.me" + "/api/election/complete",
        type: "GET",
        async: false,
        success: function(data, textStatus, jqXHR) {
            if(jqXHR.status === 201) {
                var showsnack = document.getElementById("snackbar");
                showsnack.innerText = "Results will be sent shortly to your email...";
                showsnack.className = "show";

                setTimeout(function() {
                    showsnack.className = showsnack.className.replace("show", "");
                }, 5000);
            }
        }
    });
});

// $('.results_dropdown').on('show.bs.dropdown', function() {
//     console.log("Show Event fired!");

//     $.ajax({
//         url: "https://hritvikpatel.me" + "/api/election/complete",
//         type: "GET",
//         success: function(data, status) {

//             var winners = data["winners"];
//             $("#election_results").append(`<h2 class="text-center">Winners</h2>`);
//             for(var i = 0; i < winners.length; i++) {
//                 $("#election_results").append(`<p>${winners[i].replace("::", " ")}</p>`);
//             }

//             var final_result = data["final_result"];
//             $("#election_results").append(`<h3 class="text-center">Election Results</h3>`);
//             for(var i = 0; i < final_result.length; i++) {
//                 $("#election_results").append(`<p>${final_result[i][0].replace("::", " ")} - ${final_result[i][1]} votes</p>`);
//             }
//         }
//     });
// });

// $('.results_dropdown').on('hide.bs.dropdown', function() {
//     document.getElementById("election_results").innerHTML = "";
// });
