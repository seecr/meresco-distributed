/* begin license *
 *
 * "Meresco Distributed" has components for group management based on "Meresco Components."
 *
 * Copyright (C) 2018 Seecr (Seek You Too B.V.) http://seecr.nl
 *
 * This file is part of "Meresco Distributed"
 *
 * "Meresco Distributed" is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * "Meresco Distributed" is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with "Meresco Distributed"; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 *
 * end license */

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
