const overlay_bg = document.getElementById('overlay');
let overlay_dialog = document.getElementById('overlay-dialog');
const overlay_flex = document.getElementById('overlay-flex');

let article = "";
let aid = 0;

function delete_confirm(btn) {
    overlay_bg.classList.remove('hidden');
    overlay_flex.classList.remove('hidden');
    let row = btn.parentNode.parentNode;
    article = row.getElementsByTagName('td')[0].innerText;
    aid = parseInt(row.id.slice(2));
    document.getElementById('confirm-text').innerText = `Opravdu chcete smazat článek ${article}?`;
}

function delete_send(btn) {
    let xhr = new XMLHttpRequest();
    xhr.open("POST", `/article/${aid}/delete`);
    xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    xhr.onreadystatechange = () => {
        if(xhr.readyState == XMLHttpRequest.DONE && xhr.status == 200) {
            console.log('XHR finished');
            overlay_dialog.innerHTML = `Článek ${article} smazán.`;
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
    overlay_dialog.innerHTML = '<h2 class="mb-2 text-xl font-semibold">Potvrzení</h2><p id="confirm-text" class="mb-4"></p><div id="confirm-buttons" class="flex flex-row justify-center w-full"><a class="mx-1 bg-green-600 w-36 btn-rounded hover:bg-green-500" onclick="delete_send(this);">Ano</a><a class="mx-1 bg-red-600 w-36 btn-rounded hover:bg-red-500" onclick="hide_overlay();">Ne</a> </div>'
}