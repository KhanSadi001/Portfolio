# Sadi Khan — portfolio (Django on Vercel)

A Django 6.1 site with the original particles.js background, plus:

- **Contact form**: saves messages to the database (read them in the admin). It can also email them to you through Resend. It uses a hidden spam-trap field and a signed timestamp, and allows 3 messages per 10 minutes per visitor.
- **Real likes**: stored in the database, one per visitor. A visitor is a salted hash, never a raw IP address.
- **Blog**: write posts in the admin panel (Markdown is supported, and the HTML is cleaned before display). Short posts show in full; longer posts get their own page.
- **Projects**: edit them in the admin. Language and stars are pulled live from GitHub and cached for an hour. Clicks on project links are counted through `/go/<slug>/`, which only redirects to URLs stored in the database, so it can't be abused as an open redirect.
- **Visitor stats**: page views per page per day, with no cookies, no third-party tracking and bots skipped.
- **Bit Flip game** at `/play/`: a 60-second binary game with a leaderboard. The server issues a signed, single-use round token, refuses scores sent before the round ends, caps the number of solves, and calculates the score itself.
- **Security**: a strict Content Security Policy (no inline scripts, no third-party scripts, Font Awesome hosted here), HSTS, HTTPS redirect, secure cookies, CSRF protection on every POST, an admin at a custom URL, and 12-character minimum admin passwords.

## Deploy on Vercel

You need a GitHub account and a Vercel account (sign up with GitHub).

1. **Put this `web` folder on GitHub.** Use GitHub Desktop or run:
   ```
   cd web
   git init
   git add .
   git commit -m "Portfolio"
   ```
   Then create an empty repo on github.com and follow its "push an existing repository" instructions.
   If you push the whole `my-portfolio` folder instead, set **Root Directory** to `web` in step 2.

2. **Import it in Vercel:** go to vercel.com, choose **Add New → Project**, and pick the repo. Vercel detects Django.
   Before you click Deploy, open **Environment Variables** and add:

   | Name | Value |
   |---|---|
   | `DJANGO_SECRET_KEY` | a long random string; generate one with `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
   | `DJANGO_SUPERUSER_USERNAME` | your admin username |
   | `DJANGO_SUPERUSER_PASSWORD` | a strong password, 12+ characters |
   | `ADMIN_PATH` | a hard-to-guess admin URL, e.g. `sadi-admin-7k2` |

   Click **Deploy**. This first deploy has no database yet, so pages will error. That's expected.

3. **Add the database:** in your Vercel project, open the **Storage** tab, create a **Neon** Postgres database (the free plan is enough), and connect it to this project. Vercel adds `DATABASE_URL` for you.

4. **Redeploy:** go to the **Deployments** tab, open the "…" menu on the latest deployment, and choose **Redeploy**. The build step (`build.py`) creates the tables, loads your projects and posts, and creates your admin user.

5. Open `https://<your-project>.vercel.app/<ADMIN_PATH>/` and log in.

### Optional extras

- **Email for new messages:** create a free API key at resend.com and add it as `RESEND_API_KEY`. Without your own domain, Resend only delivers to the email you signed up with, so set `CONTACT_TO_EMAIL` to that address.
- **Custom domain:** add it under Vercel → Settings → Domains, and add it to `EXTRA_ALLOWED_HOSTS` (comma-separated, e.g. `sadikhan.dev,www.sadikhan.dev`).
- **GitHub rate limit:** GitHub allows 60 unauthenticated API requests an hour, which is plenty with the one-hour cache. Add a `GITHUB_TOKEN` (fine-grained, no permissions needed) if you ever hit the limit.

After any change to environment variables, redeploy.

## Run it on your computer

```
cd web
python -m venv .venv
.venv\Scripts\activate          (on Windows; use "source .venv/bin/activate" on macOS/Linux)
pip install -r requirements.txt
python manage.py migrate
python manage.py createcachetable
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000. The admin is at http://127.0.0.1:8000/manage-site/. Locally the site uses SQLite and debug mode, so it needs no environment variables.

Run the tests with `python manage.py test core`.

## Where things live

| What | Where |
|---|---|
| Pages (HTML) | `core/templates/core/` |
| Styles | `core/static/core/css/main.css` |
| particles.js and its config | `core/static/core/js/particles.js`, `app.js` (unchanged from the original site) |
| Likes and project filter | `core/static/core/js/site.js` |
| Bit Flip game | `core/static/core/js/game.js` (browser), `core/game.py` (server rules) |
| Database tables | `core/models.py` |
| Settings and security headers | `config/settings.py` |
| Deploy-time database setup | `build.py` |

## Adding content

- **New blog post:** Admin → Posts → Add. Leave the title empty for a short post that shows in full on the blog page.
- **New project:** Admin → Projects → Add. Tick *Featured* to show it on the home page (the first 3 featured appear).
- **Messages:** Admin → Messages.
- **Hide a leaderboard cheater:** Admin → Scores, tick *Hidden*.
