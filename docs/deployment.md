# Deployment

The production site uses GitHub Pages at `https://benchopedia.com`. Cloudflare
manages DNS and redirects the alternate domains to that address.

## GitHub Pages

In the repository's **Settings → Pages**, select **GitHub Actions** as the
publishing source and set the custom domain to `benchopedia.com`. Set the domain
on GitHub before pointing DNS at Pages. With an Actions publishing source, a
`CNAME` file is unnecessary; the domain lives in repository settings.

The workflow runs the Python build, generated-site checks, and Node.js UI checks.
Only successful builds on `main` deploy. Pull requests run the same checks without
uploading or publishing the website. The SQLite database is a build artifact;
only `dist/` is uploaded. No hosting credentials are stored in the repository.

For a manual redeploy, open **Actions → GitHub Pages → Run workflow** and select
`main`. To roll back, revert the relevant change through a pull request; merging
the revert rebuilds and redeploys the previous content.

## Cloudflare DNS

For `benchopedia.com`, use these records:

| Type | Name | Target | Proxy status |
| --- | --- | --- | --- |
| A | @ | 185.199.108.153 | DNS only |
| A | @ | 185.199.109.153 | DNS only |
| A | @ | 185.199.110.153 | DNS only |
| A | @ | 185.199.111.153 | DNS only |
| CNAME | www | khooeee.github.io | DNS only |

Replace conflicting web records for these names; preserve email and unrelated
records. Keep Pages records DNS only so GitHub can check DNS and issue its HTTPS
certificate. Once the certificate is ready, enable **Enforce HTTPS** in GitHub's
Pages settings. GitHub redirects `www.benchopedia.com` to the configured apex
domain when both are set up.

For `benchopedia.ai`, configure proxied A records for `@` and `www` pointing to
`192.0.2.1` (Cloudflare's placeholder for redirect-only domains). Add a Single
Redirect rule matching both hostnames, with a dynamic destination:

```text
concat("https://benchopedia.com", http.request.uri.path)
```

Use status **301** and enable **Preserve query string**. Keep the `.ai` records
proxied so Cloudflare handles the redirect. Check that both HTTP and HTTPS
requests, nested paths, and search query strings reach the matching `.com` URL.

## Verify production

After the first deployment, check the homepage, a benchmark article, a task page,
search, and an unknown URL (which should return the custom 404 page). Check HTTPS
and redirects for the apex and `www` names on both domains. DNS changes and HTTPS
certificate issuance can take time.

GitHub Pages limits the published site to 1 GB and has a soft bandwidth limit of
100 GB per month. The workflow builds from the committed benchmark snapshots;
it does not re-import upstream datasets during deployment.
