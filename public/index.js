const socket = new WebSocket('ws://localhost:8081');

var current_round   = 0;
var computed_rounds = 0;
const plot_path     = "./data/plots";
const default_path  = "./assets/startup";
var start_show_once = false

socket.addEventListener('open', function (event) {
    
});

/* Messages from the WebSocket server */
socket.addEventListener('message', function (event) {
    msg = JSON.parse(event.data);
    switch (msg.status) {
        case 'ready':
            current_round = 0;
            computed_rounds = 0;
            updateFigures();
            document.getElementById("computed_rounds_span").innerHTML = `${computed_rounds}`;
            document.getElementById("pseudocode-round").innerHTML   =`t = 1 until ${document.getElementById("f_rounds").value}`;
            document.getElementById("pseudocode-client").innerHTML  =`i = 1 until ${document.getElementById("clients").value}`;
            document.getElementById("pseudocode-episode").innerHTML =`i = 1 until ${document.getElementById("episodes").value}`;
            document.getElementById("pseudocode-tries").innerHTML   =`i = 1 until ${document.getElementById("tries").value}`;
            document.getElementById("maze_layout").src = plot_path + "/maze_layout.png";
            document.getElementById("apply-btn").disabled = false;
            alert("Model saved successfully.");
            break;
        case 'completed_round':
            document.getElementById("computed_rounds_span").innerHTML = msg.round;
            computed_rounds = parseInt(msg.round);
            if (computed_rounds > 0 && !start_show_once) {
                document.getElementById("start-btn").disabled = false;
                start_show_once = true;
            };
            if (current_round < computed_rounds) {
                document.getElementById("next-btn").disabled = false;
            };
            break;
        case 'show_next_round':
            current_round++;
            updateFigures();
            break;
        case 'counter_complete':
            document.getElementById("start-btn").disabled = false;
            document.getElementById("stop-btn").disabled = true;
            break;
    }
});

/* Assign values after browser finished loading the page */
window.onload = function () {
    document.getElementById("data_partitioning").onchange = function () {
        let val = document.getElementById("data_partitioning").value;
        switch (val) {
            case 'horizontal':
                document.getElementById("partition_size").disabled = true;
                document.getElementById("random_pos").disabled = false;
                break;
            case 'vertical':
            document.getElementById("partition_size").disabled = false;
                document.getElementById("random_pos").disabled = true;
                break;
        };
    };

    document.getElementById("clients").onchange = function () {
        let val = document.getElementById("clients").value;
        let current_clients = document.getElementById("python_client1").length;
        if (current_clients < val) {
            for (let i = current_clients; i <= val; i++) {
                document.getElementById("python_client1").add(new Option(`#${i}`, 'i'));
                document.getElementById("python_client2").add(new Option(`#${i}`, 'i'));
                document.getElementById("python_client3").add(new Option(`#${i}`, 'i'));
                document.getElementById("sql_client1").add(new Option(`#${i}`, 'i'));
                document.getElementById("sql_client2").add(new Option(`#${i}`, 'i'));
                document.getElementById("sql_client3").add(new Option(`#${i}`, 'i'));
            };
        } else {
            for (let i = current_clients; i >= val; i--) {
                document.getElementById("python_client1").remove(i);
                document.getElementById("python_client2").remove(i);
                document.getElementById("python_client3").remove(i);
                document.getElementById("sql_client1").remove(i);
                document.getElementById("sql_client2").remove(i);
                document.getElementById("sql_client3").remove(i);
            };
        }
    };

    for (let i = 1; i < 4; i++) {
        document.getElementById(`python_client${i}`).onchange = function () {
            if (current_round == 0) {
                document.getElementById(`python_client${i}_img`).src = default_path + "/heatmap.png";
            } else {
                val = document.getElementById(`python_client${i}`).value;
                document.getElementById(`python_client${i}_img`).src = plot_path + `/round${current_round}/client_policy_heatmap_python${val}.png`;
            };
        };
        document.getElementById(`sql_client${i}`).onchange = function () {
            if (current_round == 0) {
                document.getElementById(`sql_client${i}_img`).src = default_path + "/heatmap.png";
            } else {
                val = document.getElementById(`sql_client${i}`).value;
                document.getElementById(`sql_client${i}_img`).src = plot_path + `/round${current_round}/client_policy_heatmap_sql${val}.png`;
            };
        };
    }

    document.getElementById("apply-btn").onclick = function () {
        document.getElementById("apply-btn").disabled = "disabled";
        let parameters = {
            command: "apply",
            parameters: {
                learning_problem:  document.getElementById("learning_problem_size").value,
                data_partitioning: document.getElementById("data_partitioning").value,
                federated_rounds:  document.getElementById("f_rounds").value,
                clients:           document.getElementById("clients").value,
                partition_size:    document.getElementById("partition_size").value,
                episodes:          document.getElementById("episodes").value,
                tries:             document.getElementById("tries").value,
                learning_rate:     document.getElementById("learning_rate").value,
                epsilon:           document.getElementById("egreedy").value,
                random_pos:        document.getElementById("random_pos").value
            }
        };
        socket.send(JSON.stringify(parameters));
    };

    document.getElementById("start-btn").onclick = function () {
        max_rounds = parseInt(document.getElementById("f_rounds").value);
        socket.send(JSON.stringify({command: "start", current_round: current_round, total_rounds: max_rounds}));
        document.getElementById("start-btn").disabled = true;
        document.getElementById("stop-btn").disabled = false;
    };

    document.getElementById("stop-btn").onclick = function () {
        socket.send(JSON.stringify({command: "stop"}));
        document.getElementById("start-btn").disabled = false;
        document.getElementById("stop-btn").disabled = true;
    };

    document.getElementById("reset-btn").onclick = function () {
        current_round = 0;
        updateFigures();
    };

    document.getElementById("next-btn").onclick = function () {
        current_round++;
        updateFigures();
    };

    document.getElementById("prev-btn").onclick = function () {
        current_round--;
        updateFigures();
    };
};

