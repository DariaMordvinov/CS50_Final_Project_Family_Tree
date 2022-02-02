function CurrentDate() {
    n =  new Date();
    y = n.getFullYear();
    m = n.getMonth() + 1;
    d = n.getDate();
    return y + "-" + "m" + "-" + "d";
}

function redirect() {
    window.top.location.href = "/my_tree";
}