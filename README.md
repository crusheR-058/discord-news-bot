# Discord News Bot

Posts tech news, AI model launches, research papers, Reddit posts, YouTube videos and Bluesky posts into 14 Discord channels every 15 minutes.
Free, no server, no bot account. It runs on GitHub Actions and posts through Discord webhooks.

## Channels and sources

| Channel | Secret name | Sources |
|---|---|---|
| `#tech-news` | `WEBHOOK_TECH_NEWS` | Techmeme, Ars Technica, The Verge, Wired, Hacker News front page (300+ points) |
| `#ai-news` | `WEBHOOK_AI_NEWS` | OpenAI, Anthropic (unofficial feed), Google DeepMind, Google AI, Mistral, Hugging Face, NVIDIA, TechCrunch AI, The Verge AI, Latent Space |
| `#ai-models` | `WEBHOOK_AI_MODELS` | Every new model on OpenRouter, Google News "new AI model" search, Hugging Face Daily Papers |
| `#dev-tools` | `WEBHOOK_DEV_TOOLS` | GitHub Changelog, VS Code, Cursor, Zed, JetBrains, Bun, Deno, The Pragmatic Engineer |
| `#product-launches` | `WEBHOOK_PRODUCT_LAUNCHES` | Product Hunt, Show HN (100+ points), TechCrunch Startups |
| `#t3-development` | `WEBHOOK_T3_DEVELOPMENT` | Theo (t3.gg) YouTube, create-t3-app, Next.js, tRPC, Drizzle, Tailwind CSS |
| `#backend-and-devops` | `WEBHOOK_BACKEND_DEVOPS` | Cloudflare, AWS News, Docker, Kubernetes, PostgreSQL, InfoQ, ByteByteGo, The Hacker News (security) |
| `#open-source` | `WEBHOOK_OPEN_SOURCE` | GitHub Blog open source, It's FOSS News, Phoronix |
| `#ui-ux-and-design` | `WEBHOOK_UI_UX_DESIGN` | Smashing Magazine, Nielsen Norman Group, UX Collective, Figma, web.dev, Chrome Developers, Josh W. Comeau |
| `#ai-discussions` | `WEBHOOK_AI_DISCUSSIONS` | Reddit r/singularity + r/OpenAI + r/ClaudeAI + r/artificial, Hacker News AI threads (150+ points), Simon Willison blog and Bluesky, Ethan Mollick on Bluesky |
| `#prompt-engineering` | `WEBHOOK_PROMPT_ENGINEERING` | Reddit r/PromptEngineering, Simon Willison prompt-engineering posts, Anthropic Engineering (unofficial feed), OpenAI Cookbook updates |
| `#ai-workflows` | `WEBHOOK_AI_WORKFLOWS` | Reddit r/n8n + r/AI_Agents, LangChain blog, n8n blog, Simon Willison AI-agents posts |
| `#model-comparisons` | `WEBHOOK_MODEL_COMPARISONS` | Google News "benchmark" and "leaderboard / LMArena / Artificial Analysis" searches, Simon Willison evals posts |
| `#local-ai` | `WEBHOOK_LOCAL_AI` | Reddit r/LocalLLaMA + r/ollama + r/LocalLLM, Ollama releases, LM Studio blog, Simon Willison local-LLM posts |

`#general-chat` and the voice channels get no feeds.

Each source posts at most 3 new items per run, so busy sources cannot flood a channel.
The first run only records what already exists. Posting starts from the second run.

## Setup (about 20 minutes)

### 1. Create a webhook for each channel

1. In Discord, open **Server Settings > Integrations > Webhooks**.
2. Click **New Webhook**. Name it (for example "AI News") and pick the channel.
3. Click **Copy Webhook URL**.
4. Repeat for each channel in the table above.

Your channels can have other names. The webhook decides the channel, not `feeds.json`.
You can also point two webhook secrets at the same channel to merge them.

**Keep webhook URLs secret.** Anyone who has one can post in that channel.
Never paste them into a file, a chat or a commit. If one leaks, delete it in Discord and make a new one.

