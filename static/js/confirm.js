const overlay_bg = document.getElementById('overlay');
let overlay_dialog = document.getElementById('overlay-dialog');
const overlay_flex = document.getElementById('overlay-flex');

let username = "";
let uid = 0;

function delete_confirm(btn) {
    overlay_bg.classList.remove('hidden');
    overlay_flex.classList.remove('hidden');
    let row = btn.parentNode.parentNode;
    username = row.getElementsByTagName('td')[0].innerText;
    uid = parseInt(row.id.slice(2));
    console.log(uid);
    document.getElementById('confirm-text').innerText = `Opravdu chcete smazat uživatele ${username}?`;
}

function delete_send(btn) {
    let xhr = new XMLHttpRequest();
    xhr.open("POST", `/user/${uid}/delete`);
    xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    xhr.onreadystatechange = () => {
        if(xhr.readyState == XMLHttpRequest.DONE && xhr.status == 200) {
            console.log('XHR finished');
            overlay_dialog.innerHTML = `Uživatel ${username} smazán.`;
            /*document.getElementById('confirm-text').innerText = ;
            document.getElementById('confirm-buttons').classList.add('hidden');*/
            window.setTimeout(() => {
                hide_overlay();
                window.location.reload();
            }, 2000);
        }
    }
    console.log('sending xhr...');
    xhr.send(null);
}

function hide_overlay() {
    overlay_bg.classList.add('hidden');
    overlay_flex.classList.add('hidden');
    overlay_dialog.innerHTML = '<h2 class="mb-2 text-xl font-semibold">Potvrzení</h2><p id="confirm-text" class="mb-4"></p><div id="confirm-buttons" class="flex flex-row justify-center w-full"><a class="mx-auto bg-green-500 w-36 btn-rounded hover:bg-green-400" onclick="delete_send(this);">Ano</a><a class="mx-auto bg-red-500 w-36 btn-rounded hover:bg-red-400" onclick="hide_overlay();">Ne</a></div>'
}