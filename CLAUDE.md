# Global Claude Instructions

## JavaScript / TypeScript tooling

- Prefer **Bun** over Node.js and npm whenever it is reasonable: use `bun` for installs, scripts, tests, and running tools (`bun install`, `bun run`, `bunx`).
- Do not assume a project is npm-only—check for `bun.lock` / `package.json` scripts; if Bun is available and the project supports it, default to Bun.
- Fall back to npm/pnpm/yarn or plain `node` only when the repo explicitly requires it, a tool is incompatible with Bun, or the user asks otherwise.

## GitHub
- Never add Claude as a collaborator on GitHub repositories.
- Never add Claude as a co-author on any git commit or push (do not include "Co-Authored-By: Claude" lines in commit messages).
- Never push big changes in one commit, breakdown commits in multiple small relevant commits
# Global Claude Instructions

## GitHub
- Never add Claude as a collaborator on GitHub repositories.
- Never add Claude as a co-author on any git commit or push (do not include "Co-Authored-By: Claude" lines in commit messages).
- Never push big changes in one commit, breakdown commits in multiple small relevant commits
- The very first commit on any new repository must be an empty commit (no files staged) with the message "batman": `git commit --allow-empty -m "batman"`

## Project Context Maintenance
When working inside any project directory, actively maintain the following files to preserve context across sessions:

### CLAUDE.md (project-level)
Keep a `CLAUDE.md` in the project root updated with:
- Project name and purpose
- Tech stack (languages, frameworks, key libraries)
- Deployment info (where it's deployed, URLs, environments: dev/staging/prod)
- Architecture overview (key services, databases, APIs)
- Important conventions or constraints specific to this project
- Any non-obvious decisions or gotchas

### AGENT.md
Keep an `AGENT.md` in the project root updated with:
- Current active tasks or work-in-progress
- Recent decisions made and why
- Known issues or TODOs
- Any context that will be needed in the next session to continue seamlessly

### Directory Context
- When working in a subdirectory with significant logic, add or update a brief `CONTEXT.md` there explaining what that directory does, its responsibilities, and how it fits in the overall project.

### File placement
- Always place `CLAUDE.md`, `AGENT.md`, and any other Claude context files inside a **`.claude/`** folder at the project root (e.g. `.claude/CLAUDE.md`, `.claude/AGENT.md`).
- Always add `.claude/` to the project's `.gitignore` so these files are never committed to the repository.
- If a `.gitignore` does not exist, create one and add `.claude/` to it.

### Rules
- Update these files incrementally as work progresses — don't batch it to the end.
- When the user provides project details (deployment URL, environment, stack, etc.), immediately record them in `.claude/CLAUDE.md`.
- Before starting work in a project, read existing `.claude/CLAUDE.md` and `.claude/AGENT.md` if present to restore context.
- If these files don't exist yet in a project, create them (inside `.claude/`) as soon as enough context is known.

## End-of-Conversation Context Sync (REQUIRED)

At the natural end of every conversation where work was done in a project directory, you MUST:

1. **Ask the user** before closing:
   > "Want me to update the project context files (`CLAUDE.md`, `AGENT.md`) with what we covered today?"

2. **If yes (or if user says "do it" / "yes" / "update")**, perform all of the following:
   - Update the **project-level `CLAUDE.md`** with any new tech, deployment info, architecture decisions, or conventions discovered this session.
   - Update **`AGENT.md`** with: what was worked on, key decisions made, current state, what's left to do, and any gotchas for next session.
   - Update any **subdirectory `CONTEXT.md`** files for directories that were significantly touched.
   - Update the **memory system** (`~/.claude/projects/`) with project-level facts worth remembering long-term.

3. **Format for `AGENT.md` update** — always include these sections:
   ```
   ## Last Session — <date>
   ### What was done
   ### Decisions made (and why)
   ### Current state
   ### Next steps / TODOs
   ### Gotchas / watch out for
   ```

4. **Do not skip this step** even if the conversation was short. A one-liner summary is better than nothing.
5. If the user says "no" or "skip", respect it and don't update.