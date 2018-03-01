function openEditDiv(identifier) {
    $('#edit_div_' + identifier).toggleClass('show');
    $('#opac_div').toggle();
    $('#opac_div').click(function() {closeEditDiv(identifier);});
    $(document).keyup(function(e){
        if(e.which == 27){
            closeEditDiv(identifier);
        }
    });
}

function closeEditDiv(identifier) {
    $('#edit_div_' + identifier).toggleClass('show');
    $('#opac_div').toggle();
    $('#opac_div').off("click");
    $(document).off("keyup");
}

function toggleClassWithTimeout(elm, classname) {
    elm.toggleClass(classname);
    window.setTimeout(function() {
        elm.toggleClass(classname);
    }, 1000);
}
