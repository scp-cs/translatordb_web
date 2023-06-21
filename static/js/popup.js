function displayPopup(id) {
    const popup = document.getElementById(id);
    popup.classList.add('animate-fadein')
    popup.style.display = 'flex';
    window.setTimeout(function(){
        popup.classList.remove('animate-fadein');
        popup.classList.add('animate-fadeout');
        window.setTimeout(function(){popup.style.display = 'none';}, 980)}, 5000);
}

const popups_html = document.getElementsByClassName('popup');
const popups = Array.from(popups_html);
if (popups.length > 0) {
    displayPopup('popup0');
    if (popups.length >= 1) {
        for(let i = 1; i < popups.length; i++) {
            let id = "popup" + i.toString();
            setTimeout(function(){displayPopup(id);}, 6000);
        }
    }
}

