function submitVote() {
    $.ajax({
        url: "/api/submitvote" + "?id=" + voter_id + "&ctx=" + voter_secretkey,
        type: "POST",
        data: new FormData(document.getElementById("voteform")),
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
}

$("input").keypress(function(e) {
    if(e.which == 13) {
        e.preventDefault();
        submitVote();
    }
});

$("#voteform").on('submit', function(e) {
    e.preventDefault();

    submitVote();
})

// $(document).on("submit", "form", function(e) {
//     e.preventDefault();

//     submitVote();
// });