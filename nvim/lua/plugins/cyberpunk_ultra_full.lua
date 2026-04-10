return {
  "oxfist/night-owl.nvim",
  url = "git@github.com:oxfist/night-owl.nvim.git",
  lazy = false,
  priority = 1000,
  config = function()
    vim.cmd.colorscheme("night-owl")

    local hl = vim.api.nvim_set_hl

    -- Super intense neon colors
    hl(0, "Comment", { fg = "#ff00ff", italic = true, bold = true }) -- neon purple
    hl(0, "Function", { fg = "#00ffff", bold = true }) -- neon cyan
    hl(0, "Keyword", { fg = "#ff6aff", bold = true }) -- neon pink
    hl(0, "String", { fg = "#00ff00", bold = true }) -- neon green
    hl(0, "Number", { fg = "#ffff00", bold = true }) -- bright yellow
    hl(0, "Identifier", { fg = "#ff9500", bold = true }) -- neon orange
    hl(0, "Operator", { fg = "#00ffff", bold = true }) -- neon cyan

    -- Brighten all punctuation / delimiters / quotes
    hl(0, "Delimiter", { fg = "#ffffff", bold = true }) -- (), [] {}
    hl(0, "SpecialChar", { fg = "#ffffff", bold = true }) -- backslashes, quotes
    hl(0, "MatchParen", { fg = "#ffffff", bold = true }) -- matching parentheses
    hl(0, "@punctuation.bracket", { fg = "#ffffff", bold = true }) -- Tree-sitter brackets
    hl(0, "@punctuation.delimiter", { fg = "#ffffff", bold = true }) -- Tree-sitter commas/quotes
    hl(0, "@punctuation.special", { fg = "#ffffff", bold = true }) -- other special punctuation

    -- Glow effect using background layering
    hl(0, "CursorLine", { bg = "#222222" }) -- dark glow base
    hl(0, "Visual", { bg = "#0078d7", fg = "#ffffff", bold = true }) -- Windows 7 style selection
    hl(0, "LineNr", { fg = "#8800ff" }) -- neon purple line numbers
    hl(0, "CursorLineNr", { fg = "#00ffff", bold = true })

    hl(0, "StatusLine", { bg = "#0a0a0a", fg = "#00ffff", bold = true })
    hl(0, "StatusLineNC", { bg = "#0a0a0a", fg = "#555555" })

    -- Floating windows glow
    hl(0, "NormalFloat", { bg = "#111111" })
    hl(0, "FloatBorder", { fg = "#00ffff" })

    -- LSP diagnostics neon
    hl(0, "DiagnosticError", { fg = "#ff0000", bold = true })
    hl(0, "DiagnosticWarn", { fg = "#ff9500", bold = true })
    hl(0, "DiagnosticInfo", { fg = "#00ffff", bold = true })
    hl(0, "DiagnosticHint", { fg = "#ff00ff", bold = true })

    -- Search highlights
    hl(0, "Search", { bg = "#00ffff", fg = "#000000", bold = true })
    hl(0, "IncSearch", { bg = "#ff00ff", fg = "#000000", bold = true })

    -- Telescope adjustments
    hl(0, "TelescopeBorder", { fg = "#00ffff" })
    hl(0, "TelescopeNormal", { bg = "#111111" })
    hl(0, "TelescopeSelection", { bg = "#222222", fg = "#ff6aff", bold = true })
    hl(0, "TelescopePromptPrefix", { fg = "#00ffff" })
    hl(0, "TelescopePromptNormal", { bg = "#111111", fg = "#00ffff" })

    -- Extra glow for LSP floating windows
    hl(0, "LspFloatWinBorder", { fg = "#00ffff" })

    -- Make string contents neon but keep quotes white
    hl(0, "@string", { fg = "#00ff00", bold = true })
  end,
}
