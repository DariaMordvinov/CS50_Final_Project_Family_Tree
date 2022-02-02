function makeTree(generations) {
        var str = "";
        for (var i in generations) {
            str += "<div class='generation'>";
            for (var person in generations[i]) {
                var id = generations[i][person].split(' ').join('');
                if (generations[i][person].endsWith("add")) {
                    var end = generations[i][person].indexOf("add");
                    var value = generations[i][person].slice(0, end);
                }
                else {
                    var value = generations[i][person];
                }
                str += "<div class='person " + i + "' " + "id='" + id + "'>" + value + "</div>";
            }
            str += "</div><br><br>"
        }
        document.getElementById("tree").innerHTML = str;

        // Attaches onclick event listener: new tab opens with customized url (for each person in the tree)
        $(".person").each(function() {
        $( this ).on("click", function() {window.open("profile/" + this.id, '_blank')})})
    }

// Calling the function by creating the 'tree' variable
var tree = makeTree(generations);


// It is not recommended to put more than 10 persons in one generation. However this is a precaution:
// It will create more space between nodes to keep the tree clean. This is not ideal solution, of course :)

for (var i in generations) {
    if (i != 1 && (generations[i].length - generations[i - 1].length) >= 4) {
        var persons = document.getElementsByClassName(i-1);
        for (var each = 0; each < persons.length; each++) {
             persons[each].style.marginRight = "170px";
             persons[each].style.marginLeft = "170px";
        }
    }
    if (i != generations.length && i != 1 && (generations[i - 1].length - generations[i].length) >= 4) {
        var persons = document.getElementsByClassName(i);
        for (var each = 0; each < persons.length; each++) {
             persons[each].style.marginRight = "170px";
             persons[each].style.marginLeft = "170px";
        }
    }
    if (generations[i].length >= 5) {
        var persons = document.getElementsByClassName(i);
        for (var each = 0; each < persons.length; each++) {
             persons[each].style.marginRight = "55px";
             persons[each].style.marginLeft = "55px";
        }
    }
}


// These are the functions for drawing lines using object's coordinates. It is essential for visually connecting the people in the tree
function drawPath(line, source, target) {
   var x1 = source.offset().left + source.width()/2;
   var y1 = source.offset().top + source.height();
   var x2 = target.offset().left + target.width()/2;
   var y2 = target.offset().top + target.height();
   line.attr("d", "M " + x1 + "," + y1 + " L " + x2 + "," + y2);
   line.attr("position", "absolute");
}

function drawPathChild(line, parent1, parent2, child) {
   var parent1_x = parent1.offset().left + (parent1.width()/2);
   var parent2_x = parent2.offset().left + (parent2.width()/2);
   var x1 = Math.min(parent1_x, parent2_x) + (Math.abs(parent1_x - parent2_x) / 1.8);
   var y1 = parent1.offset().top + parent1.height();
   var x2 = child.offset().left + (child.width()/2.6);
   var y2 = child.offset().top;
   line.attr("d", "M " + x1 + "," + y1 + " L " + x1 + "," + (y2 + (y1 - y2) / 3) + " " + x2 + ","
   + (y2 + (y1 - y2) / 3) + " " + x2 + "," + y2);
   line.attr("position", "absolute");
}


// Draws the connections between couples, parents-children, sibilings - in case their parents are not in the tree
function connections(couples, genetic) {

       // First, connect parents with children. We need to call drawPathChild function with the following input:
       // parents' ids, child's id and id of the line - required graphic element. The new line is created dynamically
       // for each connection with "line" class and unique id (we'll also need it later for resizing)
       for (var i in genetic) {
           if (genetic[i]["parents"].length == 1) {
               var parent1 = $('#' + genetic[i]["parents"][0].split(' ').join('') );
               for (var j in genetic[i]["children"]) {
                   var child = $('#' + genetic[i]["children"][j].split(' ').join(''));
                   var line_id = (genetic[i]["parents"][0] + genetic[i]["children"][j]).split(' ').join('');
                   document.getElementsByClassName('svg')[0].innerHTML += "<path class='line' id='" +
                   line_id + "' d=''/>";
                   var line = $('.line:last');
                   var x = drawPathChild(line, parent1, parent1, child);
               }
           }
           else {
               var parent1 = $('#' + genetic[i]["parents"][0].split(' ').join(''));
               var parent2 = $('#' + genetic[i]["parents"][1].split(' ').join(''));
               for (var j in genetic[i]["children"]) {
                   var child = $('#' + genetic[i]["children"][j].split(' ').join('') );
                   var line_id = (genetic[i]["parents"][0] + genetic[i]["children"][j]).split(' ').join('');
                   document.getElementsByClassName('svg')[0].innerHTML += "<path class='line' id='" +
                   line_id + "' d=''/>";
                   var line = $('.line:last');
                   var x = drawPathChild(line, parent1, parent2, child);
               }
           }
       }

       // Then connect couples. The same approach: we need to call drawPath function for each couple. The input for the functions is:
       // line's id (we create new line dynamically for each couple) and ids of each member of the couple
       for (var i in couples) {
           var div1 = $('#' + couples[i]["couple"][0].split(' ').join(''));
           var div2 = $('#' + couples[i]["couple"][1].split(' ').join(''));
           var line_id = (couples[i]["couple"][0] + couples[i]["couple"][1]).split(' ').join('');
           document.getElementsByClassName('svg')[0].innerHTML += "<path class='line' id='" +
           line_id + "' d=''/>";
           var line = $('.line:last');
           var x = drawPath(line, div1, div2);
       }
}

// Calling the function by creating the 'connect' variable
var connect = connections(couples, genetic);

// Handling the window resizing: we call drawing functions for each type of relationships. The functions' input is:
// line's id and ids of all the elements that have to be connected
function resizing(couples, genetic) {
    for (var i in couples) {
        var line = (couples[i]["couple"][0] + couples[i]["couple"][1]).split(' ').join('');
        drawPath( $('#' + line), $('#' + couples[i]["couple"][0].split(' ').join('')),
        $('#' + couples[i]["couple"][1].split(' ').join('')) );
    }

    for (var i in genetic) {
         if (genetic[i]["parents"].length == 1) {
             for (var j in genetic[i]["children"]) {
                  var line = (genetic[i]["parents"][0] + genetic[i]["children"][j]).split(' ').join('');
                  drawPathChild( $('#' + line),
                  $('#' + genetic[i]["parents"][0].split(' ').join('')),
                  $('#' + genetic[i]["parents"][0].split(' ').join('')),
                  $('#' + genetic[i]["children"][j].split(' ').join('')) );
             }
         }
         else {
             for (var j in genetic[i]["children"]) {
                  var line = (genetic[i]["parents"][0] + genetic[i]["children"][j]).split(' ').join('');
                  drawPathChild( $('#' + line), $('#' + genetic[i]["parents"][0].split(' ').join('')),
                  $('#' + genetic[i]["parents"][1].split(' ').join('')),
                  $('#' + genetic[i]["children"][j].split(' ').join('')) );
             }
         }
    }
}

// The resizing function will be called every time window is resized
$(window).resize(function() {resizing(couples, genetic)});

// The first changes inner html of the undefined parents
// The second line will add undefined class to those parents
// Finally, the last line turns off the onclick event from undefined parents
$('[id^="1"].person').html("Undefined parent");
$('[id^="1"].person').addClass("undefined");
$( ".undefined" ).off();





