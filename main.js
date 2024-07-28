const NAMESPACE = 'physiolab';
let REGISTERED = false;
let NAME = '';
const websocket = new WebSocket(`ws://localhost:${8032}`);
const calculator = Desmos.GraphingCalculator(calculatorElement);
/**
 * @param {number[]} arr
 */
function latexify(arr) {
    return '\\left[' + arr.map((n) => n.toPrecision(2)).join(',') + '\\right]';
}
/**
 * @type {Map.<string,number[]>}
 */
const storedValues = new Map();
/**
 * @type {Map.<string,string>}
 */
const latexNames = new Map();
websocket.onerror = console.error;
websocket.onmessage = function (event) {
    const contents = JSON.parse(event.data);
    if (REGISTERED) {
        console.assert(contents['type'] == 'update');
        if ('values' in contents) {
            for (const [name, value, latex] of contents['values']) {
                if (storedValues.has(name)) {
                    storedValues.get(name).push(value);
                } else {

                    storedValues.set(name, [value]);
                    latexNames.set(name, latex);
                }
            }
        }
    } else {

        console.assert(contents['type'] == 'init');
        REGISTERED = true;
        // This is where Svelte comes in handy
        NAME = contents['name'];
        calculator.setExpression({
            type: 'table',
            columns: [{ latex: contents['default_settings']['xAxisValue'] }, { latex: contents['defaultSettings']['yAxisValue'] }],
            id: `${NAMESPACE}__output`,
        });
        // Again, Svelte is useful
    }
};
setInterval(function () {
    // Update Desmos list instances
    for (const [name, value] of storedValues) {
        const desmosName = `${NAMESPACE}__${name}`;
        calculator.setExpression({
            type: 'expression',
            latex: `${latexNames.get(name)}=${latexify(value)}`,
            id: desmosName,
        });
    }
}, 1000);
