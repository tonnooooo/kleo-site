# Kleo — landing page

Static single-file site for Kleo, an MCP server that renders YouTube videos and Shorts from inside Claude, ChatGPT, Grok, Claude Code, Cursor, VS Code, OpenCode and Gemini CLI. Served by GitHub Pages at https://tonnooooo.github.io/kleo-site/; no build step.

- Edit `index.html`, push to `main`, the site updates within a few minutes.
- The server address is not hard-coded. Every snippet uses the placeholder `https://mcp.kleo.ai/mcp`, and the page replaces it at load time with `mcp_url` from `config.json` (today: the production server on workers.dev). To move the server, change `config.json` only; keep the placeholder exact in every new snippet, `data-copy` attribute and text node. The optional `note` in `config.json` is shown above the connect tabs.
- The page runs in one flow: hero, How it works, Templates, Behind the scenes, Connect (client tabs plus the tool table), Pricing (the free tier, and credit packs badged as not open yet), FAQ, Account. The Account section replaced the old waitlist: there is no `<form>` anywhere on the site and nothing collects an address, because getting in is one button on the server's own page.
- "Kleo" is a placeholder name: search for `Kleo` / `kleo` in `index.html`.
- Checks after editing, no browser needed: tag balance with Python's `html.parser`, and `node --check` on the script block.
- `worker/kleo_worker.py` is a copy of the GPU worker script, published so a rented machine could download it at boot when `VAST_BOOTSTRAP_URL` is set on the server. The production image already ships the worker, so this copy is only a fallback; keep it in sync with `kleo-mcp/worker/kleo_worker.py` if you ever use it.
