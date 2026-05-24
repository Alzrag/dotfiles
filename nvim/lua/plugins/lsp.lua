return {
  {
    "neovim/nvim-lspconfig",
    opts = {
      servers = {
        verible = {
          cmd = { "verible-verilog-ls", "--rules_config_search" },
        },
        -- Add asm_lsp here to activate it natively
        asm_lsp = {},
      },
    },
  },
}
