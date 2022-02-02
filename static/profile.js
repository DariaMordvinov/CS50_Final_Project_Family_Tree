  // This code will attach `fileselect` event to all file inputs on the page
  $(document).on('change', ':file', function() {
    var input = $(this),
        numFiles = input.get(0).files ? input.get(0).files.length : 1,
        label = input.val().replace(/\\/g, '/').replace(/.*\//, '');
    input.trigger('fileselect', [numFiles, label]);
  });


  $(document).ready( function() {
//below code executes on file input change and append name in text control
      $(':file').on('fileselect', function(event, numFiles, label) {

          var input = $(this).parents('.input-group').find(':text'),
              log = numFiles > 1 ? numFiles + ' files selected' : label;

          if( input.length ) {
              input.val(log);
          } else {
              if( log ) alert(log);
          }

      });
  });


function OpenForm() {
    document.getElementById("HideDiv").style.display = "none";
    document.getElementById("EditForm").style.display = "block";
}


$(".carousel-item").first().addClass("active");


function openForm() {
  document.getElementById("deleteImg").style.display = "block";
  var img = $(".carousel-item.active").attr('id');
  document.getElementById("delete").value = img;
}

function closeForm() {
  document.getElementById("deleteImg").style.display = "none";
}


var person = $(".headline").html()
$(".delete_person").click(function() {window.open("delete/" + person, '_self' )})