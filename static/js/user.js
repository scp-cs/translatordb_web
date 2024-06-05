const modWindow = document.getElementById('modal-window')
const modOverlay = document.getElementById('modal-overlay')

const table = document.getElementById('tb-articles')
const originalTable = table.innerHTML
const uid = window.location.pathname.split('/').at(-1)

let isOriginal = true
let timeoutID = 0
let originalPageCount = parseInt($("#page-selector").children().last().text())

let searchResults = {}
let isSearching = false
let currentPage = 0

// ===== UTILITY FUNCTIONS ======

/**
 * Accepts a parsable date string and converts it to the "cs-CZ" locale format
 * @param {string} dateString 
 * @returns string
 */
function dateAsLocal(dateString) {
    const date = new Date(Date.parse(dateString))
    return date.toLocaleString("cs-CZ", {year: "numeric", month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit"})
}

/**
 * Adds or changes a URL GET parameter and reloads the page
 * @param {string} key The key to be added / changed
 * @param {string} value The value to set
 */
function addGetParam(key, value) {
    let currentLocation = new URL(window.location.href)
    currentLocation.searchParams.set(key, value)
    window.location = currentLocation.toString()
}

// ===== MODAL FUNCTIONS =====

function clickOut(e) {
    if(!modWindow.contains(e.target)) {
        modalClose()
    }
}

function modalClose() {
    //$("body").css("overflow-y", "scroll") // Re-enable body scrolling
    $("#modal-overlay").fadeOut(200)
    $(window).off("click", clickOut)
}

function modalOpen(articleId, articleName) {
    //$("body").css("overflow-y", "hidden")   // Disable body scrolling while the modal is open
    $("#confirm-text").text(`Chcete smazat článek "${articleName.trim()}"?`)
    $("#btn-delete-yes").on("click", () => deleteArticle(articleId))
    $("#modal-overlay").css("display", "flex").hide().fadeIn(200)
    setTimeout(() => $(window).on("click", clickOut), 100)  // Wait for a bit so the event doesn't fire from the current click
}

function deleteArticle(id) {
    fetch(`/article/${id}/delete`, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        }
    }).then(() => window.location.reload())
}

// ===== SEARCH FUNCTIONS =====

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
        currentPage = page
        $('#tb-articles').empty()
        searchResults.result
            .slice(page*15, (page+1)*15)
            .forEach(row => {addRow(row, searchResults.has_auth)})
    } else {
        addGetParam("p", page)
    }
}

function setSorting(order) {
    if(isSearching) {
        switch (order) {
            case 'az':
                searchResults.result.sort((a, b) => a.name.localeCompare(b.name, undefined, {numeric: true}))
                break
            case 'latest':
                searchResults.result.sort((a, b) => {return Date.parse(b.added) - Date.parse(a.added)})
                break
            case 'words':
                searchResults.result.sort((a, b) => b.words - a.words)
            default:
                break
        }
        showPage(currentPage)
    } else {
        addGetParam("sort", order)
    }
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
        template.append(action_template)
    }

    $("#tb-articles").append(template)
}

function search(query) {
    if (query == "" || query.length <= 2) {
        if(isSearching) {
            setPageCount(originalPageCount)
            table.innerHTML = originalTable
            isSearching = false
        }
        return
    }
    isSearching = true
    $('.usr-row').animate({opacity: 0}, 300)
    fetch('/api/search/article?' + new URLSearchParams({
        'q': query,
        'u': uid
    })).then(response => response.json()).then(r => {
        searchResults = r
        setPageCount(Math.ceil(r.result.length/15))
        showPage(0)
    })

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