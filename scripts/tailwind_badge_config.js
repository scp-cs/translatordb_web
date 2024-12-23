/** @type {import('tailwindcss').Config} */
module.exports = {
    content: ["../templates/embeds/**/*.j2", "../models/user.py"], // user.py added for the role colors, I really have to come up with a better way to do this
    corePlugins: {
        preflight: false, // Disable the preflight / reset so that we don't break WikiDot's (or other sites) CSS
    },
    plugins: [],
}