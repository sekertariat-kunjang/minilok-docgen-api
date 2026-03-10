const fs = require('fs');
const content = fs.readFileSync('c:/Users/star/3D Objects/minlok/docgen-service/static/index.html', 'utf8');
const scriptMatches = content.match(/<script>([\s\S]*?)<\/script>/g);
if (scriptMatches) {
    scriptMatches.forEach((scriptMatch, index) => {
        const scriptCode = scriptMatch.replace(/<\/?script>/g, '');
        try {
            new Function(scriptCode);
            console.log(`Script ${index}: Syntax OK`);
        } catch (e) {
            console.error(`Script ${index} Syntax Error:`, e.message);

            // To find the line number, we can try to evaluate it
            const lines = scriptCode.split('\n');
            lines.forEach((l, i) => console.log(`${i + 1}: ${l}`));
        }
    });
} else {
    console.log('No scripts found');
}
