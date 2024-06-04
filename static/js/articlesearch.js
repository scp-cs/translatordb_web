const table = document.getElementById('tb-articles')
const originalTable = table.innerHTML
const uid = window.location.pathname.split('/').at(-1)

let is_original = true
let timeoutID = 0
let originalPageCount = parseInt($("#page-selector").children().last().text())

let searchResults = {}
let isSearching = false

function dateAsLocal(dateString) {
    const date = new Date(Date.parse(dateString))
    return date.toLocaleString("cs-CZ", {year: "numeric", month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit"})
}

function setPageCount(count) {
    console.log(count)
    $("#page-selector").empty()
    for(let i = 0; i < count; i++) {
        $("<span>", {
            class: "px-2 py-2 transition-all rounded-md hover:bg-white/30",
            text: i+1,
        }).appendTo("#page-selector").on("click", () => {showPage(i)})
    }
}

function showPage(page) {
    if(isSearching) {
        $('#tb-articles').empty()
        searchResults.result
            .slice(page*15, (page+1)*15)
            .forEach(row => {addRow(row, searchResults.has_auth)})
    } else {
        let currentLocation = new URL(window.location.href)
        currentLocation.searchParams.set("p", page)
        window.location = currentLocation.toString()
    }
}

function get_role(point_count) {
    role = ROLE_NONE
    for(const [limit, text] of Object.entries(ROLE_LIMITS)) {
        if(limit > point_count) 
            return role
        role = text
    }
    return role
}

function addRow(article, has_auth) {
    let template = $("#translation-search-template").contents().clone(true, true)

    if(article.link) {
        let link = $("<a>", {
            class: "hover:underline",
            href: article.link,
            target: "_blank",
            text: article.name})
        template.find("#translation-name").append(link)
    } else {
        template.find("#translation-name").addClass("text-gray-500").text(article.name)
    }
    template.find('#translation-bonus').text(article.bonus)
    template.find('#translation-words').text(article.words)
    
    if(article.corrector.id) {
        let link = $("<a>", {
            class: "hover:underline",
            href: `/user/${article.corrector.id}`,
            text: article.corrector.name})
        template.find("#translation-corrector").append(link)
    } else {
        template.find("#translation-corrector").text("N/A")
    }

    template.find("#translation-timestamp").text(dateAsLocal(article.added))
    
    if(has_auth) {
        let action_template = $("#translation-actions-template").contents().clone(true, true)
        action_template.find("#translation-edit").prop("href", `/article/${article.id}/edit`)
        template.find("tr").append(action_template)
    }

    $("#tb-articles").append(template)
}

function search(query) {
    if (query == "" || query.length < 2) {
        isSearching = false
        if(!is_original) {
            $('.usr-row').animate({opacity: 0}, 300)
            setPageCount(originalPageCount)
            setTimeout( () => table.innerHTML = originalTable, 300)
            is_original = true
        }
        return
    }
    isSearching = true
    $('.usr-row').animate({opacity: 0}, 300)
    is_original = false
    

    $("#tb-articles").empty()
    setTimeout(() => {
        fetch('/api/search/article?' + new URLSearchParams({
            'q': query,
            'u': uid
        })).then(response => response.json()).then(r => {
            searchResults = r
            setPageCount(Math.ceil(r.result.length/15))
            showPage(0)
        })
    }, 300);

}

function handleSearch(e) {
    clearTimeout(timeoutID)
    if(e.target.value.length > 1) {
        timeoutID = setTimeout(search, 300, e.target.value)
    } else {
        search(e.target.value)
    }
}

$("#search-field").on("input", handleSearch)