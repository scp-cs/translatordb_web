const sidebar = document.getElementById('sidebar');
const toggle = document.getElementById('sidebar-toggle');
const toggle_close = document.getElementById('sidebar-close');
const body = document.getElementsByTagName('body')[0]

let sidebar_open = false;

// I hate this script

function openSidebar() {
    if(!sidebar_open) {
        sidebar.classList.remove('-translate-x-full');
        toggle.classList.add('opacity-0');
        setTimeout(() => {window.addEventListener('click', clickAway)}, 500);
        sidebar_open = true;
        if(!matchMedia('(min-width: 768px)').matches) {
            body.style.overflowY = 'hidden'
            sidebar.style.overflowY = 'scroll'
        }
    }
}

function closeSidebar() {
    if(sidebar_open) {
        sidebar_open = false;
        sidebar.classList.add('-translate-x-full');
        window.removeEventListener('click', clickAway);
        setTimeout(() => {toggle.classList.remove('opacity-0')}, 500); // Wait for sidebar to close
        if(!matchMedia('(min-width: 768px)').matches) {
            body.style.overflowY = 'scroll'
            sidebar.style.overflowY = 'hidden'
        }
    }
}

function clickAway(e) {
    console.log(e.target.id)
    if (!sidebar.contains(e.target) && e.target.id != 'sidebar-toggle'){
        closeSidebar();
    } 
}

toggle.addEventListener('click', openSidebar);
toggle_close.addEventListener('click', closeSidebar);
closeSidebar();

