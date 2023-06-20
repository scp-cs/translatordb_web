const reg_scp = /^(SCP-)?\d{3,4}(-J|-EX|-CS)?$/iu;
const link = document.getElementById('input-link');
const titlebox = document.getElementById('input-title');

let user_changed = false;


function title_update(event) {
    let title = event.target.value;
        if(reg_scp.test(title)) {
            link.value = 'https://scp-cs.wikidot.com/'+title.toLowerCase();
        } else {
            console.log('clear');
            link.value = "";
        }
}

titlebox.addEventListener("input", title_update);
link.addEventListener('input', () => {titlebox.removeEventListener('input', title_update);})