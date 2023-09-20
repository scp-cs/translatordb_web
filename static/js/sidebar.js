const sidebar = document.getElementById('sidebar');
const toggle = document.getElementById('sidebar-toggle');
const toggle_close = document.getElementById('sidebar-close');

let sidebar_open = false;

function openSidebar() {
    if(!sidebar_open) {
        sidebar.classList.remove('-translate-x-full');
        toggle.classList.add('hidden');
        setTimeout(() => {window.addEventListener('click', clickAway)}, 500);
        sidebar_open = true;
    }
}

function closeSidebar() {
    if(sidebar_open) {
        sidebar_open = false;
        sidebar.classList.add('-translate-x-full');
        window.removeEventListener('click', clickAway);
        setTimeout(() => {toggle.classList.remove('hidden')}, 500); // Wait for sidebar to close
    }
}

function clickAway(e) {
    if (!sidebar.contains(e.target)){
        closeSidebar();
    } 
}

toggle.addEventListener('click', openSidebar);
toggle_close.addEventListener('click', closeSidebar);
closeSidebar();

