jQuery(document).ready(function($) {
    const pesLobby = {
        init: function() {
            this.getServerStatus();
            this.setupEventListeners();
        },

        getServerStatus: function() {
            $.ajax({
                url: pesData.apiUrl + 'status',
                method: 'GET',
                success: function(response) {
                    $('#server-status').html(`
                        <div class="server-info">
                            <p>Players Online: ${response.players}</p>
                            <p>Active Matches: ${response.matches}</p>
                            <p>Lobbies: ${response.lobbies}</p>
                        </div>
                    `);
                },
                error: function() {
                    $('#server-status').html('<p>Error loading server status</p>');
                }
            });
        },

        setupEventListeners: function() {
            // Add event listeners for lobby actions
        }
    };

    pesLobby.init();
});
