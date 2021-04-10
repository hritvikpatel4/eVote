function submitVote(voteform) {
    console.log(voteform);
    console.log(typeof voteform);

    $.ajax({
        url: "/api/submitvote" + "?id=" + voter_id + "&ctx=" + voter_secretkey,
        type: "POST",
        data: new FormData(voteform),
        processData: false,
        contentType: false,
        async: false,
        success: function(data, textStatus, jqXHR) {
            var showsnack = document.getElementById("snackbar");
            showsnack.innerText = "Success! Now redirecting to the login page"
            showsnack.className = "show";

            setTimeout(function() {
                showsnack.className = showsnack.className.replace("show", "");
            }, 3000);

            setTimeout(function() {
                window.location.replace("https://hritvikpatel.me");
            }, 4000);
        },
        error: function(jqXHR, textStatus, errorThrown) {
            var showsnack = document.getElementById("snackbar");
            showsnack.innerText = "Error! Please try again"
            showsnack.className = "show";

            setTimeout(function() {
                showsnack.className = showsnack.className.replace("show", "");
            }, 3000);
        }
    });
}

$("input").keypress(function(e) {
    if(e.which == 13) {
        e.preventDefault();
        
        submitVote(document.querySelector("#voteform"));
    }
});

$("#voteform").on('submit', function(e) {
    e.preventDefault();

    submitVote(this);
});