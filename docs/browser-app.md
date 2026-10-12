# Browser app

The browser app lets anyone check a data file without installing Python. It is
a single HTML file: open it, choose a CSV file, pick checks from a list (or
open a policy file), and download a report.

## Privacy

The data never leaves the computer. The app runs finassert with
[Pyodide](https://pyodide.org) (Python compiled to WebAssembly) inside the
browser tab:

- Python and the YAML reader are downloaded once, at start-up, from the pinned
  Pyodide release on the jsDelivr CDN. finassert itself is embedded in the file.
- After start-up the page makes no network requests.
- A Content-Security-Policy allows network connections only to that Pyodide
  release and allows no scripts except the embedded one, so the page cannot
  send data elsewhere even by accident.
- Reports are shown in a sandboxed frame with scripts disabled.

## What it does

1. **Choose your data**: a CSV (or JSON) file, read with the same loader as the
   command line. The first rows are previewed so the user can confirm the
   columns.
2. **Choose the checks**: each check shows a plain-language summary, a "don't
   use when" caution, and form fields for its settings. Column settings are
   picked from the file's headers. Settings typed into the form are kept as
   text and read as exact decimals. A shared policy file can be opened instead,
   and problems in it are listed with line numbers.
3. **Run the checks**: the full HTML report appears in the page and can be
   downloaded, along with the JSON artifact and the policy as YAML.

The downloaded policy is exactly the policy that ran. Running it with
`finassert check` gives identical results and the same policy fingerprint, so an
analyst can design checks in the browser and hand the file to an engineer for
an automated pipeline.

## Trying it

Every CI run attaches the built app as the `finassert-web` artifact on the
workflow's summary page; download it and open `finassert.html`. Load
`examples/positions.csv` and open `examples/policy.yml` to see a passing and a
failing check.

## Building

```bash
python scripts/build_web.py            # writes dist/web/finassert.html
```

The output is about 90 KiB and needs no server: double-click it, email it, or
put it on any static host. To host Pyodide yourself, for example on a network
without CDN access, pass `--pyodide-url https://intranet.example/pyodide/v0.27.7/full/`
pointing at a copy of the Pyodide distribution that includes `pyyaml`.

`scripts/smoke_web.py` drives the built page in headless Chromium: it loads the
examples, runs the checks, verifies the exported policy reproduces the results,
and fails on any network request after start-up or any CSP violation. CI runs it
against the real Pyodide CDN.

The page's logic lives in `finassert.web`, a JSON-in, JSON-out module that is
unit-tested under CPython; `web/app.js` only renders forms and moves text
between the page and Python.

## Limitations

- Excel workbooks must be saved as CSV first.
- Only built-in checks are listed; custom rules need the Python API or CLI.
- The first load downloads roughly 10 MB of Python runtime, which browsers cache.
