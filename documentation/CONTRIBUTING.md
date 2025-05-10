# Contributing to Opsmith

First off, thanks for being here — your interest means a lot!  
Opsmith is a growing collection of handcrafted tools, and we’d love your help shaping it.

---

## What Can I Contribute?

You can contribute in a variety of ways:

- **Add a new tool** — If you've built something cool, modular, and helpful, bring it in!
- **Fix bugs** — See something broken? Smash it.
- **Improve documentation** — Clear docs make everyone’s life easier.
- **Optimize performance** — If you can make a script smarter or faster, we want to see it.
- **Suggest ideas** — Open an issue with your concept or tool proposal.

---

## Project Structure

Each tool should live in its own subfolder like this:

```

opsmith/
├── vidsummary/        # tool folder
│   ├── script.py
│   ├── README.md
│   └── ...

````

Tools must include:
- A `README.md` explaining setup and usage
- Clean, readable code
- If using APIs, `.env.example` and dotenv support

---

## Guidelines

- Follow clean code principles. Comment where it helps.
- Dependencies should be lightweight and justified.
- Tools should be modular — ideally usable as scripts and as imports.
- Keep things cross-platform friendly if possible.

---

## Commit Style

Follow conventional commits:

```bash
feat: add new tool for transcript post-processing
fix: resolve audio conversion bug
docs: improve usage examples in vidsummary README
````

---

## 🔧 Setup for Local Development

1. Clone the repo:

   ```bash
   git clone https://github.com/yourusername/opsmith.git
   cd opsmith
   ```

2. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install project-wide tools if needed:

   ```bash
   pip install -r requirements.txt
   ```

Each tool may have its own setup instructions — check their README files.

---

## Submitting a Pull Request

1. Fork the repo and create your branch:

   ```bash
   git checkout -b feat/your-tool-name
   ```

2. Make your changes and push:

   ```bash
   git push origin feat/your-tool-name
   ```

3. Open a PR and describe your addition. Bonus points for including screenshots or usage examples!

---

## ❤️ Thank You!

Your contribution makes this project better for everyone.
We can't wait to see what you build — forge on, Opsmith 🛠

---
