#!/usr/bin/env node

const DEVELOPMENT_HEADER = 'x-zotero-development-api';
const DEFAULT_API_URL = 'http://127.0.0.1:23119/api';

export function normalizeAPIURL(value = process.env.ZOTERO_LOCAL_API_URL || DEFAULT_API_URL) {
	let url = new URL(value);
	url.pathname = url.pathname.replace(/\/+$/, '');
	if (url.pathname != '/api') throw new Error(`Local API URL must end in /api: ${url}`);
	return url.toString();
}

export async function probeDevelopmentAPI(value) {
	let apiURL = normalizeAPIURL(value);
	let response;
	try { response = await fetch(`${apiURL}/`); }
	catch (error) { throw new Error(`Could not connect to local Zotero API at ${apiURL}: ${error.message}`); }
	if (response.headers.get(DEVELOPMENT_HEADER) != '1') throw new Error(`Refusing ${apiURL}: it is not marked as a Zotero development API`);
	if (!response.ok) throw new Error(`Development Zotero API at ${apiURL} returned HTTP ${response.status}`);
	return { url: apiURL, apiVersion: response.headers.get('zotero-api-version'), schemaVersion: response.headers.get('zotero-schema-version') };
}

async function main() {
	let args = process.argv.slice(2);
	let url;
	if (args.length == 2 && args[0] == '--url') url = args[1];
	else if (args.length) throw new Error('Usage: probe-dev-api.mjs [--url http://127.0.0.1:23119/api]');
	process.stdout.write(`${JSON.stringify(await probeDevelopmentAPI(url))}\n`);
}

if (process.argv[1] && new URL(`file://${process.argv[1]}`).href == import.meta.url) {
	main().catch(error => { process.stderr.write(`${error.message}\n`); process.exit(1); });
}
