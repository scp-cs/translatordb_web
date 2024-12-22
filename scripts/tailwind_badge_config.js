/** @type {import('tailwindcss').Config} */
module.exports = {
    content: ["../templates/partials/translator_badge.j2", "../models/user.py"],
    corePlugins: {
        preflight: false, // Disable the preflight / reset so that we don't break WikiDot's (or other sites) CSS
    },
    plugins: [],
}