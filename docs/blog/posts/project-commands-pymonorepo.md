---
date: 2025-03-26
authors:
  - rogerk
categories:
  - python
  - monorepos
  - codebase
---

# How to Build this product?

In my last post, see [here](auth-flow.md), I diagrammed an OAuth workflow. That workflow is a synchronous workflow, each actor invokes and waits for a response, but it sets the stage for building our event-driven product which will specialize in multiple types of asynchronous workflows. So let's start this product with a discussion about monorepos.

## Cracking the monorepo

A '_monorepo_' is a single repository that contains multiple projects. It is a popular way to organize codebases with many coupled components, and is also used at very big companies like Google, Facebook, and Twitter.

<!-- more -->

Monorepos can provide quite a pleasant development experience when done right — with the right tooling, practices, and, of course, the right use case. Monorepos solve a very specific problem: local dependencies between projects force them to be updated together, which eliminates certain types of technical debt (e.g. ensures all current projects are always compatible with each other).

This post focuses on a very specific use case — `_uv_` Python monorepos. Until very recently, Python monorepos were quite hard to set up and maintain, with problems like the ones I mentioned above being quite common.

However, nowadays, we have a bunch of excellent tooling available with great out-of-the-box monorepo support. Guess why I will be using '_uv_' for building and managing this project?

## A GUI, a CLI and a Web Service walk into a bar ...

This is a tongue in cheek way of illustrating our target vision ... we will need to create an area (project repo) for 3 or more actors (GUI, CLI, web service). In order to produce a working OAuth workload, we need two or more web services:

- '_AuthService_' for looking up credentials (user name & password) provided by a user
- '_AppService_' for the initial application to invoke to get work done. The applications will include a '_GUI_' and a '_CLI_' command line utility.

<!----- more ------>

Does that joke into make more sense now? So we will start creating the scenario from my last post on OAuth workflow and place it all into a single code base we will create as a monorepo. A monorepo is a code base which has multiple applications or components in it, but each can be developed and run separately from the other. The share a project repository because they share dependencies. Pretend each of those four actors have modules/libraries they depend upon to be built into a single deliverable application or component. Together each actor is part of the product we will build that demonstrate our event-driven services architecture. That implies some products will be separate or independent of the others. They will interact with each other asynchronously.

Let's move on ...

## Initial creation of a repo

In this post, I am going to share an approach to building Python '_monorepos_' that solves these issues in a very elegant way. The benefits of this approach are:

- **it works with any `uv` project**
- **it needs little to zero maintenance and boilerplate**
- **it provides end-to-end pipeline caching** — including steps downstream to building the image (like running linters and tests), which is quite rare
- **it’s easy to run locally and in CI**

Here are the first commands to make this project monorepo:

```sh
mkdir event-based-svcs
cd event-based-svcs
uv init
uv add --group dev ruff pytest pytest-cov mkdocstrings mkdocs
source .venv/bin/activate
mkdocs new .
mkdocs build -s
```

Phew! That was a lot of commands. Let’s break them down:

- Creates a directory '_mkdir_' and a blank project '_uv init_' inside. The '_uv_' command makes this a python project repo. The directory (output of the '_tree_' command) has the following three mostly blank files added:

```sh
.
├── README.md
├── main.py
└── pyproject.toml
```

The main.py is a simple hello world project The pyproject.toml describes a basic python project structure:

```sh
[project]
name = "event-based-svcs"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.13"
dependencies = []

[dependency-groups]
dev = [
    "mkdocs>=1.6.1",
    "mkdocstrings>=0.29.0",
    "pytest>=8.3.5",
    "pytest-cov>=6.0.0",
    "ruff>=0.11.2",
]
```

- Adds some '_uv add_' common dependencies to the project - the dependencies are python modules/libraries we will use. We only need these modules when developing the code, so we add them as development '_---dev_' requirements as they will never be used to run the projects.
- Creates a virtual environment and activates it
- Creates a mkdoc project in the docs sub-directory
- Verifies that the mkdocs project is able to be built

> > > tip -I like to edit the root mkdoc.yml file and setup features like blog plugins

# Make the bar scene ... the monorepo

We need to add sub-projects for each actor in this bar. Each will be some form of an application. Each is able to be built independently and run inter-dependently, and interacts with at least two other applications. The GUI interacts with the AuthService and AppService. The AppService interacts with the GUI and the AppService. You see that?

```sh
mkdir projects
uv init --app projects/gui-proj
uv init --app projects/cli-proj
uv init --app projects/auth-svc
uv init --app projects/app-svc
```

Each of these commands create a subdirectory under project and will be members of the overall main project. We'll get back to the members part in a bit.

### Add the actual packages which have interdependencies

The reality is each application/component of the product have other friends at this bar. These friends are the packages each depend on to actually do work. These friends might actually be dependent on each other. Say we have two packages, lib-one and lib-two. Lib-one might need lib-two to get its work done.

```sh
uv init --package --lib projects/lib-one
uv init --package --lib projects/lib-two
```

# Essential files ...

Let's see what we have so far. If we run the tree command we see the structure of our monorepo. A mix of applications and packages to build our product on.

```sh
tree
.
├── README.md
├── docs
│   └── index.md
├── main.py
├── mkdocs.yml
├── projects
│   ├── app-svc
│   │   ├── README.md
│   │   ├── main.py
│   │   └── pyproject.toml
│   ├── auth-svc
│   │   ├── README.md
│   │   ├── main.py
│   │   └── pyproject.toml
│   ├── cli-proj
│   │   ├── README.md
│   │   ├── main.py
│   │   └── pyproject.toml
│   ├── gui-proj
│   │   ├── README.md
│   │   ├── main.py
│   │   └── pyproject.toml
│   ├── lib-one
│   │   ├── README.md
│   │   ├── pyproject.toml
│   │   └── src
│   │       └── lib_one
│   │           ├── __init__.py
│   │           └── py.typed
│   └── lib-two
│       ├── README.md
│       ├── pyproject.toml
│       └── src
│           └── lib_two
│               ├── __init__.py
│               └── py.typed
├── pyproject.toml
├── site
     :  # editted for brevity
└── uv.lock
```

> > > Tip - I like to edit the root pyproject.toml and set workspace.members to ['projects/*'] so that all the packages in the projects directory are recognized as workspace members.

We look through the file for the following line, usually the last line of the file:

```toml
members = ["projects/gui-proj", "projects/cli-proj", "projects/auth-svc", "projects/app-svc", "projects/lib-one", "projects/lib-two"]
```

Our product will eventually have more components and packages, so we need to simplify this line to the following:

```toml
members = ["projects/*"]
```

My next post will start implementing this OAuth workflow and using the capabilities of the monorepo.

## Stay Connected

I’d love to hear your thoughts! Feel free to:

- Leave comments or ask questions.
- Contribute to the **[GitHub repository](https://github.com/rogerkohlerjr/event-driven-svcs/)** (link to your repo).
- Follow me on **[LinkedIn](https://www.linkedin.com/in/rekohler/)** for updates.

Thanks for stopping by, and happy coding!

