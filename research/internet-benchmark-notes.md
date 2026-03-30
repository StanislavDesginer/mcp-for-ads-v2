# Internet Benchmark Notes

- Google Ads Developers publicly introduced an official Google Ads MCP Server in late 2025, validating MCP as a native interaction model for ad platforms.
- Public multi-network ad MCP projects show a common architecture: one MCP core, multiple provider adapters, strong safety layers, and a distinction between read analytics and write execution.
- TikTok-specific MCP examples reinforce the idea that campaign management and analytics should share one provider abstraction, even if write paths are more restricted at first.
