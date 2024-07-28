import { WebSocketServer, WebSocket } from 'ws';

const ws = new WebSocketServer({ port: 8032 });
ws.on('connection', function (ws) {
    console.log('client connected');
    ws.on('close', function () {
        console.log('client disconnected');
        clearInterval(intervalId);
    });
    function sendMessage() {
        if (ws.readyState == WebSocket.OPEN) {
            ws.send(
                JSON.stringify({
                    type: 'update',
                    values: [
                        ['pos', Math.random(), 'x_{1}'],
                        ['other', Math.random(), 'y_{1}'],
                    ],
                }),
            );
        }
    }
    const intervalId = setInterval(sendMessage, 100);
});
