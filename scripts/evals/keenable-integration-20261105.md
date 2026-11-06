# Keenable integration verification — 2026-11-05

## Change

Integrates [PR #6](https://github.com/runningZ1/union-search-skill/pull/6), documents the published keyless limits, and removes the standalone WeChat search module. This removal includes its Python/Node entry points, examples, task navigation, Cheerio dependency and doctor check. RSS remains a separate module. WeChat was outside the CLI registry, so its removal does not change the 52 search channels / 53 capabilities provided by this integration.

The Keenable adapter also includes `Retry-After` in HTTP 429 errors, or advises a 300-second cooldown when that header is missing. It does not retry, switch providers or implement a shared quota manager.

## Published limits

Checked the [official rate limits](https://docs.keenable.ai/rate-limits) and [API reference](https://docs.keenable.ai/api-reference) on 2026-11-05:

- Keyless search: 1,000 requests/hour and at most 10 requests/second per egress IP, shared with other callers on that IP. Search and fetch have separate endpoint pools.
- Keyless requests need an application name in `X-Keenable-Title`, consume no credits and need no account/API key.
- Search returns at most 50 results per request. CLI default and `--limit 0` preserve acquired results, without automatic pagination.
- A key removes the hourly cap; the default authenticated limit is 10 requests/second per organization, shared by its keys and subject to credits and plan limits.
- Follow `Retry-After` after 429. The project's conservative two-second host spacing is an operating rule, not the provider's published ceiling.

## Real end-to-end stability run

Environment: Windows, Python 3.12.4, clean isolated worktree at PR head `7f37a5b4d64da87d6d724996b1594c1a91b77673` plus the maintenance changes. No root `.env` was copied. All `KEENABLE_*` environment variables were removed from test subprocesses. No mocks or fabricated provider responses were used.

Three rounds ran the following four paths, with at least two seconds between completed commands:

```bash
python scripts/channels/keenable/keenable_search.py duckdb -m 3 --site duckdb.org --json
python union_search_cli.py platform keenable "Python programming language" --limit 3 --fail-on-platform-error
python union_search_cli.py platform keenable langchain --limit 2 --param site=pypi.org --param published_after=1y --fail-on-platform-error
python union_search_cli.py search "open source vector database" --platforms keenable wikipedia --limit 3 --deduplicate --fail-on-platform-error
```

The second round's platform query was `开源 向量数据库` to cover Chinese input. All **12/12** successful paths passed checks for nonempty titles, HTTP(S) source URLs and excerpts. Filters returned matching hosts and dates. Each union call had **2/2** successful channels, six results and source attribution. Final URLs were unique; these samples did not contain a cross-provider duplicate, so they do not prove duplicate merging against an overlapping sample.

The run, including discovery, doctor and two negative cases, took **76.61 seconds**. Successful search commands took **2.516–3.656 seconds**, mean **3.099 seconds**. This is a small repeated live smoke run, not a long-duration soak test or throughput benchmark.

Two negative cases also behaved as expected: malformed `published_after` produced HTTP 400, `ok=false` and exit 4; an empty query produced a structured usage error and exit 2. Earlier real checks on the same PR showed default and `--limit 0` each returning 50 results.

A real Requests response hook observed `POST /v1/search/public` returning HTTP 200 with no `X-API-Key` or `Authorization` header. It sent only the public app identifier. The response included `X-RateLimit-Limit: 1000`, `X-RateLimit-Remaining: 979` and an `X-RateLimit-Reset` timestamp. This corroborates the published hourly pool; the 10/second ceiling comes from official documentation, not a saturation test.

Local raw evidence is in `.work/keenable-stability/` in the review checkout. It is intentionally excluded from Git and is not a distributed documentation dependency.

## Other checks and scope

- Root `npm ci` and Defuddle runtime `npm ci` completed against lockfiles after removal of Cheerio.
- CLI `list` and `schema`: `ok=true`, Keenable remains anonymous with no required environment key.
- `doctor --platforms keenable wikipedia`: `ok=true`, exit 0, no failed checks. Missing `.env` is an expected warning for this isolated keyless run; no WeChat/Cheerio check remains.
- Existing `test_platform_groups.py`: 5/5 passed, with no mocks in that test file.
- `defuddle https://example.com`: `ok=true`, title `Example Domain` and actual extracted content, confirming the retained Node content runtime still works.
- Yao structure, lint, governance and resource-boundary checks: all returned `ok=true`. Existing warnings remain for missing manifest metadata and the large deferred resource footprint (including installed Node dependencies).
- Heuristic trigger evaluation: 19/19 passed, with the removed WeChat example replaced by a Keenable query. This does not measure real model activation rates.
- No keyed account was used. No attempt was made to exhaust hourly/per-second limits or trigger 429 deliberately. Real 429 propagation and cooldown timing are therefore unverified; the new error branch was reviewed against the documented header contract.
- No full mocked test suite, broad provider regression, paid-quota test or long-duration stability claim is made.
