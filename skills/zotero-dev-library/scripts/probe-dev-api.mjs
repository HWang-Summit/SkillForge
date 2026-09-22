#!/usr/bin/env node

const PLUGIN_HEADER = 'x-zotero-galaxypedia-api';
const DEFAULT_API_URL = 'http://127.0.0.1:23119/api/galaxypedia/v1';

export function normalizeAPIURL(value = process.env.ZOTERO_LOCAL_API_URL || DEFAULT_API_URL) {
	let url = new URL(value);
	url.pathname = url.pathname.replace(/\/+$/, '');
	if (!url.pathname.endsWith('/api/galaxypedia/v1')) {
		throw new Error(`Galaxypedia API URL must end in /api/galaxypedia/v1: ${url}`);
	}
	return url.toString();
}

export async function probeDevelopmentAPI(value) {
	let apiURL = normalizeAPIURL(value);
	let response;
	try {
		response = await fetch(apiURL + '/capabilities');
	}
	catch (error) {
		throw new Error(`Could not connect to the Galaxypedia Zotero plugin at ${apiURL}: ${error.message}`);
	}
	let capabilities = await response.json().catch(() => null);
	if (response.headers.get(PLUGIN_HEADER) != '1') {
		throw new Error(`Refusing ${apiURL}: it is not marked as a Galaxypedia plugin API`);
	}
	if (!response.ok || !capabilities || capabilities.api !== 1) {
		throw new Error(`Galaxypedia Zotero plugin at ${apiURL} returned an invalid capabilities response (HTTP ${response.status})`);
	}
	return {
		url: apiURL,
		pluginVersion: capabilities.plugin_version,
		zoteroVersion: capabilities.zotero_version,
		writeEnabled: capabilities.write_enabled,
		capabilities: capabilities.capabilities,
	};
}

async function main() {
	let args = process.argv.slice(2);
	let url;
	if (args.length == 2 && args[0] == '--url') url = args[1];
	else if (args.length) throw new Error('Usage: probe-dev-api.mjs [--url http://127.0.0.1:23119/api/galaxypedia/v1]');
	process.stdout.write(JSON.stringify(await probeDevelopmentAPI(url)) + '\n');
}

if (process.argv[1] && new URL(`file://${process.argv[1]}`).href == import.meta.url) {
	main().catch(error => {
		process.stderr.write(`${error.message}\n`);
		process.exit(1);
	});
}
