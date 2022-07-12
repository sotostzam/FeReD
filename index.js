const express = require('express');
const app = express();
const WebSocket = require('ws');

const wss = new WebSocket.Server({ port:8081 });

wss.on('connection', function connection(ws) {
    console.log('Connection with client established.');

    var args = null;
    const { spawn } = require('node:child_process');
    var apply_worker = null;
    var run_worker = null;
    
    function apply_model(args) {
        apply_worker = spawn(`bash start-api.sh "apply-model" ${args}`, [], { shell: true,  detached: true });
        apply_worker.stdout.on('data', (data) => {
            console.log(`stdout: ${data}`);
        });
        apply_worker.stderr.on('data', (data) => {
            console.log(`stderr: ${data}`);
        });
        apply_worker.on('error', (err) => {
            console.log(`error: ${err}`);
        });
        apply_worker.on('close', (code) => {
            console.log(`close with code: ${code}`);
            if (code == 0) {
                ws.send(JSON.stringify({status: "ready"}));
            };
            apply_worker = null;
            run_model(args);
        });
    };
    
    function run_model(args) {
        run_worker = spawn(`bash start-api.sh "run-model" ${args}`, [], { shell: true, detached: true });
        run_worker.stdout.on('data', (data) => {
            let completed_round = parseInt(data);
            ws.send(JSON.stringify({status: "completed_round", round: completed_round}));
        });
        run_worker.stderr.on('data', (data) => {
            console.log(`stderr: ${data}`);
        });
        run_worker.on('error', (err) => {
            console.log(`error: ${err}`);
        });
        run_worker.on('close', (code) => {
            console.log(`close with code: ${code}`);
        });
    };

    ws.on('message', function incoming(message) {
        console.log('received: %s', JSON.parse(message));
        msg = JSON.parse(message);
        switch (msg.command) {
            case 'apply':
                args = `${msg.parameters.learning_problem} ${msg.parameters.data_partitioning} ` + 
                       `${msg.parameters.federated_rounds} ${msg.parameters.clients} ` + 
                       `${msg.parameters.partition_size} ${msg.parameters.episodes} ` +
                       `${msg.parameters.tries} ${msg.parameters.learning_rate} ${msg.parameters.random_pos}`;
                       
                if (apply_worker != null) { process.kill(-apply_worker.pid); };
                if (run_worker != null)   { process.kill(-run_worker.pid); };
                
                apply_model(args);
                break;
        };
    })
})

app.listen(8000, () => console.log('listening at 8000'));
app.use(express.static('public'));
