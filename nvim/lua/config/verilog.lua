-- lua/plugins/verilog.lua
return {
  -- Optional: verilog.vim for indentation and basic syntax
  {
    "vhda/verilog.vim",
    ft = { "verilog", "systemverilog" },
  },
  -- Treesitter support
  {
    "nvim-treesitter/nvim-treesitter",
    opts = function(_, opts)
      opts.ensure_installed = opts.ensure_installed or {}
      -- only add if not already there
      local exists = false
      for _, lang in ipairs(opts.ensure_installed) do
        if lang == "verilog" then
          exists = true
        end
      end
      if not exists then
        table.insert(opts.ensure_installed, "verilog")
      end
    end,
  },
}
