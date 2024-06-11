const ROLE_LIMITS = {
    5: 'Překladatel I',
    10: 'Překladatel II',
    25: 'Překladatel III',
    50: 'Překladatel IV',
    100: 'Překladatel V',
    200: 'Překladatel VI',
    500: 'Překladatel VII'
}

const ROLE_NONE = 'Žádná'

const table = document.getElementById('ut-body')
const originalTable = table.innerHTML

let isOriginal = true
let timeoutID = 0

function getRole(point_count) {
    role = ROLE_NONE
    for(const [limit, text] of Object.entries(ROLE_LIMITS)) {
        if(limit > point_count) 
            return role
        role = text
    }
    return role
}

function makeRow(user) {
    const discordBlock = user.discord ? `<img class="w-8 h-8 rounded-[50%] inline md:mr-4" src="/content/avatar/${user.discord}?s=thumb"> ${user.displayname ?? user.discord}` : user.displayname ?? user.discord
    return `<tr class="h-10 md:p-4 usr-row" id="u-${user.id}">
            <td data-label="Přezdívka">${user.nickname}</td>
            <td data-label="Discord ID">${discordBlock}</td>
            <td data-label="Počet překladů">${user.tr_count}</td>
            <td data-label="Počet bodů">${user.points.toFixed(1)}</td>
            <td data-label="Role">${getRole(user.points)}</td>
            <td class="flex flex-col md:table-row"><a class="inline-block w-full mb-2 md:inline md:w-auto md:mb-0" href="/user/${user.id}"><i class="text-3xl transition-opacity bi bi-eye opacity-40 hover:opacity-100"></i></a></td>
        </tr>`
}

function search(query) {
    if (query == "" || query.length < 2) {
        $('#page-selector').removeClass('hidden')
        if(!isOriginal) {
            table.innerHTML = originalTable
            isOriginal = true
        }
        return
    }
    $("#page-selector").addClass('hidden')
    isOriginal = false
    let newHtml = ""
    fetch('/api/search/user?' + new URLSearchParams({
        'q': query
    }))
    .then(response => response.json())
    .then(r => r.result.forEach(user => {newHtml += makeRow(user)}))
    .then(() => table.innerHTML = newHtml)

}

function handleSearch(event) {
    clearTimeout(timeoutID)
    if(event.target.value.length > 1) {
        timeoutID = setTimeout(search, 300, event.target.value)
    } else {
        search(event.target.value)
    }
}

$("#search-field").on("input", handleSearch)