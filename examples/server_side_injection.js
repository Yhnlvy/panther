eval('2*2')
eval('2*2',22, 22, 34)

global.eval('2*2')
global.eval('2*2', 33)

var sum = new Function('a', 'b', 'return a + b');
var multiply = new Function('x', 'y', 'z', 'return x * y * z');


var sum = new global.Function('a', 'b', 'return a + b');
var multiply = new global.Function('x', 'y', 'z', 'return x * y * z');
