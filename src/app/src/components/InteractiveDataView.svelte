<script>
    import { onMount } from 'svelte';
    export let data;
    export let format = 'json'; // 'json' or 'yaml'
    export let onKeyClick = (path) => {};
    
    import yaml from 'js-yaml';

    function renderValue(value, path = []) {
        if (value === null) return '<span class="text-gray-500">null</span>';
        if (typeof value === 'boolean') return `<span class="text-yellow-500">${value}</span>`;
        if (typeof value === 'number') return `<span class="text-blue-500">${value}</span>`;
        if (typeof value === 'string') {
            // Check if the path ends with 'url' or '_url' and the value looks like a URL
            const lastPath = path[path.length - 1];
            if ((lastPath === 'url' || (lastPath != null && typeof lastPath === 'string' && lastPath.endsWith('_url'))) && 
                (value.startsWith('http://') || value.startsWith('https://'))) {
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
            
            // Use a button for interactive keys
            result += `${spacing}<span class="key"><button type="button" data-path="${pathString}" class="text-purple-500 hover:underline focus:outline-none">${key}</button></span>: `;
            
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

    $: formattedData = format === 'json' 
        ? processObject(data)
        : yaml.dump(data).split('\n').map(line => {
            const [key, ...rest] = line.split(':');
            if (rest.length) {
                return `<span class="key"><button type="button" data-path="${key.trim()}" class="text-purple-500 hover:underline focus:outline-none">${key}</button>:${rest.join(':')}</span>`;
            }
            return line;
        }).join('\n');

    let container;

    onMount(() => {
        const handleClick = (event) => {
            if (event.target.tagName === 'BUTTON' && event.target.dataset.path) {
                event.preventDefault();
                const path = event.target.dataset.path;
                onKeyClick(path);
            }
        };
        container.addEventListener('click', handleClick);

        return () => {
            container.removeEventListener('click', handleClick);
        };
    });
</script>

<!-- Use a div instead of pre -->
<div
    bind:this={container}
    class="bg-gray-800 text-white p-4 rounded overflow-auto font-mono whitespace-pre-wrap"
>
    {@html formattedData}
</div>

<style>
    :global(.key button) {
        background: none;
        border: none;
        padding: 0;
        margin: 0;
        color: inherit;
        cursor: pointer;
        text-align: left;
    }
    :global(.key button:hover),
    :global(.key button:focus) {
        text-decoration: underline;
    }
</style>