function checkButtons() {
    if (current_round == document.getElementById("f_rounds").value || (current_round == computed_rounds) &&
       (computed_rounds > 0)) {
        document.getElementById("next-btn").disabled = true;
    } else if (current_round == 1) {
        document.getElementById("prev-btn").disabled  = true;
        document.getElementById("reset-btn").disabled = false;
    } else if (current_round == 0) {
        document.getElementById("reset-btn").disabled = true;
        document.getElementById("prev-btn").disabled  = true;
        if (computed_rounds == 0) {
            document.getElementById("next-btn").disabled  = true;
        } else {
            document.getElementById("next-btn").disabled  = false;
        };
    } else {
        console.log(document.getElementById("prev-btn").disabled);
        if (document.getElementById("next-btn").disabled)  { document.getElementById("next-btn").disabled  = false; };
        if (document.getElementById("prev-btn").disabled)  { document.getElementById("prev-btn").disabled  = false; };
        if (document.getElementById("reset-btn").disabled) { document.getElementById("reset-btn").disabled  = false; };
    };
};

function updateFigures() {
    document.getElementById("current_round_span").innerHTML = `${current_round}`;
    document.getElementById("heatmap_python").src    = plot_path + `/round${current_round}/server_policy_heatmap_python.png`;
    document.getElementById("heatmap_sql").src       = plot_path + `/round${current_round}/server_policy_heatmap_sql.png`;
    document.getElementById("sync_times_python").src = plot_path + `/round${current_round}/sync_times_python.png`;
    document.getElementById("sync_times_sql").src    = plot_path + `/round${current_round}/sync_times_sql.png`;
    document.getElementById("convergence").src       = plot_path + `/round${current_round}/convergence.png`;

    for (let i = 1; i < 4; i++) {
        if (current_round == 0) {
            document.getElementById(`python_client${i}_img`).src = default_path + "/heatmap.png";
            document.getElementById(`sql_client${i}_img`).src    = default_path + "/heatmap.png";
        } else {
            val_p = document.getElementById(`python_client${i}`).value;
            val_s = document.getElementById(`sql_client${i}`).value;
            document.getElementById(`python_client${i}_img`).src = plot_path + `/round${current_round}/client_policy_heatmap_python${val_p}.png`;
            document.getElementById(`sql_client${i}_img`).src    = plot_path + `/round${current_round}/client_policy_heatmap_sql${val_s}.png`;
        };
    };

    checkButtons();
};
