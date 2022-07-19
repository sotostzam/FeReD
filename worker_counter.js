let intervalID;
let total_rounds;
let computed_rounds;
let current_round;

function start_loop() {
    if (current_round == total_rounds) {
        process.send(JSON.stringify({command: "completed"}));
        clearInterval(intervalID);
        intervalID = null;
    } else {
        if (current_round < computed_rounds) {
            process.send(JSON.stringify({command: "advance_round"}));
            current_round++;
        };
    };
};

process.on("message", message => {
    msg = JSON.parse(message);
    switch (msg.command) {
        case 'computed_rounds':
            computed_rounds = msg.computed_rounds;
            break;
        case 'start':
            current_round = msg.current_round;
            total_rounds = msg.total_rounds;
            if (!intervalID) {
                intervalID = setInterval(start_loop, 1000);
            };
            break;
        case 'stop':
            clearInterval(intervalID);
            intervalID = null;
            break;
    };
});
