# Xyntra 1.0.0

## What's Included

- Contract validation workflow for specs and coding contracts.
- Interactive slash command: `/coding projects validation <path> [--major-version N]`.
- Direct CLI entrypoint: `xyntra validate-contract <path> --major-version N`.
- Three-stage refinement chain: ChatGPT -> Kimi -> Claude.
- Versioned outputs: refined contract markdown, `WHATS_INCLUDED` notes, and audit JSON.
- Up-front surfacing in the CLI welcome flow, README, and public-site starter commands.

## Notes

- The Kimi stage is configured specifically for this workflow with `KIMI_API_KEY` and `KIMI_MODEL`; it is not wired into the core provider registry.
