# CS50 Final Project: Family Tree

#### Video Demo:  https://youtu.be/bj0dWR8iX2M
#### "Family Tree" is a Flask application for creating your own family tree. 

This is my final project for the CS50x studying course. To create this project I used Python, Java Script, HTML, CSS, Jinja and JQuery. It also uses SQL database.
This is a Flask application that allows users to create their own family trees. User can register on the website, login
and logout, add his relatives to the tree, delete relatives, add photos and description to relatives' profiles. User can 
also delete his/her own account. On the "my_tree" page user can see visualised version of his family connections.

**Database**

For this project I created 4 initial tables: users, people, people_photos and people_stories. People table contains information
on all people, added to the data base: users and their relatives included. 

People table has 5 columns: id (primary key), name, birth, death, related_to. In related_to column we save user's id. By default 
there is one row in people table: undefined person with id == 1. I use him in connection tables to express lack of connection
(for example: person has no parents or only 1 parent).

When user is registered app inserts him in the peoples' table first and then saves him in the users' table with the id, assigned 
to him in the peoples' table. In people_photos there are 2 columns: name of the image and id of a person. When user adds a picture
to the person's profile, app will save its name in the data base and then save the image in the files. If we already have 
the image with the exact same name, the app will add randomized letters until the name becomes unique.

**Database: connections between relatives**

To maintain all kinds of relationships in the family tree I came up with the following approach. Every time new user registers,
a new table is created in the database with the name of the user's id. In this table I maintain all the information about family 
connections.

The connection tables have 5 columns: child_generation, parent_1, parent_2, child, sib_group. To be clear, my application doesn't allow 
more than 2 parents at once, this is the problem to be addressed in the future.
By default user has generation == 100. So everyone from the generation above would have higher numbers and vice versa. 
User's father has generation equal to 101, grandfather's to 102 and so on. Sib_group - is "sibling group", equals to id 
of the first child, added to this family. I need this id to figure out siblings, that do not have parents.

*Example*

1) We registered new user the id == 2. First row in his connection table will look like that:<br />
**generation_id: 100<br />
parent_1: 1<br />
parent_2: 1<br />
child: 2<br />
sib_group: 2<br />**
2) We added his mother with the id == 3. Row changed to:<br />
**generation_id: 100<br />
parent_1: 3<br />
parent_2: 1<br />
child: 2<br />
sib_group: 2<br />**
3) We added his brother with id == 4. There will be another row:<br />
**generation_id: 100<br />
parent_1: 3<br />
parent_2: 1<br />
child: 4<br />
sib_group: 2<br />**
Note that his brother would be in the same generation and sibling group. 
4) Now, if we add father == 5, both rows will change to:
**generation_id: 100<br />
parent_1: 3<br />
parent_2: 5<br />
child: 2<br />
sib_group: 2<br />**<br />
**generation_id: 100<br />
parent_1: 3<br />
parent_2: 5<br />
child: 4<br />
sib_group: 2<br />**


**Application's limitations**

This is my first studying project, so there are some limitations in my app. I hope I'll be able to solve some of these 
problems in the future.

- User can add only those people, with whom he has "blood by blood" connection. For example:
I can add both of my parents and all of their relatives. But if I add my spouse, I can't add his relatives as well: they 
would not be considered as my relatives.

- Application probably wouldn't handle too many relatives too well. Errors in visualization of the tree may occur if there
will be more than 15 people in one generation.

- User can't add more than 2 parents to the tree. For instance his step-mother.

- While adding a new person to the tree, the program figures out the connections for the user. For instance: we have a 
family of 3 people - David (father), Anna (mother) and Sam (son). If we try to add another person as Sam's brother, app
will make David and Anna this new person's parents too. He can't have Anna as a mother and some other man as a dad.

- **The application is not suitable for mobile use.**

**Some of the challenges I faced**

The most complicated task for me was visualization of the family tree. I wanted to make it possible for the app to arrange 
data on people relatively neatly on the page. You'll find most of the visualization-related code in helper.py file and tree.js file.

When "drawing" a tree, app takes these steps:

1) in Python: Reads information on user's relatives from the database and arrange it in several dictionaries to express parent-child 
and partner-partner relationships.

2) in Python: Makes "generation" dictionary where keys will be in the range from 1 to the number of presented generations.
Values - all the relatives from this specific generation. At this point I get rid of "100" type generation. Example: 
{1: grandparents; 2: parents; 3: children}

3) in Python: Now rearranges values in the generation dictionary. To make it easy to draw the tree later, we have to put relatives 
in the correct order: spouses together, their sibling not too far, etc. To do that I find the "middle" of the tree first
(check tree_middle function in helpers.py) and then arrange people from there, each time dividing them in two groups.

4) Transfers dictionaries with Jinja.

5) in JS: puts every person on the page: each row - one generation. Attaches onclick events to each person - so we could 
open profile pages.

6) in JS: draws connections between relatives. I used html svg element and added paths to it. App uses people's coordinates
on the page to draw lines. This was the most challenging problem for me to deal with.

7) in JS: Adds resizing. Every time window resizes, lines are rearranged on the page.

8) in JS: Renames undefined parents to "undefined" if there is any and turns off onclick event from their boxes.

**Files**

Project has the following structure:

- *Project*
  - *static*
     - all css files
     - all java script files
     - *files* (folder for images)
  - *templates*
     - all html files
     - *public*
       - profile.html
  - application.py (the main Python code for the web server) <br />
  - helpers.py (some functions) <br />
  - family_tree.db (data base)
  - README.md


Thank you for reading this, Daria Mordvinov.
