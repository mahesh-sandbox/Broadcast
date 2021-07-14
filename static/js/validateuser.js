$(function() {
  $('a#validate').bind('click', function() {
    $("#result").text("Validating Users ... Please Wait");
    $.getJSON('/validate', json={
     users : " {{  details["user_list"]  }} ",
     scrum_masters : " {{ details["scrum_master"] }} "  
    },
    function(data) {
      $("#result").text(data);
    });
    return false;
  });
});
