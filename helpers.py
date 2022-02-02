from functools import wraps
from flask import redirect, render_template, session
from cs50 import SQL

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///family_tree.db")


# Wrapping function
def login_required(f):
    """
    Decorate routes to require login.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/sign_in")
        return f(*args, **kwargs)
    return decorated_function


# Checks if a file with the given name already exist in our uploader folder
def filename_check(filename):
    files = db.execute("SELECT photo FROM people_photos")
    for row in files:
        if row["photo"] == filename:
            return True


def born_check(name):
    if name.find(" born ") != -1:
        birth = name[name.find(" born") + 6:]
        word = name[:name.find(" born")]
        name = word + " " + "add" + birth.replace("-", "") + "add"
    return name


def add_check(name, person_id):
    if name.find(" add") != -1:
        birth = db.execute("SELECT birth FROM people WHERE id = ?", person_id)[0]["birth"]
        name = name[:name.find(" add")] + " born " + birth
    return name


# Check all the variables on a person from the tree and return templates accordingly
def profile_back(person, person_birth, person_death, text, photos):
    if person_death is None:
        if text is None:
            if len(photos) == 0:
                return render_template("public/profile.html", person=person, birth=person_birth)
            else:
                return render_template("public/profile.html", person=person, birth=person_birth, photos=photos)
        else:
            if len(photos) == 0:
                return render_template("public/profile.html", person=person, birth=person_birth, text=text)
            else:
                return render_template("public/profile.html", person=person, birth=person_birth,
                                       text=text, photos=photos)
    else:
        if text is None:
            if len(photos) == 0:
                return render_template("public/profile.html", person=person, birth=person_birth, death=person_death)
            else:
                return render_template("public/profile.html", person=person, birth=person_birth, death=person_death,
                                       photos=photos)
        else:
            if len(photos) == 0:
                return render_template("public/profile.html", person=person, birth=person_birth, death=person_death,
                                       text=text)
            else:
                return render_template("public/profile.html", person=person, birth=person_birth, death=person_death,
                                       text=text, photos=photos)


# Check all the variables on a new person and returns template accordingly
def approval_list(name, birth, death, children, parents, siblings, partner, connection):
    if death is None:
        if connection["type"] == "parent" or connection["type"] == "spouse/partner":
            if len(children) == 0:
                return render_template("approval.html", name=name, birth=birth, partner=partner)
            else:
                if partner is None:
                    return render_template("approval.html", name=name, birth=birth, children=children)
                else:
                    return render_template("approval.html", name=name, birth=birth, children=children, partner=partner)
        else:
            if len(parents) == 0:
                return render_template("approval.html", name=name, birth=birth, siblings=siblings)
            else:
                if len(siblings) == 0:
                    return render_template("approval.html", name=name, birth=birth, parents=parents)
                else:
                    return render_template("approval.html", name=name, birth=birth, parents=parents, siblings=siblings)
    else:
        if connection["type"] == "parent" or connection["type"] == "spouse/partner":
            if len(children) == 0:
                return render_template("approval.html", name=name, birth=birth, partner=partner)
            else:
                if partner is None:
                    return render_template("approval.html", name=name, birth=birth, death=death, children=children)
                else:
                    return render_template("approval.html", name=name, birth=birth, death=death, children=children,
                                           partner=partner)
        else:
            if len(parents) == 0:
                return render_template("approval.html", name=name, birth=birth, death=death, siblings=siblings)
            else:
                if len(siblings) == 0:
                    return render_template("approval.html", name=name, birth=birth, death=death, parents=parents)
                else:
                    return render_template("approval.html", name=name, birth=birth, parents=parents, death=death,
                                           siblings=siblings)


# Makes a nice date
def date_maker(date):
    year = date[:4]
    month = int(date[5:7]) - 1
    day = str(int(date[8:]))
    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
              "November", "December"]
    date = day + " " + months[month] + ", " + year
    return date


def extract_name(name):
    clean_name = ""
    clean_name += name[0]
    for i in name[1:]:
        if i.isupper():
            clean_name += " "
        clean_name += i

    if clean_name.find("add") != -1:
        clean_name = clean_name[:clean_name.index("add")] + " " + clean_name[clean_name.index("add"):]

    return clean_name


# Finds id by the given name
def find_id(name):
    person_id = db.execute("SELECT id FROM people WHERE name = ? AND related_to = ?", name, session["user_id"])[0]["id"]
    return person_id


# Checks what kind of connections we need to update in our data base
def update_connections(connection, id, children, parents, siblings, partner, table_name):

    # With these types of connection we need to look at possible children and possible partner
    if connection["type"] == "parent" or connection["type"] == "spouse/partner":

        # If there is no children, we need to update only partner
        if len(children) == 0:

            partner = born_check(partner)
            partner_id = find_id(partner)
            # If partner and person don't have any children, partner would not exist in the table as a parent.
            # He/she only exist as a child
            generation = db.execute("SELECT child_generation FROM ? WHERE child = ?",
                                    table_name, partner_id)[0]["child_generation"] - 1
            db.execute("INSERT INTO ? (child_generation, parent_1, parent_2, child, sib_group) VALUES (?, ?, ?, ?, ?)",
                    table_name, generation, id, partner_id, 1, 1)

        # We know who the children are
        else:
            # If there is no partner, we need to update parent for every child
            if partner is None:
                if len(children) == 1:
                    child = children[0]
                    child = born_check(child)
                    child_id = find_id(child)
                    if db.execute("SELECT * FROM ? WHERE child = ?", table_name, child_id):
                        db.execute("UPDATE ? SET parent_1 = ? WHERE child = ?", table_name, id, child_id)
                    else:
                        generation = db.execute("SELECT child_generation FROM ? WHERE parent_1 = ? OR parent_2 = ?",
                                                table_name, child_id, child_id)[0]["child_generation"] + 1
                        sib_group = child_id
                        db.execute(
                            "INSERT INTO ? (child_generation, parent_1, parent_2, child, sib_group) VALUES (?, ?, ?, ?, ?)",
                            table_name, generation, id, 1, child_id, sib_group)
                else:
                    for i in children:
                        child = i
                        child = born_check(child)
                        child_id = find_id(child)
                        db.execute("UPDATE ? SET parent_1 = ? WHERE child = ?", table_name, id, child_id)

            else:
                partner = born_check(partner)
                partner_id = find_id(partner)
                # We need to update both: partner and children
                for i in children:
                    child = i
                    child = born_check(child)
                    child_id = find_id(child)
                    db.execute("UPDATE ? SET parent_1 = ?, parent_2 = ? WHERE child = ?", table_name, id, partner_id,
                               child_id)

    # And if connection type == child or sibling
    else:

        # If we need to update only sibling
        if len(parents) == 0:
            sib = siblings[0]
            sib = born_check(sib)
            sib_id = find_id(sib)
            # If a sibling exist in table as a child
            if db.execute("SELECT * FROM ? WHERE child = ?", table_name, sib_id):
                generation = db.execute("SELECT child_generation FROM ? WHERE child = ?", table_name,
                                        sib_id)[0]["child_generation"]
                sib_group = db.execute("SELECT sib_group FROM ? WHERE child = ?", table_name,
                                       sib_id)[0]["sib_group"]
            # If a sibling exist as someone's parent
            else:
                generation = db.execute("SELECT child_generation FROM ? WHERE parent_1 = ? OR parent_2 = ?", table_name,
                                        sib_id, sib_id)[0]["child_generation"] + 1
                sib_group = sib_id
                db.execute("INSERT INTO ? (child_generation, parent_1, parent_2, child, sib_group) VALUES (?, ?, ?, ?, ?)",
                           table_name, generation, 1, 1, sib_id, sib_group)

            # Insert row into the table with final values
            db.execute(
                    "INSERT INTO ? (child_generation, parent_1, parent_2, child, sib_group) VALUES (?, ?, ?, ?, ?)",
                    table_name, generation, 1, 1, id, sib_group)

        # If we know the parents
        else:
            parent1 = parents[0]
            parent1 = born_check(parent1)
            parent1_id = find_id(parent1)
            if len(parents) == 2:
                parent2 = parents[1]
                parent2 = born_check(parent2)
                parent2_id = find_id(parent2)
            else:
                parent2_id = 1

            # If we need to update both: parents and siblings
            if len(siblings) != 0:
                sib_group = db.execute("SELECT sib_group FROM ? WHERE parent_1 = ? OR parent_2 = ?",
                                  table_name, parent1_id, parent1_id)[0]["sib_group"]
                generation = db.execute("SELECT child_generation FROM ? WHERE parent_1 = ? OR parent_2 = ?", table_name,
                                        parent1_id, parent1_id)[0]["child_generation"]
                db.execute(
                    "INSERT INTO ? (child_generation, parent_1, parent_2, child, sib_group) VALUES (?, ?, ?, ?, ?)",
                    table_name, generation, parent1_id, parent2_id, id, sib_group)

            # If we need to update only parents
            else:
                if db.execute("SELECT * FROM ? WHERE parent_1 = ? OR parent_2 = ?", table_name, parent1_id, parent1_id):
                    sib_group = id
                    db.execute("UPDATE ? SET child = ?, sib_group = ? WHERE parent_1 = ? OR parent_2 = ?",
                               table_name, id, sib_group, parent1_id, parent1_id)
                else:
                    # If a parent exist in a table as someone's child
                    generation = db.execute("SELECT child_generation FROM ? WHERE child = ?", table_name,
                                            parent1_id)[0]["child_generation"] - 1
                    sib_group = id
                    db.execute(
                        "INSERT INTO ? (child_generation, parent_1, parent_2, child, sib_group) VALUES (?, ?, ?, ?, ?)",
                        table_name, generation, parent1_id, parent2_id, id, sib_group)
    return None


# If connection is parent, this function will return new person's children and partner
def connection_parent(children, partner, table_name, relative_id):

    # Check for the spouse/partner
    parent_1 = db.execute("SELECT parent_1 FROM ? WHERE child = ?", table_name, relative_id)
    if parent_1:
        partner_id = parent_1[0]["parent_1"]
        if partner_id != 1:
            partner = db.execute("SELECT name FROM people WHERE id = ?", partner_id)[0]["name"]
            partner = add_check(partner, partner_id)
        else:
            partner_id = db.execute("SELECT parent_2 FROM ? WHERE child = ?",
                                    table_name, relative_id, )[0]["parent_2"]
            if partner_id != 1:
                partner = db.execute("SELECT name FROM people WHERE id = ?", partner_id)[0]["name"]
                partner = add_check(partner, partner_id)

    if db.execute("SELECT sib_group FROM ? WHERE child = ?", table_name, relative_id):
        sib_group = db.execute("SELECT sib_group FROM ? WHERE child = ?", table_name, relative_id)[0]["sib_group"]
        if sib_group != 1:
            children_ids = set()
            rows = db.execute("SELECT child FROM ? WHERE sib_group = ?", table_name, sib_group)
            for i in rows:
                children_ids.add(i["child"])

            children_ids.discard(1)
            children_ids.discard(relative_id)

            # Check that there is still children in the set
            if len(children_ids) != 0:
                for i in children_ids:
                    child = db.execute("SELECT name FROM people WHERE id = ?", i)[0]["name"]
                    child = add_check(child, i)
                    children.append(child)

    return {"children": children, "partner": partner}


# If connection is child this function will return parents and siblings
def connection_child(parents, siblings, table_name, relative_id):

    # Check for the other parent
    if db.execute("SELECT parent_1 FROM ? WHERE parent_2 = ?", table_name, relative_id) and \
            db.execute("SELECT parent_1 FROM ? WHERE parent_2 = ?", table_name, relative_id)[0]["parent_1"] != 1:
        parent_2 = db.execute("SELECT parent_1 FROM ? WHERE parent_2 = ?", table_name, relative_id)[0]["parent_1"]
        parent_2Name = db.execute("SELECT name FROM people WHERE id = ?", parent_2)[0]["name"]
        parent_2Name = add_check(parent_2Name, parent_2)
        parents.append(parent_2Name)
    else:
        if db.execute("SELECT parent_2 FROM ? WHERE parent_1 = ?", table_name, relative_id) and \
                db.execute("SELECT parent_2 FROM ? WHERE parent_1 = ?", table_name, relative_id)[0]["parent_2"] != 1:
            parent_2 = db.execute("SELECT parent_2 FROM ? WHERE parent_1 = ?", table_name, relative_id)[0]["parent_2"]
            parent_2Name = db.execute("SELECT name FROM people WHERE id = ?", parent_2)[0]["name"]
            parent_2Name = add_check(parent_2Name, parent_2)
            parents.append(parent_2Name)

    # Check for siblings
    if db.execute("SELECT child FROM ? WHERE parent_1 = ? OR parent_2 = ?", table_name, relative_id, relative_id):
        sibling_ids = set()
        rows = db.execute("SELECT child FROM ? WHERE parent_1 = ? OR parent_2 = ?", table_name, relative_id,
                          relative_id)
        for i in rows:
            sibling_ids.add(i["child"])

        sibling_ids.discard(1)
        if len(sibling_ids) != 0:
            for i in sibling_ids:
                sib = db.execute("SELECT name FROM people WHERE id = ?", i)[0]["name"]
                sib = add_check(sib, i)
                siblings.append(sib)

    return {"parents": parents, "siblings": siblings}


# If connection is spouse/partner, this function will return spouse and children
def connection_spouse(partner, children, table_name, relative_id):

    # Check for children - if a partner already has children in a tree,
    # new person will automatically become their parent too
    child = db.execute("SELECT child FROM ? WHERE parent_1 = ? OR parent_2 = ?", table_name, relative_id, relative_id)
    if child:
        children_ids = set()
        rows = child
        for i in rows:
            children_ids.add(i["child"])
        children_ids.discard(1)

        # Check that there is still children in the set
        if len(children_ids) != 0:
            for i in children_ids:
                child = db.execute("SELECT name FROM people WHERE id = ?", i)[0]["name"]
                child = add_check(child, i)
                children.append(child)

    return {"spouse": partner, "children": children}


# If connection is sibling, this function will return parents and siblings
def connection_sibling(siblings, parents, table_name, relative_id):

    if db.execute("SELECT * FROM ? WHERE child = ?", table_name, relative_id):
        sib_group = db.execute("SELECT sib_group FROM ? WHERE child = ?", table_name, relative_id)[0]["sib_group"]
        parent_1 = db.execute("SELECT parent_1 FROM ? WHERE child = ?", table_name, relative_id)[0]["parent_1"]

        if parent_1 != 1:
            parent_1Name = db.execute("SELECT name FROM people WHERE id = ?", parent_1)[0]["name"]
            parent_1Name = add_check(parent_1Name, parent_1)
            parents.append(parent_1Name)

            parent_2 = db.execute("SELECT parent_2 FROM ? WHERE child = ?", table_name, relative_id)[0]["parent_2"]
            if parent_2 != 1:
                parent_2Name = db.execute("SELECT name FROM people WHERE id = ?", parent_2)[0]["name"]
                parent_2Name = add_check(parent_2Name, parent_2)
                parents.append(parent_2Name)
        else:
            parent_2 = db.execute("SELECT parent_2 FROM ? WHERE child = ?", table_name, relative_id)[0]["parent_2"]
            if parent_2 != 1:
                parent_2Name = db.execute("SELECT name FROM people WHERE id = ?", parent_2)[0]["name"]
                parent_2Name = add_check(parent_2Name, parent_2)
                parents.append(parent_2Name)

        if sib_group != 1:
            rows = db.execute("SELECT child FROM ? WHERE sib_group = ?", table_name, sib_group)
            sib_ids = set()
            for i in rows:
                sib_ids.add(i["child"])

            sib_ids.discard(1)
            sib_ids.discard(relative_id)
            if len(sib_ids) != 0:
                for i in sib_ids:
                    sib = db.execute("SELECT name FROM people WHERE id = ?", i)[0]["name"]
                    sib = add_check(sib, i)
                    siblings.append(sib)

    return {"siblings": siblings, "parents": parents}


# Makes a list of all couples in user's family tree
def couples(table_name, user_id):
    couple_ids = []
    rows = db.execute("SELECT parent_1, parent_2 FROM ? WHERE parent_1 != ? AND parent_2 != ?", table_name, 1, 1)
    for i in rows:
        if [i["parent_1"], i["parent_2"]] not in couple_ids:
            couple_ids.append([i["parent_1"], i["parent_2"]])

    couples = []
    for i in couple_ids:
        couple = []
        for j in i:
            name = db.execute("SELECT name FROM people WHERE id = ? AND related_to = ?", j, user_id)[0]["name"]
            couple.append(name)
        couples.append({"couple": couple})
    return couples


# Make a list of all families (parents-children) from user's family tree
def genetic(table_name, user_id):
    genetic_ids = db.execute(
        "SELECT parent_1, parent_2, child FROM ? WHERE child != 1 AND (parent_1 != 1 OR parent_2 != 1)",
        table_name)

    all_parents = []
    genetic = []

    for i in genetic_ids:
        parents = []
        if i["parent_1"] != 1:
            parents.append(
                db.execute("SELECT name FROM people WHERE id = ? AND related_to = ?", i["parent_1"], user_id)[0][
                    "name"])
        if i["parent_2"] != 1:
            parents.append(
                db.execute("SELECT name FROM people WHERE id = ? AND related_to = ?", i["parent_2"], user_id)[0][
                    "name"])

        if parents not in all_parents:
            all_parents.append(parents)
            child = db.execute("SELECT name FROM people WHERE id = ? AND related_to = ?", i["child"], user_id)[0][
                "name"]
            genetic.append({"parents": parents, "children": [child, ]})
        else:
            for j in genetic:
                if j["parents"] == parents:
                    j["children"].append(
                        db.execute("SELECT name FROM people WHERE id = ? AND related_to = ?", i["child"], user_id)[0][
                            "name"])
                    break

    siblings = []
    sib_groups = {}
    sib_ids = db.execute("SELECT sib_group, child FROM ? WHERE child != 1 AND parent_1 == 1 AND parent_2 == 1",
                         table_name)

    for i in sib_ids:
        child = db.execute("SELECT name FROM people WHERE id = ? AND related_to = ?", i["child"], user_id)[0]["name"]
        if i["sib_group"] in sib_groups:
            sib_groups[i["sib_group"]].append(child)
        else:
            sib_groups[i["sib_group"]] = [child, ]

    for j in sib_groups:
        if len(sib_groups[j]) > 1:
            siblings.append(sib_groups[j])

    for i in siblings:
        parent_name = str(1) + i[0]
        genetic.append({"parents": [parent_name, ], "children": i})

    return genetic


# Defines the middle of the tree (user's parents' generation)
def tree_middle(generations, genetic, couples, user_name):
    start = []
    start_line = []

    for family in genetic:
        if user_name in family["children"]:
            start = family["parents"]

    if len(start) == 0:
        for i in generations:
            if user_name in generations[i]:
                number = i
                for person in generations[i]:
                    if person not in start_line:
                        start_line.append(person)

                        partner = check_couple(person, couples, start_line)
                        if partner is not None:
                            start_line.append(partner)
                            for family in genetic:
                                if partner in family["children"]:
                                    for child in family["children"]:
                                        if child not in start_line:
                                            start_line.append(child)

                        for family in genetic:
                            if person in family["children"]:
                                for child in family["children"]:
                                    if child not in start_line:
                                        start_line.insert([start_line.index(person), child])
                                        partner = check_couple(child, couples, start_line)
                                        if partner is not None:
                                          start_line.insert([start_line.index(child), partner])

    else:
        for i in generations:
            if start[0] in generations[i]:
                number = i

        parent_left = start[0]
        if len(start) > 1:
            parent_right = start[1]
        else:
            parent_right = None

        left_sibs = []
        right_sibs = []

        for family in genetic:
            if parent_left in family["children"]:
                for i in family["children"]:
                    left_sibs.append(i)
            elif parent_right is not None and parent_right in family["children"]:
                for i in family["children"]:
                    right_sibs.append(i)

        if parent_left in left_sibs:
            left_sibs.remove(parent_left)
        if len(right_sibs) > 0 and parent_right in right_sibs:
            right_sibs.remove(parent_right)

        start_line.append(parent_left)
        if parent_right is not None:
            start_line.append(parent_right)
            for i in right_sibs:
                x = 0
                for j in couples:
                    if i in j["couple"] and i not in start_line:
                        start_line.append(i)
                        x += 1
                        if i == j["couple"][0]:
                            start_line.append(j["couple"][1])
                        else:
                            start_line.append(j["couple"][0])
                if x == 0:
                    start_line.append(i)

        for i in left_sibs:
            for j in couples:
                if i in j["couple"] and i not in start_line:
                    if i == j["couple"][0]:
                        start_line.insert(0, j["couple"][1])
                    else:
                        start_line.insert(0, j["couple"][0])
            start_line.insert(0, i)

    for i in generations:
        if i == number:
            line = generations[i]

    if len(line) != len(start_line):
        for person in line:
            if person not in start_line:
                start_line.append(person)

            partner = check_couple(person, couples, start_line)
            if partner is not None:
                start_line.append(partner)

            sibs = check_sibs(person, genetic, start_line)
            for sib in sibs:
                start_line.insert(start_line.index(person), sib)
                partner = check_couple(sib, couples, start_line)
                if partner is not None:
                    start_line.insert(start_line.index(sib), partner)

    return {number: start_line}


# Check for siblings on the person
def check_sibs(person, genetic, line):
    siblings = []
    for family in genetic:
        if person in family["children"]:
            for sib in family["children"]:
                if sib not in line:
                    siblings.append(sib)
    return siblings


# Checks if a person has a partner
def check_couple(person, couples, line):
    partner = None
    for c in couples:
        if person in c["couple"]:
            if person == c["couple"][0]:
                partner = c["couple"][1]
            else:
                partner = c["couple"][0]
    if partner not in line:
        return partner
    else:
        return None


# Arranges relatives in the generation lines above the middle of the tree in the correct order
def arrangeLineAbove(line_below, genetic, couples):
    next_line = []
    # Let's go through the children in the line below and find their parents
    for i in range(len(line_below)):
        child = line_below[i]
        for family in genetic:
            if child in family["children"]:
                parents = []
                for parent in family["parents"]:
                    if parent not in next_line:
                        parents.append(parent)

                if len(parents) == 1:
                    next_line.append(parents[0])
                    sibs = check_sibs(parents[0], genetic, next_line)
                    for sib in sibs:
                        next_line.append(sib)
                        partner = check_couple(sib, couples, next_line)
                        if partner is not None:
                            next_line.insert(next_line.index(sib) + 1, partner)
                elif len(parents) > 1:
                    left_parent = parents[0]
                    right_parent = parents[1]
                    next_line.append(left_parent)
                    next_line.append(right_parent)
                    left_sibs = check_sibs(left_parent, genetic, next_line)
                    right_sibs = check_sibs(right_parent, genetic, next_line)
                    for sib in left_sibs:
                        x = 0
                        for group in genetic:
                            if sib in group["parents"]:
                                x += 1
                        if x == 0:
                            next_line.insert(next_line.index(left_parent), sib)
                            partner = check_couple(sib, couples, next_line)
                            if partner is not None:
                                next_line.insert(next_line.index(sib), partner)
                    for sib in right_sibs:
                        next_line.append(sib)
                        partner = check_couple(sib, couples, next_line)
                        if partner is not None:
                            next_line.append(partner)

    return next_line


# Arranges relatives in the generation lines below the middle of the tree in the correct order
def arrangeLineBelow(line_above, genetic, couples):
    next_line = []
    for person in line_above:
        for family in genetic:
            if person in family["parents"]:
                for child in family["children"]:
                    couple = []
                    if child not in next_line:
                        couple.append(child)
                    partner = check_couple(child, couples, next_line)
                    if partner is not None:
                        couple.append(partner)

                    if len(couple) == 1:
                        next_line.append(child)
                    elif len(couple) > 1:
                        left_person = child
                        right_person = partner
                        next_line.append(left_person)
                        next_line.append(right_person)
                        left_sibs = check_sibs(left_person, genetic, next_line)
                        right_sibs = check_sibs(right_person, genetic, next_line)
                        for sib in left_sibs:
                            next_line.insert(next_line.index(left_person), sib)
                            partner = check_couple(sib, couples, next_line)
                            if partner is not None:
                                next_line.insert(next_line.index(sib), partner)
                        for sib in right_sibs:
                            next_line.append(sib)
                            partner = check_couple(sib, couples, next_line)
                            if partner is not None:
                                next_line.append(partner)
    return next_line


# Organize all the relatives by generations
def generations(table_name, id, couples, genetic):
    relatives = []
    rows = db.execute("SELECT id FROM people WHERE related_to = ?", id)
    for i in rows:
        relatives.append(i["id"])

    generation_ids = dict()
    generations = dict()

    for i in relatives:
        if db.execute("SELECT * FROM ? WHERE child = ?", table_name, i):
            generation = db.execute("SELECT child_generation FROM ? WHERE child = ?", table_name, i)[0][
                "child_generation"]
            generation_ids.setdefault(generation, []).append(i)
        else:
            generation = db.execute("SELECT child_generation FROM ? WHERE parent_1 = ? OR parent_2 = ?",
                                    table_name, i, i)[0]["child_generation"] + 1
            generation_ids.setdefault(generation, []).append(i)

    x = len(generation_ids)
    y = x - 1

    for i in sorted(generation_ids.keys(), reverse=True):
        generation = []
        for j in generation_ids[i]:
            name = db.execute("SELECT name FROM people WHERE id = ? AND related_to = ?", j, id)[0]["name"]
            generation.append(name)
        generations[x - y] = generation
        y -= 1

    new_line = []
    for i in genetic:
        if i["parents"][0][0] == "1":
            child = i["children"][0]
            for j in generations:
                if child in generations[j]:
                    if j != 1:
                        generation = j - 1
                        generations[generation].append(i["parents"][0])
                    else:
                        new_line.append(i["parents"][0])

    if len(new_line) > 0:
        for k in sorted(generations.keys(), reverse=True):
            generations[k + 1] = generations[k]
            del generations[k]
        generations[1] = [i["parents"][0], ]

    # Now we have to rearrange relatives: every line has to begin with the same family, so parents would be
    # just above their children
    generations = arrange(generations, id, couples, genetic)
    return generations


# Arranges the whole tree
def arrange(generations, id, couples, genetic):
    arrangedGenerations = dict()

    user_name = db.execute("SELECT username FROM users WHERE id = ?", id)[0]["username"]

    # Find the middle of the tree
    start_line = tree_middle(generations, genetic, couples, user_name)
    for i in start_line:
        arrangedGenerations[i] = start_line[i]
        number = i

    # Now we arranged the starting point of the tree  - parents of the user.
    # We have to arrange all the lines above and all the lines below this pont

    # Let's rearrange lines above the starting line
    for i in range(number - 1, 0, -1):
        line_below = arrangedGenerations[i + 1]
        next_line = arrangeLineAbove(line_below, genetic, couples)
        arrangedGenerations[i] = next_line

    # Now to the lines below
    for i in range(number + 1, len(generations) + 1):
        line_above = arrangedGenerations[i - 1]
        next_line = arrangeLineBelow(line_above, genetic, couples)
        arrangedGenerations[i] = next_line

    final_generations = dict()
    x = len(generations)
    y = x - 1

    for i in sorted(arrangedGenerations.keys()):
        generation = []
        for j in arrangedGenerations[i]:
            generation.append(j)
        final_generations[x - y] = generation
        y -= 1

    return final_generations


def removable(user_id):
    families = genetic(str(user_id), user_id)
    pairs = couples(str(user_id), user_id)
    rows = db.execute("SELECT name FROM people WHERE related_to = ? AND id != ?", user_id, user_id)
    relatives = []
    for row in rows:
        relatives.append(row["name"])

    not_removable = set()

    for person in relatives:
        for family in families:
            if person in family["children"]:
                for pair in pairs:
                    if person in pair:
                        not_removable.add(person)
                for i in families:
                    if person in i["parents"]:
                        not_removable.add(person)

    for person in relatives:
        if person in not_removable:
            relatives.remove(person)

    for i in range(len(relatives)):
        if relatives[i].find(" add") != -1:
            relatives[i] = relatives[i][:relatives[i].find(" add")] + " born " + \
                           db.execute("SELECT birth FROM people WHERE name = ? AND related_to = ?",
                                      relatives[i], user_id)[0]["birth"]
    return relatives
