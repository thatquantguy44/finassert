# Assistant tool server

`finassert-assistant` lets an AI assistant such as Claude run finassert checks
on files on your computer. You can ask in plain language, for example "check
that the weights in positions.xlsx add up to one and nothing is negative", and
the assistant uses finassert to do it and explains the result.

The server speaks the [Model Context Protocol](https://modelcontextprotocol.io)
over stdio. It uses the same policies, loaders, and reports as the command
line, so a check the assistant runs gives the same result as
`finassert check`.

## Setting it up

Install the extra, which adds the MCP SDK:

```bash
uv add "finassert[assistant]"    # or: pip install "finassert[assistant]"
```

Then register the server with your assistant. For Claude Desktop, add it to
`claude_desktop_config.json`, naming the folders it may read:

```json
{
  "mcpServers": {
    "finassert": {
      "command": "finassert-assistant",
      "args": ["--root", "/Users/you/Documents/positions"]
    }
  }
}
```

In Claude Code: `claude mcp add finassert -- finassert-assistant --root /path/to/data`.

## What the assistant can do

| Tool | Does |
|---|---|
| `rules` | Lists every check with its settings and when not to use it. |
| `templates` | Lists the starter policies with their assumptions. |
| `suggest` | Matches the starter policies to a file's column names, explaining each match, and returns the adapted policy for the user to confirm. |
| `check_policy` | Validates policy text and lists problems with line numbers. |
| `inspect` | Shows a file's columns, row count, and first rows; lists a workbook's sheets. |
| `run_checks` | Runs a policy (text, file, or template) on a file and returns every result. |

The server also gives the assistant reporting rules: an "error" outcome means a
check could not run and is never a pass, failing rows are named by the row
numbers the spreadsheet shows, the policy's assumptions are repeated, and
tolerances are never loosened, or checks dropped, without asking you.

## Safety

- The server reads only inside the `--root` folders (by default the folder it
  starts in). Paths are resolved before they are compared, so `..` and symbolic
  links cannot reach other folders.
- Every tool only reads, except `run_checks`, which writes an HTML report when
  given `html_report_path`. The path must end in `.html`, must be inside a root,
  and an existing file is replaced only when `overwrite` is set.
- Nothing is sent anywhere except back to the assistant you connected it to.
  What you share with that assistant is governed by its own terms.
