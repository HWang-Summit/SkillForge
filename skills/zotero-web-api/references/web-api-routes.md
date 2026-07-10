# Zotero Web API Routes

Base URL: `https://api.zotero.org`

## Authentication

Send the API key in a header:

```text
Zotero-API-Key: <key>
Zotero-API-Version: 3
```

Do not put the key in URLs, logs, or command output.

## Key Status

```text
GET /keys/current
```

Use this to discover `userID`, username, and access scope. The response can include the key string, so scripts must strip it before output.

## Collections

```text
GET  /users/<userID>/collections?limit=100
GET  /groups/<groupID>/collections?limit=100
POST /users/<userID>/collections
POST /groups/<groupID>/collections
DELETE /users/<userID>/collections/<collectionKey>
DELETE /groups/<groupID>/collections/<collectionKey>
```

Create a top-level collection:

```json
[{"name": "Papers"}]
```

Create a child collection:

```json
[{"name": "To Read", "parentCollection": "PARENTKEY"}]
```

Successful writes return a response with `successful["0"].key` and `successful["0"].version`.

Use collection deletion only for explicit cleanup, normally for temporary test collections. Send `If-Unmodified-Since-Version` when the current collection version is available.

## Items

```text
GET   /users/<userID>/items/top?q=<query>&limit=100
GET   /groups/<groupID>/items/top?q=<query>&limit=100
POST  /users/<userID>/items
POST  /groups/<groupID>/items
PATCH /users/<userID>/items/<itemKey>
PATCH /groups/<groupID>/items/<itemKey>
```

Create item payloads are arrays:

```json
[
  {
    "itemType": "journalArticle",
    "title": "...",
    "creators": [],
    "collections": ["COLLECTIONKEY"],
    "tags": [{"tag": "machine learning"}]
  }
]
```

When PATCHing an existing item, send the full desired `collections` list and use:

```text
If-Unmodified-Since-Version: <item version>
```

If Zotero returns `412 Precondition Failed`, refetch the item and retry only if the user still wants the write.

## Pagination

List endpoints can return more than one page. Use:

```text
limit=100&start=<offset>
```

Stop when `start + limit >= Total-Results` or when a page returns fewer than `limit` rows.

## Common Errors

- `401` or `403`: missing key or insufficient access.
- `404`: wrong user/group/library/item/collection key.
- `409`: invalid item data or write conflict.
- `412`: version mismatch; refetch before retrying.
- Network/DNS failures: retry only after confirming connectivity.
