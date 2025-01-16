<script>
    export let data;
    export let format = 'json'; // 'json' or 'yaml'
    export let onKeyClick = (path) => {};
    
    import yaml from 'js-yaml';

    function renderValue(value, path = []) {
        if (value === null) return '<span class="text-gray-500">null</span>';
        if (typeof value === 'boolean') return `<span class="text-yellow-500">${value}</span>`;
        if (typeof value === 'number') return `<span class="text-blue-500">${value}</span>`;
        if (typeof value === 'string') {
            // Check if the path ends with 'url' and the value looks like a URL
            if (path[path.length - 1] === 'url' && (value.startsWith('http://') || value.startsWith('https://'))) {
                return `<span class="text-green-500"><a href="${value}" target="_blank" class="hover:underline">"${value}"</a></span>`;
            }
            return `<span class="text-green-500">"${value}"</span>`;
        }
        return '';
    }

    function processObject(obj, indent = 0, path = []) {
        let result = '';
        const spacing = '  '.repeat(indent);
        
        for (const [key, value] of Object.entries(obj)) {
            const currentPath = [...path, key];
            const pathString = currentPath.join('.');
            
            result += `${spacing}<span class="key"><a href="#" data-path="${pathString}" class="text-purple-500 hover:underline">${key}</a></span>: `;
            
            if (typeof value === 'object' && value !== null) {
                if (Array.isArray(value)) {
                    result += '[\n';
                    value.forEach((item, index) => {
                        if (typeof item === 'object' && item !== null) {
                            result += `${spacing}  ${processObject(item, indent + 1, [...currentPath, index])}`;
                        } else {
                            result += `${spacing}  ${renderValue(item, [...currentPath, index])},\n`;
                        }
                    });
                    result += `${spacing}],\n`;
                } else {
                    result += '{\n';
                    result += processObject(value, indent + 1, currentPath);
                    result += `${spacing}},\n`;
                }
            } else {
                result += `${renderValue(value, currentPath)},\n`;
            }
        }
        return result;
    }

    function handleClick(event) {
        if (event.target.tagName === 'A' && event.target.dataset.path) {
            // Only prevent default and handle click for keys (which have data-path)
            event.preventDefault();
            const path = event.target.dataset.path;
            onKeyClick(path);
        }
        // URLs (without data-path) will use their default behavior
    }

    $: formattedData = format === 'json' 
        ? processObject(data)
        : yaml.dump(data).split('\n').map(line => {
            const [key, ...rest] = line.split(':');
            if (rest.length) {
                return `<span class="key"><a href="#" data-path="${key.trim()}" class="text-purple-500 hover:underline">${key}</a>:${rest.join(':')}</span>`;
            }
            return line;
        }).join('\n');
</script>

<pre
    class="bg-gray-800 text-white p-4 rounded overflow-auto"
    on:click={handleClick}
>{@html formattedData}</pre>

<style>
    pre {
        font-family: monospace;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    :global(.key a) {
        text-decoration: none;
    }
    :global(.key a:hover) {
        text-decoration: underline;
    }
</style> 