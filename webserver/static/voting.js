function submitVote(voteform) {
    console.log(voteform);
    console.log(typeof voteform);

    $.ajax({
        url: "/api/submitvote" + "?id=" + voter_id + "&ctx=" + voter_secretkey,
        type: "POST",
        data: new FormData(voteform),
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

        console.log(document.querySelector("#voteform"));
        console.log(typeof document.querySelector("#voteform"));
        
        submitVote(document.querySelector("#voteform"));
    }
});

$("#voteform").on('submit', function(e) {
    e.preventDefault();
    
    console.log(this);
    console.log(typeof this);

    submitVote(this);
});