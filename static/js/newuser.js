const ch_e = document.getElementById('check-exempt');
const ch_l = document.getElementById('check-login');

function updateExempt(c) {
    if(c.checked) {
        ch_e.innerHTML = 'Ano';
    } else {
        ch_e.innerHTML = 'Ne';
    }
}

function updateLogin(c) {
    if(c.checked) {
        ch_l.innerHTML = 'Ano';
    } else {
        ch_l.innerHTML = 'Ne';
    }
}