const ROLE_LIMITS = {
    5: 'Překladatel I',
    10: 'Překladatel II',
    25: 'Překladatel III',
    50: 'Překladatel IV',
    100: 'Překladatel V'
}

const ROLE_NONE = 'Žádná'

const table = document.getElementById('ut-body')
const originalHtml = table.innerHTML

let is_original = true
let timeoutID = 0

function get_role(point_count) {
    role = ROLE_NONE
    for(const [limit, text] of Object.entries(ROLE_LIMITS)) {
        if(limit > point_count) 
            return role
        role = text
    }
    return role
}

function make_row(u, has_auth) {
    const dscblock = u.discord ? `<img class="w-8 h-8 rounded-[50%] inline md:mr-4" src="/content/avatar/${u.discord}?s=thumb"> ${u.displayname ?? u.discord}` : u.displayname ?? u.discord
    let btnblock = `<a class="inline-block w-full mb-2 md:inline md:w-auto md:mb-0" href="/user/${u.id}"><i class="text-3xl transition-opacity bi bi-eye opacity-40 hover:opacity-100"></i></a>`
    if(has_auth) 
        btnblock += `<a class="opacity-40 hover:opacity-100" onclick="delete_confirm(this);"><i class="mx-3 text-3xl transition-opacity bi bi-x-circle"></i></a>`

    return `<tr class="h-10 md:p-4 usr-row" id="u-${u.id}">
            <td data-label="Přezdívka">${u.nickname}</td>
            <td data-label="Discord ID">${dscblock}</td>
            <td data-label="Počet překladů">${u.tr_count}</td>
            <td data-label="Počet bodů">${u.points.toFixed(1)}</td>
            <td data-label="Role">${get_role(u.points)}</td>
            <td class="flex flex-col md:table-row">${btnblock}</td>
        </tr>`
}

function search(target) {
    console.log('st')
    if (target.value == "" || target.value.length < 2) {
        if(!is_original) {
            $('.usr-row').animate({opacity: 0}, 300)
            setTimeout( () => table.innerHTML = originalHtml, 300)
            is_original = true
        }
        return
    }
    $('.usr-row').animate({opacity: 0}, 300)
    is_original = false

    let newHtml = ""
    setTimeout(() => {
        
        fetch('/api/search/user?' + new URLSearchParams({
            'q': target.value
        })).then(response => response.json()).then(r => r.result.forEach(a => {newHtml += make_row(a, r.has_auth)})).then(() => table.innerHTML = newHtml)
    }, 300);

}

function handleSearch(e) {
    clearTimeout(timeoutID)
    if(e.target.value.length > 1) {
        timeoutID = setTimeout(search, 300, e.target)
    } else {
        search(e.target)
    }
}

document.getElementById('search-field').addEventListener('input', handleSearch)