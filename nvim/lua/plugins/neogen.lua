-- ~/.config/nvim/lua/plugins/neogen.lua
return {
  "danymat/neogen",
  dependencies = { "nvim-treesitter/nvim-treesitter", "L3MON4D3/LuaSnip" }, -- make sure parsers + snippet engine are installed
  config = function()
    -- Setup Neogen
    require("neogen").setup({
      enabled = true,
      input_after_comment = true,
      snippet_engine = "luasnip",
      languages = {
        lua = { template = { annotation_convention = "emmylua" } },
        python = { template = { annotation_convention = "google_docstrings" } },
      },
    })

    -- Keymaps using vim.keymap.set (safer than :lua strings)
    local opts = { noremap = true, silent = true }
    vim.keymap.set("n", "<Leader>nf", function()
      require("neogen").generate()
    end, opts)

    vim.keymap.set("n", "<Leader>nc", function()
      require("neogen").generate({ type = "class" })
    end, opts)

    vim.keymap.set("i", "<C-l>", function()
      require("neogen").jump_next()
    end, opts)

    vim.keymap.set("i", "<C-h>", function()
      require("neogen").jump_prev()
    end, opts)
  end,
}
