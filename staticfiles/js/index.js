let more_options = document.getElementById("more_options");
let more_options_div = document.getElementById("more_options_div");

// Toggle display of more_options_div when the more_options button is clicked
more_options.addEventListener("click", function(event) {
  event.preventDefault();  // Prevents the default anchor behavior
  more_options_div.style.display = more_options_div.style.display === "grid" ? "none" : "grid";
});

// Hide the div when clicking outside of it
document.addEventListener("click", function(event) {
  let isClickInside = more_options_div.contains(event.target) || more_options.contains(event.target);

  if (!isClickInside) {
    more_options_div.style.display = "none";  // Hide the div if the click is outside
  }
});





// Initialize reply button functionality
// function initializeReplyButtons() {
//   document.querySelectorAll('.reply').forEach(reply => {
//     reply.addEventListener('click', function () {
//       const targetId = this.getAttribute('data-target');
//       const replySection = document.getElementById(targetId);
//       if (replySection) {
//         // Toggle the visibility of the reply section
//         replySection.style.display = replySection.style.display === 'none' ? 'block' : 'none';
//       }
//     });
//   });
// }

$(document).ready(function () {
  $(".like-button").click(function () {
    const postId = $(this).data("post-id");
    const csrfToken = $("#csrf_token").val();
    const $this = $(this); // Reference to the clicked button

    $.ajax({
      url: `/like/${postId}/`,
      type: "POST",
      headers: {
        "X-CSRFToken": csrfToken,
      },
      success: function (response) {
        // Update the like count with the formatted value
        const likeCount = response.count; // This is already formatted from the server
        $(`.likes[data-post-id="${postId}"]`).text(`${likeCount} Likes`); // Update the like count display

        // Toggle the like button image using data attributes
        if (response.liked) {
          $this.attr("src", $this.data("liked-src")); // Use the liked image source
        } else {
          $this.attr("src", $this.data("unliked-src")); // Use the unliked image source
        }
      },
      error: function (xhr) {
        console.error("Error liking the post:", xhr.responseText);
      },
    });
  });

  // Update like counts every 90 seconds
  setInterval(function () {
    $(".like-button").each(function () {
      const postId = $(this).data("post-id");
      $.ajax({
        url: `/like-count/${postId}/`,
        type: "GET",
        success: function (response) {
          $(`.likes[data-post-id="${postId}"]`).text(`${response.count} Likes`); // Ensure correct element
        },
      });
    });
  }, 90000);
});


// Loop through each form and attach a listener to the input field

// // Call the function initially to bind event listeners
// setTimeout(initializeReplyButtons, 1);
