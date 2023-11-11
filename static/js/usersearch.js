function add_row(userid, name, discord, displayname, tr_count, points) {
    ```<tr class="h-10 md:p-4" id="u-{{user.id}}">
            <td data-label="Přezdívka">{{ user.nickname }}</td>
            <td data-label="Discord ID">
            {% if user.discord %}
            <img class="w-8 h-8 rounded-[50%] inline md:mr-4" src={{ url_for('UserContent.get_avatar', uid=(user.discord or 0)) }}>
            {{ user.display or user.discord }}
            {% endif %}</td>
            <td data-label="Počet překladů">{{ user.count }}</td>
            <td data-label="Počet bodů">{{ "%.1f" % user.points }}</td>
            <td data-label="Role">{{get_user_role(user.points)}}</td>
            <td class="flex flex-col md:table-row">
                <a class="inline-block w-full mb-2 bg-blue-600 btn-rounded hover:bg-blue-500 md:inline md:w-auto md:mb-0" href="{{url_for('UserController.user', uid=user.id)}}">Zobrazit</a>
                {% if current_user.is_authenticated %}
                <a class="bg-red-600 btn-rounded hover:bg-red-400" onclick="delete_confirm(this);">Smazat</a>
                {% endif %}
            </td>
        </tr>```
}