### 2. Put this folder on GitHub

1. Create a free account at https://github.com and click **New repository**.
2. Make it **Public** (Actions minutes are unlimited for public repos). Webhook URLs stay hidden in Secrets.
3. Click **uploading an existing file** and drag in every file from this folder, including the `.github` folder.
   If the browser skips `.github`, create the file `.github/workflows/news.yml` with **Add file > Create new file** and paste its content.

### 3. Add the webhook URLs as secrets

In the repo: **Settings > Secrets and variables > Actions > New repository secret**.
Add one secret per channel. Use the **Secret name** from the table at the top, and the channel's webhook URL as the value.

A channel without a secret is skipped, so you can start with only some of them.

### 4. Start it

1. Open the **Actions** tab. If asked, click **I understand my workflows, go ahead and enable them**.
2. Click **discord-news > Run workflow**. This first run only records existing items.
3. From now on it runs every 15 minutes and posts new items.

## Change sources

Edit `feeds.json` on GitHub (pencil icon). Add or remove URLs in a channel's `feeds` list.

| To follow | Add this URL |
|---|---|
| A Bluesky account | `https://bsky.app/profile/HANDLE/rss` (for example `simonwillison.net`) |
| A Mastodon account | `https://mastodon.social/@NAME.rss` (use the account's own server) |
| A subreddit | add it to an existing Reddit URL: `r/LocalLLaMA+ollama+NEWSUB/top/.rss?t=day` |
| A YouTube channel | `https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID` |
| Any topic in the news | `https://news.google.com/rss/search?q=YOUR+TOPIC+when:1d&hl=en-US&gl=US&ceid=US:en` |
| Releases of a GitHub project | `https://github.com/OWNER/REPO/releases.atom` |
| An arXiv category | `https://rss.arxiv.org/rss/cs.AI` (very busy; Hugging Face Daily Papers is the curated version) |

More tested feeds: `https://www.engadget.com/rss.xml`, `https://www.tomshardware.com/feeds/all`, `https://9to5mac.com/feed/`,
`https://blogs.microsoft.com/feed/`, `https://aws.amazon.com/blogs/machine-learning/feed/`, `https://www.coindesk.com/arc/outboundfeeds/rss/`,
`https://www.space.com/feeds/all`, `https://www.gamedeveloper.com/rss.xml`, `https://dev.to/feed`.

To add a new channel: add a block to `feeds.json` with a new `webhook_secret` name, add a secret with that name (step 3),
and add a matching line under `env:` in `.github/workflows/news.yml` (for example `WEBHOOK_NEW: ${{ secrets.WEBHOOK_NEW }}`).

Each post uses the profile picture `avatars/<channel>.png` (channel name without `#`, for example `avatars/tech-news.png`).
To change one, replace that PNG (square, at least 128x128). A channel without a PNG uses the webhook's own picture.

## Known limits

- **Reddit:** Reddit allows about one request per minute without login, so the script waits 65 seconds between Reddit sources (a run takes about 4 minutes).
  Put several subreddits in one URL (`r/A+B+C`) instead of adding more Reddit URLs.
  Reddit has been closing free access and may block GitHub's servers or end RSS. If the Actions log shows `FAIL https://www.reddit.com/... HTTP 429` or `403` in every run, Reddit is blocking it. The other sources in those channels keep working.
- **X (Twitter):** not included. X has no free API. Reading posts costs about $0.005 each. Most AI labs and researchers also post on Bluesky and their blogs, which are covered here.
- **Anthropic:** has no official RSS feed. The `#ai-news` entry uses an unofficial community feed that can break.

## Troubleshooting

- Nothing posts: the first run never posts. Wait for the next run, or check the **Actions** tab for red runs.
- `skip #x: secret ... not set`: the secret name in GitHub does not match `feeds.json`, or the secret has no line under `env:` in `news.yml`.
- `FAIL <url>`: that site was down or blocked the request. The other sources still run, and the failed one is retried next run.
- GitHub pauses scheduled workflows in a repo with no activity for 60 days. The bot commits `seen.json` often, which counts as activity.
