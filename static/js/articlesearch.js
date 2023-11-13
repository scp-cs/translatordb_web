const table = document.getElementById('tb-articles')
const originalHtml = table.innerHTML
const uid = window.location.pathname.split('/').at(-1)

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

function make_row(t, has_auth) {
    let titlelink = t.link ? `<a class="hover:underline" target="_blank" href="${t.link}">${t.name}</a>` : `<span class="text-gray-500">${t.name}</span>`
    btns = `<td class="flex flex-col gap-2 md:table-row"><a class="" href="/article/${t.id}/edit"><i class="bi bi-pencil-square opacity-40 hover:opacity-100 text-2xl transition-opacity"></i></a><a class="" onclick="delete_confirm(this);"><i class="bi bi-x-circle opacity-40 hover:opacity-100 text-2xl transition-opacity"></i></a></td>`

    return `<tr id="t-${t.id}" class="h-12">
    <td data-label="Název:">${titlelink}</td>
    <td data-label="Počet slov:">${t.words}</td>
    <td data-label="Bonus:">${t.bonus}</td>
    <td data-label="Zapsáno:">${t.added}</td>
    ${has_auth ? btns : ""}
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
        
        fetch('/api/search/article?' + new URLSearchParams({
            'q': target.value,
            'u': uid
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