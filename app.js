const express = require('express');
const app = express();
const WebSocket = require('ws');

const wss = new WebSocket.Server({ port:8081 });

wss.on('connection', function connection(ws) {
    console.log('Client connected successfully.');

    var args = null;
    const { spawn } = require('node:child_process');
    const { fork }  = require('node:child_process');
    var model_worker   = null;
    
    var counter_worker = fork("worker_counter.js"); 
    counter_worker.on('message', message => {
        msg = JSON.parse(message);
        switch (msg.command) {
            case 'advance_round':
                ws.send(JSON.stringify({status: "show_next_round"}));
                break;
            case 'completed':
                ws.send(JSON.stringify({status: "counter_complete"}));
                break;
        };
    });
    
    function run_model(args) {
        model_worker = spawn(`cd public/data; bash start-api.sh ${args}`, [], { shell: true, detached: true });
        model_worker.stdout.on('data', (data) => {
            decoded_data = data.toString('utf8');
            if (isNaN(parseInt(decoded_data))) {
                console.log(decoded_data);
            } else {
                let completed_round = parseInt(data);
                if (completed_round == 0) {
                    ws.send(JSON.stringify({status: "ready"}));
                } else {
                    ws.send(JSON.stringify({status: "completed_round", round: completed_round}));
                    counter_worker.send(JSON.stringify({command: "computed_rounds", computed_rounds: completed_round}));
                };
            };
        });
        model_worker.stderr.on('data', (data) => {
            console.log(`stderr: ${data}`);
        });
        model_worker.on('error', (err) => {
            console.log(`error: ${err}`);
        });
        model_worker.on('close', (code) => {
            if (code != 0) {
                console.log(`Child process error code: ${code}`);
            };
            model_worker = null;
        });
    };

    ws.on('message', function incoming(message) {
        msg = JSON.parse(message);
        switch (msg.command) {
            case 'apply':
                args = `${msg.parameters.learning_problem} ${msg.parameters.data_partitioning} ` + 
                       `${msg.parameters.federated_rounds} ${msg.parameters.clients} ` + 
                       `${msg.parameters.partition_size} ${msg.parameters.episodes} ` +
                       `${msg.parameters.tries} ${msg.parameters.learning_rate} ` +
                       `${msg.parameters.epsilon} ${msg.parameters.random_pos} 0`;
                       
                if (model_worker != null)   { process.kill(-model_worker.pid); };
                
                run_model(args);
                break;
            case 'start':
                counter_worker.send(JSON.stringify({command: "start", current_round: msg.current_round, total_rounds: msg.total_rounds}));
                break;
            case 'stop':
                counter_worker.send(JSON.stringify({command: "stop"}));
                break;
        };
    });
    
    ws.on('close', function() {
      console.log("Client disconnected.");
    });
})

app.listen(8000, () => console.log('To access FeReD, open the following URL: http://localhost:8000'));
app.use(express.static('public'));
